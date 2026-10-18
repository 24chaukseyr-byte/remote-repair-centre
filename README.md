# Remote Mobile Repair Centre

PBL project. Two modules implemented:
1. **User Registration & Login**
2. **Repair Request Booking** (submit, view, cancel)

Stack: Python, Flask, SQLite, HTML/CSS.

## Run it

```
python -m venv venv
venv\Scripts\activate            (Windows)   |   source venv/bin/activate   (Mac/Linux)
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

The SQLite database file `repair_centre.db` is created automatically on first run.

## Run the automated tests

```
pytest -v
```
96 tests: unit tests for every validation rule (boundary value analysis, equivalence
partitioning) plus functional and integration tests through the Flask test client.
Test names contain the manual test case ID from the test plan (e.g. `test_TC06_...`).

## Files

| File | Purpose |
|---|---|
| `app.py` | Flask routes for both modules |
| `database.py` | SQLite schema and helpers |
| `validators.py` | All input validation rules |
| `templates/`, `static/` | HTML pages and CSS |
| `tests/test_validators.py` | Unit tests |
| `tests/test_app.py` | Functional and integration tests |

## Routes

| Route | Module | Purpose |
|---|---|---|
| `/register` | 1 | Create account |
| `/login`, `/logout` | 1 | Session handling |
| `/dashboard` | 1 | Landing page after login |
| `/request/new` | 2 | Submit repair request |
| `/requests` | 2 | List own requests |
| `/request/<id>/cancel` | 2 | Cancel a Submitted request |

## Design notes

- Forms use `novalidate` on purpose so the server-side validation (the part being tested) is
  what rejects bad input, and invalid data can be demonstrated in the browser.
- Passwords are stored hashed (Werkzeug).
- Email is stored lowercase, so duplicate checks are case-insensitive.
- Request IDs are generated as REQ-0001, REQ-0002, ...

## Known limitations (can be logged as Low priority issues or backlog items)

- No CSRF protection on forms.
- No limit on failed login attempts.
- No "forgot password" flow.
- No technician or admin side; status only changes from Submitted to Cancelled.
