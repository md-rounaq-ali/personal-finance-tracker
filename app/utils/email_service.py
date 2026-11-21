"""
Email & OTP Verification Service — Supports HTTPS Email APIs (Brevo / Resend) & SMTP
Bypasses cloud port restrictions (such as Render blocking ports 25, 465, and 587).
"""
import os
import smtplib
import secrets
import string
import json
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash
from flask import current_app
from app import db
from app.models import OTPVerification


def generate_otp(length=6):
    """Generate a cryptographically secure numeric OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def send_via_brevo_http(to_email, subject, html_content, text_content=None):
    """
    Send email via Brevo HTTP API (Port 443 / HTTPS).
    Never blocked by cloud hosts like Render. Free 300 emails/day.
    """
    api_key = os.environ.get('BREVO_API_KEY', '').strip().strip('"').strip("'")
    if not api_key:
        return False, "BREVO_API_KEY not configured"

    sender_email = (
        os.environ.get('BREVO_SENDER_EMAIL', '').strip()
        or os.environ.get('MAIL_USERNAME', 'fintrack.security@gmail.com').strip()
    )
    sender_name = "FinTrack Security"

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    if text_content:
        payload["textContent"] = text_content

    try:
        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status in (200, 201, 202):
                return True, None
            return False, f"Brevo HTTP error: {response.status}"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8') if e.fp else str(e)
        if "Key not found" in err_body or e.code == 401:
            return False, "Brevo API Key not found or unauthorized. In Brevo, open the 'API Keys' tab (not SMTP tab), generate a key (starts with 'xkeysib-'), and verify your Brevo email."
        return False, f"Brevo API error: {err_body}"
    except Exception as e:
        return False, f"Brevo connection error: {str(e)}"


def send_via_resend_http(to_email, subject, html_content, text_content=None):
    """
    Send email via Resend HTTP API (Port 443 / HTTPS).
    """
    api_key = os.environ.get('RESEND_API_KEY', '').strip()
    if not api_key:
        return False, "RESEND_API_KEY not configured"

    sender = os.environ.get('MAIL_DEFAULT_SENDER', 'onboarding@resend.dev').strip()

    payload = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }
    if text_content:
        payload["text"] = text_content

    try:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status in (200, 201, 202):
                return True, None
            return False, f"Resend HTTP error: {response.status}"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8') if e.fp else str(e)
        return False, f"Resend API error: {err_body}"
    except Exception as e:
        return False, f"Resend connection error: {str(e)}"


def send_smtp_email(to_email, subject, html_content, text_content=None):
    """
    Primary dispatcher:
    1. Checks if Brevo HTTP API is configured (HTTPS Port 443 - recommended for Render)
    2. Checks if Resend HTTP API is configured (HTTPS Port 443)
    3. Falls back to raw SMTP (Port 587 TLS -> Port 465 SSL)
    """
    # Fast path for automated testing
    if current_app and current_app.config.get('TESTING'):
        return True, None

    # Check for HTTPS Email APIs first (Render never blocks Port 443)
    if os.environ.get('BREVO_API_KEY'):
        return send_via_brevo_http(to_email, subject, html_content, text_content)

    if os.environ.get('RESEND_API_KEY'):
        return send_via_resend_http(to_email, subject, html_content, text_content)

    # Standard SMTP fallback
    mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com').strip()
    mail_username = os.environ.get('MAIL_USERNAME', '').strip().strip('"').strip("'")
    raw_password = os.environ.get('MAIL_PASSWORD', '').strip().strip('"').strip("'")
    mail_password = raw_password.replace(' ', '')
    mail_sender = os.environ.get('MAIL_DEFAULT_SENDER', '').strip().strip('"').strip("'") or f"FinTrack Security <{mail_username}>"

    if not mail_username or not mail_password:
        return False, "Email service not configured. Add BREVO_API_KEY or MAIL_USERNAME & MAIL_PASSWORD in Render."

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = mail_sender
    msg['To'] = to_email
    msg['Reply-To'] = mail_sender
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain='gmail.com')
    msg['Auto-Submitted'] = 'auto-generated'

    if text_content:
        msg.attach(MIMEText(text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))

    err587_str = "Not attempted"
    # Attempt Port 587
    try:
        with smtplib.SMTP(mail_server, 587, timeout=8) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(mail_username, mail_password)
            server.send_message(msg)
        return True, None
    except Exception as err587:
        err587_str = str(err587)

    # Attempt Port 465
    try:
        with smtplib.SMTP_SSL(mail_server, 465, timeout=8) as server:
            server.login(mail_username, mail_password)
            server.send_message(msg)
        return True, None
    except Exception as err465:
        if "Network is unreachable" in str(err465) or "Network is unreachable" in err587_str:
            return False, "Render free instances block outbound SMTP ports (587/465). Add free BREVO_API_KEY to send emails via HTTPS port 443."
        return False, f"SMTP Error (587: {err587_str} | 465: {err465})"


def create_and_send_otp(email, purpose='register'):
    """
    Creates an OTP in the database and dispatches it via email.
    """
    email = email.strip().lower()

    # Invalidate previous unused OTPs for this email and purpose
    existing_otps = OTPVerification.query.filter_by(
        email=email,
        purpose=purpose,
        is_used=False
    ).all()
    for o in existing_otps:
        o.is_used = True

    # Generate 6-digit OTP
    otp_code = generate_otp(6)
    otp_hash = generate_password_hash(otp_code)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    otp_record = OTPVerification(
        email=email,
        otp_hash=otp_hash,
        purpose=purpose,
        expires_at=expires_at,
        is_used=False,
        attempts=0
    )
    db.session.add(otp_record)
    db.session.commit()

    purpose_title = "Account Verification" if purpose == 'register' else "Password Reset Request"
    purpose_desc = (
        "Thank you for signing up with FinTrack! Please use the 6-digit code below to verify your email address and activate your account:"
        if purpose == 'register' else
        "We received a request to reset your FinTrack account password. Use the 6-digit code below to authorize your password change:"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0b1120; color: #f8fafc; padding: 20px; }}
            .container {{ max-width: 520px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 32px; border: 1px solid #334155; }}
            .logo {{ font-size: 32px; text-align: center; margin-bottom: 8px; }}
            .title {{ text-align: center; font-size: 22px; font-weight: 700; color: #38bdf8; margin-bottom: 20px; }}
            .desc {{ font-size: 15px; color: #cbd5e1; line-height: 1.6; margin-bottom: 24px; }}
            .otp-box {{ background: #0f172a; border: 2px dashed #0284c7; border-radius: 8px; text-align: center; padding: 18px; margin-bottom: 24px; }}
            .otp-code {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #38bdf8; font-family: monospace; }}
            .footer {{ font-size: 13px; color: #64748b; line-height: 1.5; border-top: 1px solid #334155; padding-top: 16px; margin-top: 24px; }}
            .warning {{ color: #f59e0b; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">💰 FinTrack</div>
            <div class="title">{purpose_title}</div>
            <p class="desc">{purpose_desc}</p>
            <div class="otp-box">
                <div class="otp-code">{otp_code}</div>
            </div>
            <p class="desc"><span class="warning">⏰ This code will expire in 10 minutes.</span> Never share your verification code with anyone.</p>
            <div class="footer">
                If you did not make this request, you can safely ignore this email. Your account remains protected.
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"FinTrack {purpose_title}\n\nYour 6-digit verification code is: {otp_code}\n\nThis code will expire in 10 minutes."

    sent, error = send_smtp_email(
        to_email=email,
        subject=f"FinTrack Verification Code: {otp_code}",
        html_content=html_content,
        text_content=text_content
    )

    is_testing = current_app.config.get('TESTING', False)
    is_local_dev = (os.environ.get('FLASK_DEBUG') == '1') and (not os.environ.get('RENDER'))

    if not sent:
        if is_testing or is_local_dev:
            print(f"\n[FinTrack DEV LOCAL] OTP for {email}: {otp_code} (Reason: {error})")
            return True, otp_code
        return False, error

    return True, None


def verify_otp_code(email, code, purpose='register'):
    """
    Verifies an entered OTP code for an email and purpose.
    """
    email = email.strip().lower()
    code = code.strip()

    otp_record = OTPVerification.query.filter_by(
        email=email,
        purpose=purpose,
        is_used=False
    ).order_by(OTPVerification.created_at.desc()).first()

    if not otp_record:
        return False, "No active verification code found. Please request a new one."

    if otp_record.attempts >= 5:
        otp_record.is_used = True
        db.session.commit()
        return False, "Too many incorrect attempts. This code has been invalidated. Please request a new code."

    if otp_record.is_expired():
        otp_record.is_used = True
        db.session.commit()
        return False, "Verification code has expired. Please request a new code."

    if not otp_record.check_otp(code):
        otp_record.attempts += 1
        db.session.commit()
        remaining = 5 - otp_record.attempts
        return False, f"Invalid verification code. {remaining} attempt(s) remaining."

    otp_record.is_used = True
    db.session.commit()
    return True, None


def send_welcome_email(to_email, username):
    """
    Sends a professional Welcome Email upon successful account creation.
    Fails safely without breaking user registration if email service is unavailable.
    """
    to_email = to_email.strip().lower()
    username = username.strip() if username else "there"

    subject = "Welcome to FinTrack! 🚀 Your Account is Ready"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to FinTrack</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b1120; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e2e8f0;">
    <div style="max-width: 600px; margin: 40px auto; background-color: #0f172a; border-radius: 16px; overflow: hidden; border: 1px solid #1e293b; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);">
        <!-- Header Banner -->
        <div style="background: linear-gradient(135deg, #059669 0%, #0d9488 50%, #0284c7 100%); padding: 36px 30px; text-align: center;">
            <div style="font-size: 48px; margin-bottom: 8px;">💰</div>
            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 700; letter-spacing: -0.5px;">FinTrack</h1>
            <p style="margin: 8px 0 0; color: #e6fffa; font-size: 14px; font-weight: 500;">Smart Personal Finance & Budgeting</p>
        </div>

        <!-- Body Content -->
        <div style="padding: 36px 32px;">
            <h2 style="margin: 0 0 16px; color: #f8fafc; font-size: 20px; font-weight: 600;">Welcome aboard, {username}! 🎉</h2>
            <p style="margin: 0 0 20px; color: #94a3b8; font-size: 15px; line-height: 1.6;">
                Your FinTrack account has been successfully verified and activated. You're now equipped with the tools to take complete control of your financial growth.
            </p>

            <!-- Feature Highlights -->
            <div style="background-color: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 28px; border: 1px solid #334155;">
                <p style="margin: 0 0 12px; color: #f1f5f9; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">What you can do right now:</p>
                <div style="padding: 6px 0; font-size: 14px; color: #cbd5e1; line-height: 1.6;">
                    💸 <strong>Track Expenses & Income:</strong> Log transactions effortlessly with smart categories.<br>
                    🏦 <strong>Multi-Account Management:</strong> Keep Bank, Cash, and Savings synced.<br>
                    🎯 <strong>Set Monthly Budgets:</strong> Establish category limits to avoid overspending.<br>
                    📊 <strong>Visual Reports:</strong> View real-time analytics on your spending habits.
                </div>
            </div>

            <!-- Call to Action -->
            <div style="text-align: center; margin: 32px 0;">
                <a href="https://personal-finance-tracker-l1n2.onrender.com/dashboard" style="display: inline-block; background-color: #10b981; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 15px; padding: 14px 32px; border-radius: 10px; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);">
                    Open Your Dashboard →
                </a>
            </div>

            <p style="margin: 28px 0 0; color: #64748b; font-size: 13px; line-height: 1.5;">
                🔒 <em>Security reminder: Never share your account credentials with anyone. FinTrack will never ask for your password via email.</em>
            </p>
        </div>

        <!-- Footer -->
        <div style="background-color: #0b1120; padding: 24px 30px; text-align: center; border-top: 1px solid #1e293b;">
            <p style="margin: 0 0 8px; color: #cbd5e1; font-size: 13px; font-weight: 500;">
                © 2026 FinTrack. All rights reserved.
            </p>
            <p style="margin: 0 0 14px; color: #94a3b8; font-size: 12.5px;">
                Developed by <a href="https://md-rounaq-ali.netlify.app/" target="_blank" rel="noopener noreferrer" style="color: #38bdf8; text-decoration: underline; font-weight: 600;">Md Rounaq Ali</a>
            </p>
            <div style="margin: 14px 0 14px;">
                <a href="https://www.google.com/search?q=md+rounaq+ali" target="_blank" rel="noopener noreferrer" style="display: inline-block; background: rgba(56, 189, 248, 0.12); color: #38bdf8; text-decoration: none; font-size: 12px; font-weight: 600; padding: 8px 18px; border-radius: 999px; border: 1px solid rgba(56, 189, 248, 0.35);">
                    🔍 Search Creator on Google: <span style="text-decoration: underline;">md rounaq ali ↗</span>
                </a>
            </div>
            <p style="margin: 0; color: #64748b; font-size: 11px;">
                personal-finance-tracker-l1n2.onrender.com
            </p>
        </div>
    </div>
</body>
</html>"""

    text_content = f"""Welcome to FinTrack, {username}!

Your account has been successfully created and your email is verified.

Log in and visit your dashboard: https://personal-finance-tracker-l1n2.onrender.com/dashboard

What you can do with FinTrack:
- Track expenses and income
- Manage Bank and Cash accounts
- Set monthly budgets
- View visual financial analytics

Best regards,
FinTrack Team
"""

    try:
        sent, err = send_smtp_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        return sent, err
    except Exception as e:
        if current_app:
            current_app.logger.warning(f"Failed to dispatch welcome email to {to_email}: {e}")
        return False, str(e)

