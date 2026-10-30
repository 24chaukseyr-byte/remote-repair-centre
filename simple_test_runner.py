"""Simple white-box test runner (same style as the lab notebook).
Run:  python simple_test_runner.py
Each row: ID, function, input, expected output. Prints Actual and PASS/FAIL.
"""
from datetime import date
from validators import validate_password, validate_pickup_date, validate_phone

TODAY = date(2026, 10, 20)

test_cases = [
    # (ID, description, function, arguments, expected)
    ("WB01", "Password too short",        validate_password,    ("Ab@1",), False),
    ("WB02", "Password no uppercase",     validate_password,    ("abcd@1234",), False),
    ("WB03", "Password no lowercase",     validate_password,    ("ABCD@1234",), False),
    ("WB04", "Password no digit",         validate_password,    ("Abcd@efgh",), False),
    ("WB05", "Password no special char",  validate_password,    ("Abcd12345",), False),
    ("WB06", "Password valid",            validate_password,    ("Rahul@123",), True),
    ("WB07", "Date wrong format",         validate_pickup_date, ("31-12-2026", TODAY), False),
    ("WB08", "Date inside range",         validate_pickup_date, ("2026-10-25", TODAY), True),
    ("WB09", "Date in the past",          validate_pickup_date, ("2026-10-19", TODAY), False),
    ("WB10", "Date beyond 30 days",       validate_pickup_date, ("2026-11-20", TODAY), False),
    ("WB11", "Phone trailing newline",    validate_phone,       ("9876543210\n",), False),
]

passed = 0
print(f"{'ID':<6}{'Scenario':<28}{'Expected':<10}{'Actual':<10}Status")
print("-" * 62)
for tc_id, desc, func, args, expected in test_cases:
    actual = func(*args)
    status = "PASS" if actual == expected else "FAIL"
    passed += status == "PASS"
    print(f"{tc_id:<6}{desc:<28}{str(expected):<10}{str(actual):<10}{status}")
print("-" * 62)
print(f"Total: {len(test_cases)}   Passed: {passed}   Failed: {len(test_cases) - passed}")
