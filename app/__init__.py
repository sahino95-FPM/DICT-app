"""Initialisation de l'application Flask"""
import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.config import config


# Instances globales
csrf = CSRFProtect()
db_engine = None
db_session = None
mariadb_engine = None
mariadb_session = None


def create_app(config_name='default'):
    """Factory pour créer l'application Flask"""
    app = Flask(__name__)

    # Chargement de la configuration
    app.config.from_object(config[config_name])

    # Initialisation CSRF
    csrf.init_app(app)

    # Configuration des logs
    configure_logging(app)

    # Initialisation de la base de données
    init_database(app)

    # Enregistrement des blueprints (contrôleurs)
    register_blueprints(app)

    # Enregistrement des filtres Jinja
    register_template_filters(app)

    # Gestion des erreurs
    register_error_handlers(app)

    app.logger.info(f"Application {app.config['APP_NAME']} démarrée")

    return app


def configure_logging(app):
    """Configure le système de logging"""
    log_level = getattr(logging, app.config['LOG_LEVEL'])

    # Configuration du logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(app.config['LOG_FILE']),
            logging.StreamHandler()
        ]
    )


def init_database(app):
    """Initialise la connexion aux bases de données"""
    global db_engine, db_session, mariadb_engine, mariadb_session

    try:
        # Récupérer l'objet de configuration
        config_obj = config[app.config['FLASK_ENV']]()

        # ========================================
        # Base de données principale (Scénario 1)
        # ========================================
        database_uri = config_obj.DATABASE_URI

        db_engine = create_engine(
            database_uri,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=app.config['DEBUG']
        )

        # Création de la session factory
        session_factory = sessionmaker(bind=db_engine)
        db_session = scoped_session(session_factory)

        app.logger.info("Connexion à la base de données principale établie")

        # ========================================
        # Base de données MariaDB (Scénario 2)
        # ========================================
        try:
            mariadb_uri = config_obj.MARIADB_URI

            mariadb_engine = create_engine(
                mariadb_uri,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=app.config['DEBUG']
            )

            # Création de la session factory pour MariaDB
            mariadb_session_factory = sessionmaker(bind=mariadb_engine)
            mariadb_session = scoped_session(mariadb_session_factory)

            app.logger.info("Connexion à la base de données MariaDB (Scénario 2) établie")

        except Exception as e:
            app.logger.warning(f"Connexion MariaDB non disponible (Scénario 2 désactivé): {e}")
            mariadb_engine = None
            mariadb_session = None

        # Fermeture automatique des sessions après chaque requête
        @app.teardown_appcontext
        def shutdown_session(exception=None):
            if db_session:
                db_session.remove()
            if mariadb_session:
                mariadb_session.remove()

    except Exception as e:
        app.logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        raise


def register_blueprints(app):
    """Enregistre les blueprints (routes)"""
    from app.controllers.main_controller import main_bp
    from app.controllers.scenario1_controller import scenario1_bp
    from app.controllers.scenario2_controller import scenario2_bp
    from app.controllers.exports_controller import exports_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(scenario1_bp, url_prefix='/scenarios/1')
    app.register_blueprint(scenario2_bp, url_prefix='/scenarios/2')
    app.register_blueprint(exports_bp, url_prefix='/exports')


def register_template_filters(app):
    """Enregistre des filtres personnalisés pour Jinja2"""

    @app.template_filter('format_currency')
    def format_currency(value):
        """Formate un montant en devise"""
        if value is None:
            return '-'
        return f"{value:,.2f} FCFA".replace(',', ' ')

    @app.template_filter('format_date')
    def format_date(value, format='%d/%m/%Y'):
        """Formate une date"""
        if value is None:
            return '-'
        if isinstance(value, str):
            return value
        return value.strftime(format)

    @app.template_filter('format_number')
    def format_number(value):
        """Formate un nombre avec séparateurs de milliers"""
        if value is None:
            return '-'
        return f"{value:,}".replace(',', ' ')

    # Ajouter les fonctions Python natives aux globals de Jinja2
    app.jinja_env.globals.update({
        'max': max,
        'min': min
    })


def register_error_handlers(app):
    """Enregistre les gestionnaires d'erreurs"""

    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        app.logger.error(f"Erreur interne: {error}")
        if db_session:
            db_session.rollback()
        return render_template('errors/500.html'), 500
