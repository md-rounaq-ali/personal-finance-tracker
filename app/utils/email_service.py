"""
Email & OTP Verification Service — Secure token generation & resilient SMTP delivery
"""
import os
import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash
from flask import current_app
from app import db
from app.models import OTPVerification


def generate_otp(length=6):
    """Generate a cryptographically secure numeric OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def send_smtp_email(to_email, subject, html_content, text_content=None):
    """
    Send an email via SMTP with automatic dual-port fallback (Port 587 TLS -> Port 465 SSL).
    Sanitizes spaces and quotes from credentials automatically.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    # Fast path for automated testing
    if current_app and current_app.config.get('TESTING'):
        return True, None

    mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com').strip()
    mail_username = os.environ.get('MAIL_USERNAME', '').strip().strip('"').strip("'")
    raw_password = os.environ.get('MAIL_PASSWORD', '').strip().strip('"').strip("'")
    # Google App Passwords often have spaces (e.g. 'rwqa qrow fhmm xodm') -> strip spaces for SMTP
    mail_password = raw_password.replace(' ', '')
    mail_sender = os.environ.get('MAIL_DEFAULT_SENDER', '').strip().strip('"').strip("'") or f"FinTrack Security <{mail_username}>"

    if not mail_username or not mail_password:
        return False, "SMTP credentials missing: Please set MAIL_USERNAME and MAIL_PASSWORD in Render Environment."

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = mail_sender
    msg['To'] = to_email

    if text_content:
        msg.attach(MIMEText(text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))

    err587_str = "Not attempted"
    # Attempt 1: Port 587 with STARTTLS
    try:
        with smtplib.SMTP(mail_server, 587, timeout=12) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(mail_username, mail_password)
            server.send_message(msg)
        return True, None
    except Exception as err587:
        err587_str = str(err587)
        if current_app:
            current_app.logger.warning(f"SMTP Port 587 attempt failed: {err587_str}. Retrying on Port 465 (SSL)...")

    # Attempt 2: Port 465 with direct SSL (often more reliable on cloud providers)
    try:
        with smtplib.SMTP_SSL(mail_server, 465, timeout=12) as server:
            server.login(mail_username, mail_password)
            server.send_message(msg)
        return True, None
    except Exception as err465:
        error_msg = f"Email delivery failed (Port 587: {err587_str} | Port 465: {err465})"
        if current_app:
            current_app.logger.error(error_msg)
        return False, error_msg


def create_and_send_otp(email, purpose='register'):
    """
    Creates an OTP in the database and dispatches it via email.
    purpose: 'register' or 'forgot_password'
    Returns: (bool_success, error_or_dev_otp)
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

    # Email content formatting
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

    # Dispatch email
    sent, error = send_smtp_email(
        to_email=email,
        subject=f"FinTrack Verification Code: {otp_code}",
        html_content=html_content,
        text_content=text_content
    )

    # In production (e.g. on Render), NEVER display the OTP on screen!
    is_testing = current_app.config.get('TESTING', False)
    is_local_dev = (os.environ.get('FLASK_DEBUG') == '1') and (not os.environ.get('RENDER'))

    if not sent:
        if is_testing or is_local_dev:
            print(f"\n[FinTrack DEV LOCAL] OTP for {email}: {otp_code} (Reason: {error})")
            return True, otp_code
        # In production: Fail securely and do NOT leak the OTP
        return False, error

    return True, None


def verify_otp_code(email, code, purpose='register'):
    """
    Verifies an entered OTP code for an email and purpose.
    Returns: (is_valid, error_message)
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

    # Check max attempts (prevent brute force)
    if otp_record.attempts >= 5:
        otp_record.is_used = True
        db.session.commit()
        return False, "Too many incorrect attempts. This code has been invalidated. Please request a new code."

    # Check expiration
    if otp_record.is_expired():
        otp_record.is_used = True
        db.session.commit()
        return False, "Verification code has expired. Please request a new code."

    # Verify code
    if not otp_record.check_otp(code):
        otp_record.attempts += 1
        db.session.commit()
        remaining = 5 - otp_record.attempts
        return False, f"Invalid verification code. {remaining} attempt(s) remaining."

    # Success: Mark used
    otp_record.is_used = True
    db.session.commit()
    return True, None
