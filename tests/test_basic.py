import pytest
from patch_isrm import app   # adjust if your package name differs

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_home_redirect(client):
    """Test that the home route returns 200 or redirects."""
    response = client.get("/")
    assert response.status_code in (200, 302)

def test_login_page(client):
    """Test that the login page loads."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data

def test_register_page(client):
    """Test that the register page loads."""
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Register" in response.data

def test_dashboard_requires_login(client):
    """Dashboard should redirect if not logged in."""
    response = client.get("/dashboard")
    assert response.status_code in (302, 401)

def test_admin_requires_login(client):
    """Admin route should redirect or deny if not logged in."""
    response = client.get("/admin")
    assert response.status_code in (302, 401)

def test_upload_requires_login(client):
    """Upload route should redirect or deny if not logged in."""
    response = client.get("/upload")
    assert response.status_code in (302, 401)

    # yes modified it hello
