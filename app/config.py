"""Configuration de l'application Flask"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration de base"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Application
    APP_NAME = os.getenv('APP_NAME', 'FPMsigm | Inspections')
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', '50'))
    MAX_EXPORT_ROWS = int(os.getenv('MAX_EXPORT_ROWS', '5000'))

    # Base de données principale (Scénario 1 - SQLite)
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_NAME = os.getenv('DB_NAME', 'fpm_inspections.db')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Base de données MariaDB pour Scénario 2
    MARIADB_HOST = os.getenv('MARIADB_HOST', 'localhost')
    MARIADB_PORT = int(os.getenv('MARIADB_PORT', '3306'))
    MARIADB_NAME = os.getenv('MARIADB_NAME', 'admi')
    MARIADB_USER = os.getenv('MARIADB_USER', 'readonly_user')
    MARIADB_PASSWORD = os.getenv('MARIADB_PASSWORD', '')

    @property
    def DATABASE_URI(self):
        """Construit l'URI de connexion à la base de données principale"""
        if self.DB_TYPE == 'mysql':
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_TYPE == 'postgresql':
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_TYPE == 'sqlite':
            return f"sqlite:///{self.DB_NAME}"
        else:
            raise ValueError(f"Type de base de données non supporté: {self.DB_TYPE}")

    @property
    def MARIADB_URI(self):
        """Construit l'URI de connexion à MariaDB pour le Scénario 2"""
        return f"mariadb+mariadbconnector://{self.MARIADB_USER}:{self.MARIADB_PASSWORD}@{self.MARIADB_HOST}:{self.MARIADB_PORT}/{self.MARIADB_NAME}"

    # Logs
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')

    # Sécurité
    SESSION_COOKIE_SECURE = False  # True en production avec HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Pas d'expiration du token CSRF


class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True


class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


# Dictionnaire des configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
