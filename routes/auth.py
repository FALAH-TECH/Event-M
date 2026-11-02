"""Authentication routes: login, register, logout."""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

import data
import mysql.connector
from werkzeug.security import check_password_hash
from routes.auth_utils import ROLE_HOME

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        home = ROLE_HOME.get(session.get("role"), "auth.login")
        return redirect(url_for(home))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = data.get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            # Brief redirect page shows loading state, then auto-navigates
            return render_template(
                "redirecting.html",
                role=user["role"],
                destination=url_for(ROLE_HOME[user["role"]]),
            )

        flash("Invalid email or password.", "error")
        return render_template("login.html", email=email)

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        home = ROLE_HOME.get(session.get("role"), "auth.login")
        return redirect(url_for(home))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        college = request.form.get("college", "").strip()
        roll_number = request.form.get("roll_number", "").strip()

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if not college:
            errors.append("College is required.")
        if not roll_number:
            errors.append("Roll number is required.")
        if data.get_user_by_email(email):
            errors.append("An account with this email already exists.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "register.html",
                name=name,
                email=email,
                college=college,
                roll_number=roll_number,
            )

        try:
            data.save_user({"name": name, "email": email, "password": password,
                            "role": "participant", "college": college,
                            "roll_number": roll_number})
        except (ValueError, mysql.connector.IntegrityError):
            flash("Unable to create account; check the details and email address.", "error")
            return render_template("register.html", name=name, email=email, college=college, roll_number=roll_number)
        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
