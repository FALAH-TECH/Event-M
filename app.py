
from dotenv import load_dotenv
from flask import Flask, render_template, session, redirect, url_for

from extensions import db, migrate
from routes.auth_utils import ROLE_HOME


# Load local environment variables
load_dotenv()


def create_app(config="config.DevConfig"):

    # Step 1: Create the Flask application
    app = Flask(__name__)

    # Step 2: Load configuration
    app.config.from_object(config)

    # Step 3: Verify the secret key exists
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY is not set")

    # Step 4: Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Step 5: Import blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.manager import manager_bp
    from routes.participant import participant_bp

    # Step 6: Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(manager_bp, url_prefix="/manager")
    app.register_blueprint(
        participant_bp,
        url_prefix="/participant"
    )

    # Step 7: Landing page
    @app.route("/")
    def landing():
        role = session.get("role")

        if session.get("user_id") and role in ROLE_HOME:
            return redirect(url_for(ROLE_HOME[role]))

        return render_template("landing.html")

    # Step 8: Handle missing pages
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    # Return the configured Flask application
    return app
