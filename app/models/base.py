"""Module de base pour l'accès aux données"""
from sqlalchemy import text
from flask import current_app


class BaseModel:
    """Classe de base pour les modèles d'accès aux données"""

    @staticmethod
    def execute_query(query, params=None):
        """
        Exécute une requête SQL paramétrée et retourne les résultats

        Args:
            query: Requête SQL avec placeholders (:param_name)
            params: Dictionnaire des paramètres

        Returns:
            Liste de dictionnaires (résultats)
        """
        from app import db_session
        try:
            result = db_session.execute(text(query), params or {})
            # Conversion en liste de dictionnaires
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            db_session.rollback()
            raise Exception(f"Erreur lors de l'exécution de la requête: {str(e)}")

    @staticmethod
    def execute_scalar(query, params=None):
        """
        Exécute une requête et retourne une seule valeur

        Args:
            query: Requête SQL avec placeholders
            params: Dictionnaire des paramètres

        Returns:
            Valeur scalaire
        """
        from app import db_session
        try:
            result = db_session.execute(text(query), params or {})
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            db_session.rollback()
            raise Exception(f"Erreur lors de l'exécution de la requête: {str(e)}")

    @staticmethod
    def commit():
        """Valide la transaction en cours"""
        from app import db_session
        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise Exception(f"Erreur lors de la validation: {str(e)}")

    @staticmethod
    def rollback():
        """Annule la transaction en cours"""
        from app import db_session
        db_session.rollback()
