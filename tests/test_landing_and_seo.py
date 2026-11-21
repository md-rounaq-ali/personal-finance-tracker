"""
Tests for Public Landing Page, Robots.txt, and Sitemap.xml (SEO & PageRank)
"""

def test_landing_page_unauthenticated(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'FinTrack' in response.data
    assert b'Md Rounaq Ali' in response.data
    assert b'Master Your Money' in response.data
    assert b'All rights reserved' in response.data
    assert b'md-rounaq-ali.netlify.app' in response.data


def test_landing_page_authenticated_redirects(auth_client):
    response = auth_client.get('/')
    assert response.status_code == 302
    assert '/dashboard' in response.headers['Location']


def test_robots_txt(client):
    response = client.get('/robots.txt')
    assert response.status_code == 200
    assert response.content_type == 'text/plain; charset=utf-8' or 'text/plain' in response.content_type
    assert b'User-agent: *' in response.data
    assert b'sitemap.xml' in response.data


def test_sitemap_xml(client):
    response = client.get('/sitemap.xml')
    assert response.status_code == 200
    assert 'xml' in response.content_type
    assert b'<urlset' in response.data
    assert b'https://personal-finance-tracker-l1n2.onrender.com/' in response.data


def test_health_endpoints(client):
    for endpoint in ['/health', '/api/health', '/api/v1/health']:
        resp = client.get(endpoint)
        assert resp.status_code == 200
        assert b'online' in resp.data

