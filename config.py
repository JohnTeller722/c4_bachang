import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret'
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'super-secret-salt'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///my_flask_app.db'
    SECURITY_PASSWORD_HASH = 'argon2'
    SECURITY_TWO_FACTOR_SECRET = os.environ.get('SECURITY_TWO_FACTOR_SECRET') or 'super-secret-2fa'
    SECURITY_TWO_FACTOR_ENABLED_METHODS = ['email', 'authenticator']
    SECURITY_TWO_FACTOR_MAIL_VALIDITY = 300  # 5 minutes
    SECURITY_TWO_FACTOR = True
    SECURITY_TOTP_SECRETS = {
        '1': os.environ.get('SECURITY_TOTP_SECRET') or 'super-secret-totp'
    }