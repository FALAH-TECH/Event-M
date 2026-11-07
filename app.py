
from dotenv import load_dotenv

# Load environment variables before configuring Flask
load_dotenv()

import mysql.connector
import database

from flask import Flask, render_template, session, redirect, url_for

from extensions import db, migrate
from routes.auth_utils import ROLE_HOME


def create_app(config="config.DevConfig"):

    # 1. Create Flask application
    app = Flask(__name__)

    # 2. Load environment-specific settings
    app.config.from_object(config)

    # 3. Ensure a secret key is configured
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY is not set")

    # 4. Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # 5. Import application blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.manager import manager_bp
    from routes.participant import participant_bp

    # 6. Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(manager_bp, url_prefix="/manager")
    app.register_blueprint(
        participant_bp,
        url_prefix="/participant"
    )

    # 7. Landing page
    @app.route("/")
    def landing():
        role = session.get("role")

        if session.get("user_id") and role in ROLE_HOME:
            return redirect(url_for(ROLE_HOME[role]))

        return render_template("landing.html")

    # 8. MySQL configuration errors
    @app.errorhandler(database.DatabaseConfigurationError)
    def database_configuration_error(error):
        return (
            "MySQL configuration is missing. "
            "Please check the environment variables.",
            503
        )

    # 9. MySQL connection/query errors
    @app.errorhandler(mysql.connector.Error)
    def database_unavailable(error):
        app.logger.error("MySQL error: %s", type(error).__name__)
        return (
            "Database unavailable. Please try again later.",
            503
        )

    # 10. HTTP error handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    # 11. Return the configured application
    return app
