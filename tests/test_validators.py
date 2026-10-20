"""Unit tests for validators.py (Boundary Value Analysis + Equivalence Partitioning).

Test names carry the manual test case ID from the test plan (TCxx).
"""
from datetime import date, timedelta

import pytest

from validators import (validate_address, validate_brand, validate_confirm_password,
                        validate_description, validate_email, validate_imei,
                        validate_issue_type, validate_model, validate_name,
                        validate_password, validate_phone, validate_pickup_date,
                        validate_registration, validate_request)


# ---------------- Module 1 ----------------

def test_TC01_valid_registration_data():
    form = {"full_name": "Rahul Sharma", "email": "rahul@test.com", "phone": "9876543210",
            "password": "Rahul@123", "confirm_password": "Rahul@123"}
    assert validate_registration(form) == {}


@pytest.mark.parametrize("email", ["rahul@test", "rahul.test.com", "@test.com", "rahul@.com", "a b@test.com"])
def test_TC03_invalid_email_rejected(email):
    assert validate_email(email) is False


@pytest.mark.parametrize("email", ["rahul@test.com", "r.s+tag@mail.co.in"])
def test_valid_email_accepted(email):
    assert validate_email(email) is True


@pytest.mark.parametrize("phone,expected", [
    ("987654321", False),      # TC04: 9 digits, below minimum
    ("9876543210", True),      # TC05: 10 digits, boundary
    ("98765432101", False),    # TC06: 11 digits, above maximum
    ("5876543210", False),     # TC07: starts with 5
    ("6000000000", True),      # first digit lower boundary
    ("98765abcde", False),
    ("", False),
])
def test_TC04_to_TC07_phone_rules(phone, expected):
    assert validate_phone(phone) is expected


@pytest.mark.parametrize("password,expected", [
    ("Ab@1234", False),                # TC08: 7 chars, below minimum
    ("Abcd@123", True),                # TC09: 8 chars, boundary
    ("Abcdefg123", False),             # TC10: no special character
    ("abcd@1234", False),              # no uppercase
    ("ABCD@1234", False),              # no lowercase
    ("Abcdef@gh", False),              # no digit
    ("Abcdefghij@12345678", True),     # 19 chars
    ("Abcdefghij@123456789", True),    # 20 chars, upper boundary
    ("Abcdefghij@1234567890", False),  # 21 chars, above maximum
    ("", False),
])
def test_TC08_to_TC10_password_rules(password, expected):
    assert validate_password(password) is expected


def test_TC11_confirm_password_mismatch():
    assert validate_confirm_password("Rahul@123", "Rahul@124") is False
    assert validate_confirm_password("Rahul@123", "Rahul@123") is True


@pytest.mark.parametrize("name,expected", [
    ("Rahul Sharma", True),
    ("Rahul123", False),      # TC12: digits
    ("Ra", False),            # 2 chars, below minimum
    ("Raj", True),            # 3 chars, boundary
    ("A" * 50, True),         # 50 chars, boundary
    ("A" * 51, False),        # 51 chars, above maximum
    ("Rahul@", False),
    ("   ", False),
])
def test_TC12_name_rules(name, expected):
    assert validate_name(name) is expected


def test_TC13_empty_registration_form_flags_every_field():
    errors = validate_registration({})
    assert set(errors) == {"full_name", "email", "phone", "password", "confirm_password"}


# ---------------- Module 2 ----------------

@pytest.mark.parametrize("imei,expected", [
    ("12345678901234", False),     # TC20: 14 digits
    ("123456789012345", True),     # TC21: 15 digits
    ("1234567890123456", False),   # TC22: 16 digits
    ("12345678901234A", False),    # TC23: contains a letter
    ("", False),
])
def test_TC20_to_TC23_imei_rules(imei, expected):
    assert validate_imei(imei) is expected


@pytest.mark.parametrize("text,expected", [
    ("Cracked s", False),          # TC24: 9 chars
    ("Cracked sc", True),          # TC25: 10 chars
    ("x" * 300, True),             # 300 chars, upper boundary
    ("x" * 301, False),            # TC26: 301 chars
])
def test_TC24_to_TC26_description_rules(text, expected):
    assert validate_description(text) is expected


def test_TC27_to_TC29_pickup_date_rules():
    today = date(2026, 10, 20)
    assert validate_pickup_date("2026-10-19", today) is False                          # TC27 yesterday
    assert validate_pickup_date("2026-10-20", today) is True                           # TC28 today
    assert validate_pickup_date("2026-11-19", today) is True                           # today + 30
    assert validate_pickup_date((today + timedelta(days=31)).isoformat(), today) is False  # TC29
    assert validate_pickup_date("20-10-2026", today) is False                          # wrong format
    assert validate_pickup_date("", today) is False


def test_TC30_brand_must_be_selected():
    assert validate_brand("") is False
    assert validate_brand("NotABrand") is False
    assert validate_brand("Samsung") is True


def test_issue_type_must_be_listed():
    assert validate_issue_type("Screen") is True
    assert validate_issue_type("") is False
    assert validate_issue_type("Exploded") is False


def test_TC31_address_rules():
    assert validate_address("Nagpur") is False             # too short
    assert validate_address("A" * 9) is False
    assert validate_address("A" * 10) is True
    assert validate_address("A" * 200) is True
    assert validate_address("A" * 201) is False


@pytest.mark.parametrize("model,expected", [("S", False), ("S2", True), ("M" * 40, True), ("M" * 41, False)])
def test_model_rules(model, expected):
    assert validate_model(model) is expected


def test_TC19_valid_request_form_has_no_errors():
    today = date.today()
    form = {"brand": "Samsung", "model": "Galaxy S21", "imei": "123456789012345",
            "issue_type": "Screen", "description": "Cracked screen after fall",
            "pickup_date": (today + timedelta(days=1)).isoformat(),
            "pickup_address": "12 Civil Lines, Nagpur"}
    assert validate_request(form) == {}


def test_empty_request_form_flags_every_field():
    assert set(validate_request({})) == {"brand", "model", "imei", "issue_type",
                                         "description", "pickup_date", "pickup_address"}

@pytest.mark.parametrize("email", ["a..b@test.com", "a@test..com", ".a@test.com", "a.@test.com", "a@-test.com"])
def test_regression_malformed_email_rejected(email):
    assert validate_email(email) is False