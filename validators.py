"""Input validation for the Remote Mobile Repair Centre.

Every rule is a small function returning True/False so it can be unit tested
on its own. validate_registration() and validate_request() combine the rules
and return a dict of {field: error message} (empty dict means valid).
"""
import re
from datetime import date, datetime, timedelta

BRANDS = ["Samsung", "Apple", "Xiaomi", "OnePlus", "Realme", "Oppo", "Vivo", "Motorola", "Other"]
ISSUE_TYPES = ["Screen", "Battery", "Charging port", "Water damage", "Software", "Other"]

_EMAIL_RE = re.compile(r"[A-Za-z0-9]+([._%+-][A-Za-z0-9]+)*@([A-Za-z0-9]+(-[A-Za-z0-9]+)*\.)+[A-Za-z]{2,}")
_NAME_RE = re.compile(r"^[A-Za-z ]+$")
_PHONE_RE = re.compile(r"^[6-9][0-9]{9}$")
_IMEI_RE = re.compile(r"^[0-9]{15}$")


def _clean(value):
    return (value or "").strip()


# ---------- Module 1: registration / login rules ----------

def validate_name(name):
    """3 to 50 characters, letters and spaces only."""
    name = _clean(name)
    return 3 <= len(name) <= 50 and bool(_NAME_RE.match(name))


def validate_email(email):
    """Valid email format, at most 100 characters."""
    email = _clean(email)
    return len(email) <= 100 and bool(_EMAIL_RE.fullmatch(email))


def validate_phone(phone):
    """Exactly 10 digits, first digit 6, 7, 8 or 9."""
    return bool(_PHONE_RE.fullmatch(phone or ""))


def validate_password(password):
    """8 to 20 characters with uppercase, lowercase, digit and special character."""
    password = password or ""
    return bool(
        8 <= len(password) <= 20
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"[0-9]", password)
        and re.search(r"[^A-Za-z0-9]", password)
    )


def validate_confirm_password(password, confirm):
    return (password or "") == (confirm or "") and (password or "") != ""


# ---------- Module 2: repair request rules ----------

def validate_brand(brand):
    return _clean(brand) in BRANDS


def validate_model(model):
    """2 to 40 characters."""
    return 2 <= len(_clean(model)) <= 40


def validate_imei(imei):
    """Exactly 15 digits."""
    return bool(_IMEI_RE.fullmatch(imei or ""))


def validate_issue_type(issue_type):
    return _clean(issue_type) in ISSUE_TYPES


def validate_description(description):
    """10 to 300 characters."""
    return 10 <= len(_clean(description)) <= 300


def validate_address(address):
    """10 to 200 characters."""
    return 10 <= len(_clean(address)) <= 200


def validate_pickup_date(value, today=None):
    """Format YYYY-MM-DD, from today up to 30 days ahead (not in the past)."""
    today = today or date.today()
    try:
        picked = datetime.strptime(_clean(value), "%Y-%m-%d").date()
    except ValueError:
        return False
    return today <= picked <= today + timedelta(days=30)


# ---------- Combined form validators ----------

def validate_registration(form):
    errors = {}
    if not _clean(form.get("full_name")):
        errors["full_name"] = "Full name is required."
    elif not validate_name(form.get("full_name")):
        errors["full_name"] = "Name must be 3 to 50 characters, letters and spaces only."

    if not _clean(form.get("email")):
        errors["email"] = "Email is required."
    elif not validate_email(form.get("email")):
        errors["email"] = "Enter a valid email address."

    if not _clean(form.get("phone")):
        errors["phone"] = "Phone number is required."
    elif not validate_phone(form.get("phone")):
        errors["phone"] = "Phone must be exactly 10 digits and start with 6, 7, 8 or 9."

    if not form.get("password"):
        errors["password"] = "Password is required."
    elif not validate_password(form.get("password")):
        errors["password"] = (
            "Password must be 8 to 20 characters with an uppercase letter, "
            "a lowercase letter, a digit and a special character."
        )

    if not form.get("confirm_password"):
        errors["confirm_password"] = "Please confirm your password."
    elif not validate_confirm_password(form.get("password"), form.get("confirm_password")):
        errors["confirm_password"] = "Passwords do not match."
    return errors


def validate_request(form, today=None):
    errors = {}
    if not validate_brand(form.get("brand")):
        errors["brand"] = "Please select a brand."
    if not validate_model(form.get("model")):
        errors["model"] = "Model must be 2 to 40 characters."
    if not validate_imei(form.get("imei")):
        errors["imei"] = "IMEI must be exactly 15 digits."
    if not validate_issue_type(form.get("issue_type")):
        errors["issue_type"] = "Please select an issue type."
    if not validate_description(form.get("description")):
        errors["description"] = "Description must be 10 to 300 characters."
    if not validate_pickup_date(form.get("pickup_date"), today):
        errors["pickup_date"] = "Pickup date must be today or up to 30 days ahead (not in the past)."
    if not validate_address(form.get("pickup_address")):
        errors["pickup_address"] = "Pickup address must be 10 to 200 characters."
    return errors
