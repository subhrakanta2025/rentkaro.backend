import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    
    # CORS Configuration
    CORS_ORIGINS = '*'  # Allow all origins
    
    # ZeptoMail Configuration
    ZEPTOMAIL_API_URL = os.getenv('ZEPTOMAIL_API_URL', 'https://api.zeptomail.in/v1.1/email')
    ZEPTOMAIL_API_KEY = os.getenv('ZEPTOMAIL_API_KEY', '')
    ZEPTOMAIL_FROM_EMAIL = os.getenv('ZEPTOMAIL_FROM_EMAIL', 'noreply@rideindiarentals.com')
    
    # OTP Configuration
    OTP_EXPIRY_MINUTES = 10

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///ride_rentals.db')
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

def get_config():
    """Get the appropriate configuration"""
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    return DevelopmentConfig
