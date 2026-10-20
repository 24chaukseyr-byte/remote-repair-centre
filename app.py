"""Remote Mobile Repair Centre.

Module 1: User Registration & Login
Module 2: Repair Request Booking
"""
import os
import sqlite3
from datetime import date, timedelta
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from database import connect, init_db, next_request_id
from validators import (BRANDS, ISSUE_TYPES, validate_registration,
                        validate_request)


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        DATABASE=os.path.join(app.root_path, "repair_centre.db"),
    )
    if test_config:
        app.config.update(test_config)

    init_db(app.config["DATABASE"])

    # ---------- helpers ----------
    def get_db():
        if "db" not in g:
            g.db = connect(app.config["DATABASE"])
        return g.db

    @app.teardown_appcontext
    def close_db(exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.before_request
    def load_user():
        g.user = None
        user_id = session.get("user_id")
        if user_id:
            g.user = get_db().execute(
                "SELECT id, full_name, email FROM users WHERE id = ?", (user_id,)
            ).fetchone()

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                flash("Please log in to continue.", "error")
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    # ---------- Module 1: registration, login, logout ----------
    @app.route("/")
    def index():
        return redirect(url_for("dashboard" if g.user else "login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "GET":
            return render_template("register.html", errors={}, form={})

        form = request.form
        errors = validate_registration(form)
        email = form.get("email", "").strip().lower()

        if "email" not in errors:
            exists = get_db().execute(
                "SELECT 1 FROM users WHERE email = ?", (email,)
            ).fetchone()
            if exists:
                errors["email"] = "This email is already registered."

        if errors:
            return render_template("register.html", errors=errors, form=form), 400

        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (full_name, email, phone, password_hash) VALUES (?, ?, ?, ?)",
                (form["full_name"].strip(), email, form["phone"],
                 generate_password_hash(form["password"])),
            )
            db.commit()
        except sqlite3.IntegrityError:
            errors["email"] = "This email is already registered."
            return render_template("register.html", errors=errors, form=form), 400

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "GET":
            return render_template("login.html", form={})

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return render_template("login.html", form=request.form), 401

        session.clear()
        session["user_id"] = user["id"]
        return redirect(url_for("dashboard"))

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        rows = get_db().execute(
            "SELECT status, COUNT(*) AS n FROM repair_requests WHERE user_id = ? GROUP BY status",
            (g.user["id"],),
        ).fetchall()
        counts = {r["status"]: r["n"] for r in rows}
        return render_template("dashboard.html", counts=counts)

    # ---------- Module 2: repair requests ----------
    def date_limits():
        today = date.today()
        return today.isoformat(), (today + timedelta(days=30)).isoformat()

    @app.route("/request/new", methods=["GET", "POST"])
    @login_required
    def new_request():
        min_date, max_date = date_limits()
        ctx = dict(brands=BRANDS, issue_types=ISSUE_TYPES,
                   min_date=min_date, max_date=max_date)

        if request.method == "GET":
            return render_template("new_request.html", errors={}, form={}, **ctx)

        form = request.form
        errors = validate_request(form)
        if errors:
            return render_template("new_request.html", errors=errors, form=form, **ctx), 400

        db = get_db()
        request_id = next_request_id(db)
        db.execute(
            """INSERT INTO repair_requests
               (request_id, user_id, brand, model, imei, issue_type,
                description, pickup_date, pickup_address, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Submitted')""",
            (request_id, g.user["id"], form["brand"].strip(), form["model"].strip(),
             form["imei"], form["issue_type"].strip(), form["description"].strip(),
             form["pickup_date"].strip(), form["pickup_address"].strip()),
        )
        db.commit()
        flash(f"Repair request {request_id} submitted.", "success")
        return redirect(url_for("my_requests"))

    @app.route("/requests")
    @login_required
    def my_requests():
        rows = get_db().execute(
            "SELECT * FROM repair_requests WHERE user_id = ? "
            "ORDER BY created_at DESC, request_id DESC",
            (g.user["id"],),
        ).fetchall()
        return render_template("my_requests.html", requests=rows)

    @app.route("/request/<request_id>/cancel", methods=["POST"])
    @login_required
    def cancel_request(request_id):
        db = get_db()
        row = db.execute(
            "SELECT status FROM repair_requests WHERE request_id = ? AND user_id = ?",
            (request_id, g.user["id"]),
        ).fetchone()
        if row is None:
            abort(404)
        if row["status"] != "Submitted":
            flash(f"Request {request_id} cannot be cancelled (status: {row['status']}).", "error")
            return redirect(url_for("my_requests"))

        db.execute(
            "UPDATE repair_requests SET status = 'Cancelled' WHERE request_id = ?",
            (request_id,),
        )
        db.commit()
        flash(f"Request {request_id} cancelled.", "success")
        return redirect(url_for("my_requests"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
