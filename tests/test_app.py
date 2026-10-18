"""Functional and integration tests using Flask's test client.

Test names carry the manual test case ID from the test plan (TCxx).
Each test runs against a fresh temporary SQLite database.
"""
import sqlite3
from datetime import date, timedelta

import pytest

from app import create_app

USER_A = {"full_name": "Rahul Sharma", "email": "rahul@test.com", "phone": "9876543210",
          "password": "Rahul@123", "confirm_password": "Rahul@123"}
USER_B = {"full_name": "Priya Verma", "email": "priya@test.com", "phone": "9123456780",
          "password": "Priya@123", "confirm_password": "Priya@123"}


def request_data(**overrides):
    data = {"brand": "Samsung", "model": "Galaxy S21", "imei": "123456789012345",
            "issue_type": "Screen", "description": "Cracked screen after fall",
            "pickup_date": (date.today() + timedelta(days=1)).isoformat(),
            "pickup_address": "12 Civil Lines, Nagpur"}
    data.update(overrides)
    return data


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def client(db_path):
    app = create_app({"TESTING": True, "DATABASE": db_path, "SECRET_KEY": "test"})
    return app.test_client()


def register(client, user=USER_A, **overrides):
    return client.post("/register", data={**user, **overrides}, follow_redirects=True)


def login(client, email="rahul@test.com", password="Rahul@123"):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


# ---------------- Module 1: registration ----------------

def test_TC01_valid_registration_creates_account(client, db_path):
    response = register(client)
    assert response.status_code == 200
    assert b"Registration successful" in response.data
    row = sqlite3.connect(db_path).execute("SELECT email FROM users").fetchone()
    assert row[0] == "rahul@test.com"


def test_TC02_duplicate_email_rejected(client):
    register(client)
    response = register(client)
    assert response.status_code == 400
    assert b"already registered" in response.data


def test_duplicate_email_is_case_insensitive(client):
    register(client)
    response = register(client, email="RAHUL@test.com")
    assert response.status_code == 400
    assert b"already registered" in response.data


def test_TC03_invalid_email_shows_error(client):
    response = register(client, email="rahul@test")
    assert response.status_code == 400
    assert b"valid email" in response.data


@pytest.mark.parametrize("phone,ok", [("987654321", False), ("9876543210", True),
                                      ("98765432101", False), ("5876543210", False)])
def test_TC04_to_TC07_phone_through_form(client, phone, ok):
    response = register(client, phone=phone)
    if ok:
        assert b"Registration successful" in response.data
    else:
        assert response.status_code == 400
        assert b"10 digits" in response.data


@pytest.mark.parametrize("password,ok", [("Ab@1234", False), ("Abcd@123", True), ("Abcdefg123", False)])
def test_TC08_to_TC10_password_through_form(client, password, ok):
    response = register(client, password=password, confirm_password=password)
    if ok:
        assert b"Registration successful" in response.data
    else:
        assert response.status_code == 400
        assert b"Password must be" in response.data


def test_TC11_confirm_password_mismatch(client):
    response = register(client, confirm_password="Rahul@124")
    assert response.status_code == 400
    assert b"do not match" in response.data


def test_TC12_name_with_digits_rejected(client):
    response = register(client, full_name="Rahul123")
    assert response.status_code == 400
    assert b"letters and spaces" in response.data


def test_TC13_empty_form_shows_required_errors(client):
    response = client.post("/register", data={})
    assert response.status_code == 400
    for text in (b"Full name is required", b"Email is required", b"Phone number is required",
                 b"Password is required", b"confirm your password"):
        assert text in response.data


# ---------------- Module 1: login / logout ----------------

def test_TC14_valid_login_opens_dashboard(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    assert b"Welcome, Rahul Sharma" in response.data


def test_TC15_wrong_password_rejected(client):
    register(client)
    response = login(client, password="Wrong@123")
    assert response.status_code == 401
    assert b"Invalid email or password" in response.data


def test_TC16_unregistered_email_rejected(client):
    response = login(client, email="none@test.com")
    assert response.status_code == 401
    assert b"Invalid email or password" in response.data


def test_TC17_logout_blocks_dashboard(client):
    register(client)
    login(client)
    client.post("/logout")
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_TC18_password_is_stored_hashed(client, db_path):
    register(client)
    stored = sqlite3.connect(db_path).execute("SELECT password_hash FROM users").fetchone()[0]
    assert stored != "Rahul@123"
    assert "Rahul@123" not in stored


# ---------------- Module 2: repair requests ----------------

def logged_in(client, user=USER_A):
    register(client, user)
    login(client, user["email"], user["password"])


def test_TC19_valid_request_saved_with_id_and_status(client):
    logged_in(client)
    response = client.post("/request/new", data=request_data(), follow_redirects=True)
    assert response.status_code == 200
    assert b"REQ-0001" in response.data
    assert b"Submitted" in response.data


def test_request_ids_increment(client):
    logged_in(client)
    client.post("/request/new", data=request_data())
    response = client.post("/request/new", data=request_data(), follow_redirects=True)
    assert b"REQ-0002" in response.data


@pytest.mark.parametrize("field,value,message", [
    ("imei", "12345678901234", b"15 digits"),                                   # TC20
    ("imei", "1234567890123456", b"15 digits"),                                 # TC22
    ("imei", "12345678901234A", b"15 digits"),                                  # TC23
    ("description", "Cracked s", b"10 to 300"),                                 # TC24
    ("description", "x" * 301, b"10 to 300"),                                   # TC26
    ("pickup_date", (date.today() - timedelta(days=1)).isoformat(), b"Pickup date"),   # TC27
    ("pickup_date", (date.today() + timedelta(days=31)).isoformat(), b"Pickup date"),  # TC29
    ("brand", "", b"select a brand"),                                           # TC30
    ("pickup_address", "Nagpur", b"10 to 200"),                                 # TC31
])
def test_TC20_to_TC31_invalid_request_rejected(client, field, value, message):
    logged_in(client)
    response = client.post("/request/new", data=request_data(**{field: value}))
    assert response.status_code == 400
    assert message in response.data


@pytest.mark.parametrize("field,value", [
    ("imei", "123456789012345"),                 # TC21
    ("description", "Cracked sc"),               # TC25
    ("pickup_date", date.today().isoformat()),   # TC28
])
def test_TC21_TC25_TC28_boundary_values_accepted(client, field, value):
    logged_in(client)
    response = client.post("/request/new", data=request_data(**{field: value}), follow_redirects=True)
    assert response.status_code == 200
    assert b"REQ-0001" in response.data


def test_TC32_user_sees_only_own_requests(client):
    logged_in(client, USER_A)
    client.post("/request/new", data=request_data(model="Galaxy A-Model"))
    client.post("/logout")

    logged_in(client, USER_B)
    client.post("/request/new", data=request_data(model="Pixel B-Model"))

    response = client.get("/requests")
    assert b"Pixel B-Model" in response.data
    assert b"Galaxy A-Model" not in response.data


def test_TC33_cancel_submitted_request(client):
    logged_in(client)
    client.post("/request/new", data=request_data())
    response = client.post("/request/REQ-0001/cancel", follow_redirects=True)
    assert b"cancelled" in response.data
    assert b"Cancelled" in response.data


def test_TC34_cancel_twice_is_rejected(client):
    logged_in(client)
    client.post("/request/new", data=request_data())
    client.post("/request/REQ-0001/cancel")
    response = client.post("/request/REQ-0001/cancel", follow_redirects=True)
    assert b"cannot be cancelled" in response.data


def test_cannot_cancel_another_users_request(client):
    logged_in(client, USER_A)
    client.post("/request/new", data=request_data())
    client.post("/logout")
    logged_in(client, USER_B)
    response = client.post("/request/REQ-0001/cancel")
    assert response.status_code == 404


# ---------------- Integration (Module 1 + Module 2) ----------------

@pytest.mark.parametrize("path", ["/request/new", "/requests", "/dashboard"])
def test_TC35_protected_pages_redirect_when_logged_out(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_TC35_cancel_requires_login(client):
    response = client.post("/request/REQ-0001/cancel")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_TC36_request_linked_to_logged_in_user(client, db_path):
    logged_in(client)
    client.post("/request/new", data=request_data())
    conn = sqlite3.connect(db_path)
    user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("rahul@test.com",)).fetchone()[0]
    owner = conn.execute("SELECT user_id FROM repair_requests WHERE request_id = 'REQ-0001'").fetchone()[0]
    assert owner == user_id
