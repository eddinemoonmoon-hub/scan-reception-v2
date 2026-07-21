import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pmd-reception-secret-2026')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+pg8000://', 1)
    elif DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+pg8000://', 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL if DATABASE_URL else 'sqlite:///' + os.path.join(BASE_DIR, 'reception.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_NAME = 'PMD Reception'
    ADMIN_PASSWORD = 'admin123'
    VERSION = '1.0.0'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 86400
    SESSION_COOKIE_NAME = 'pmd_session'
