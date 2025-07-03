import os
from datetime import timedelta

# Base directory
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'url_database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # URL Shortener settings
    SHORT_CODE_LENGTH = 6  # Length of auto-generated short codes
    DEFAULT_EXPIRATION_DAYS = 30  # Default expiration period for URLs
    MAX_CUSTOM_CODE_LENGTH = 32  # Maximum length for custom codes
    MIN_CUSTOM_CODE_LENGTH = 3  # Minimum length for custom codes
    
    # Rate limiting settings (if you implement this later)
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    
    # Security settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    REMEMBER_COOKIE_SECURE = True
    
    # Analytics settings
    TRACK_CLICKS = True
    TRACK_REFERRERS = False  # Set to True if you implement referrer tracking
    
    # Application settings
    APP_NAME = "Short.ly"
    APP_DESCRIPTION = "Professional URL Shortener Service"
    APP_VERSION = "1.0.0"
    APP_CONTACT_EMAIL = "support@short.ly"
    
    # Admin settings
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@short.ly')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'change-this-password')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries
    SESSION_COOKIE_SECURE = False  # Allow cookies over HTTP in development
    EXPLAIN_TEMPLATE_LOADING = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost.localdomain'

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    # Use a more secure secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24))
    # Database configuration for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Security settings for production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Disable tracking modifications to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the appropriate config class based on FLASK_ENV"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])