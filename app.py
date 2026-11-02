"""
Event Management System — Flask application entry point.
Run: python app.py
"""

import os
import mysql.connector
import database
from dotenv import load_dotenv
from flask import Flask, render_template, session, redirect, url_for

load_dotenv()

from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.manager import manager_bp
from routes.participant import participant_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY")

    @app.before_request
    def require_session_secret():
        if not app.secret_key:
            return "FLASK_SECRET_KEY must be configured in the environment or .env.", 503

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(manager_bp, url_prefix="/manager")
    app.register_blueprint(participant_bp, url_prefix="/participant")

    @app.route("/")
    def landing():
        if session.get("user_id"):
            role = session.get("role")
            if role == "admin":
                return redirect(url_for("admin.dashboard"))
            if role == "manager":
                return redirect(url_for("manager.dashboard"))
            if role == "participant":
                return redirect(url_for("participant.home"))
        return render_template("landing.html")

    @app.errorhandler(database.DatabaseConfigurationError)
    def database_configuration_error(e):
        return "MYSQL_PASSWORD must be configured in the environment or .env.", 503

    @app.errorhandler(mysql.connector.Error)
    def database_unavailable(e):
        return "Database unavailable. Please check the MySQL configuration and try again.", 503

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
