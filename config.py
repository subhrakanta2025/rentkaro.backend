import os
import urllib.parse
from datetime import timedelta


def build_db_uri_from_env(default=None):
    """Construct SQLAlchemy DB URI from discrete env vars if DATABASE_URL not set.

    Supports MySQL credentials provided as DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD.
    """
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url

    host = os.getenv('DB_HOST')
    name = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    port = os.getenv('DB_PORT', '3306')

    if host and name and user:
        # Percent-encode password to handle special chars
        encoded_pw = urllib.parse.quote_plus(password or '')
        return f"mysql+pymysql://{user}:{encoded_pw}@{host}:{port}/{name}"

    return default


def required_db_uri():
    uri = build_db_uri_from_env()
    if not uri:
        raise RuntimeError('Database configuration missing: set DATABASE_URL or DB_HOST/DB_NAME/DB_USER[/DB_PASSWORD/DB_PORT]')
    return uri

def _parse_origins():
    """Parse allowed origins from ALLOWED_ORIGINS or legacy CORS_ORIGINS."""
    raw = os.getenv('ALLOWED_ORIGINS') or os.getenv('CORS_ORIGINS')
    if not raw:
        raw = 'https://rentkaro-frontend-807261496773.us-central1.run.app, https://www.rentkaro.online, https://rentkaro.online,https://app.rentkaro.online'
    return [o.strip() for o in raw.split(',') if o.strip()]


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    
    # CORS Configuration
    CORS_ORIGINS = _parse_origins()
    
    # ZeptoMail Configuration
    ZEPTOMAIL_API_URL = os.getenv('ZEPTOMAIL_API_URL', 'https://api.zeptomail.in/v1.1/email')
    ZEPTOMAIL_API_KEY = os.getenv('ZEPTOMAIL_API_KEY', '')
    ZEPTOMAIL_FROM_EMAIL = os.getenv('ZEPTOMAIL_FROM_EMAIL', 'noreply@rideindiarentals.com')
    
    # OTP Configuration
    OTP_EXPIRY_MINUTES = 10
    # SQLAlchemy engine options to improve connection reliability with remote MySQL
    # Enable pool_pre_ping to detect and recycle stale connections.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': int(os.getenv('SQLALCHEMY_POOL_RECYCLE', '280')),
        'pool_size': int(os.getenv('SQLALCHEMY_POOL_SIZE', '10')),
        'pool_timeout': int(os.getenv('SQLALCHEMY_POOL_TIMEOUT', '30')),
        'connect_args': {
            'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '10'))
        }
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = required_db_uri()

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = required_db_uri()
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = required_db_uri()

def get_config():
    """Get the appropriate configuration"""
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    return DevelopmentConfig
