
import os
from datetime import timedelta


def _db_url():
    url = os.environ.get(
        "DATABASE_URL",
        "sqlite:///eventhub.db"
    )
    return url.replace("postgres://", "postgresql://", 1)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = _db_url()

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)


class DevConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-only-not-secret"
    )


class ProdConfig(Config):
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
