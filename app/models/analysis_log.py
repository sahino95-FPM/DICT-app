"""Modèle pour l'historique des analyses"""
from datetime import datetime
from app.models.base import BaseModel
import json


class AnalysisLogModel(BaseModel):
    """Gestion des logs d'analyse"""

    @staticmethod
    def create_log(nom_utilisateur, intitule, motif, scenario_id, parametres, metriques):
        """
        Crée un log d'analyse

        Args:
            nom_utilisateur: Nom de l'utilisateur
            intitule: Titre de l'analyse
            motif: Motif de l'analyse
            scenario_id: ID du scénario
            parametres: Dict des paramètres de recherche
            metriques: Dict des métriques clés (nb résultats, etc.)

        Returns:
            ID du log créé
        """
        query = """
            INSERT INTO analysis_log
            (nom_utilisateur, intitule, motif, scenario_id, parametres, metriques, date_analyse)
            VALUES
            (:nom_utilisateur, :intitule, :motif, :scenario_id, :parametres, :metriques, :date_analyse)
        """

        params = {
            'nom_utilisateur': nom_utilisateur,
            'intitule': intitule,
            'motif': motif,
            'scenario_id': scenario_id,
            'parametres': json.dumps(parametres),
            'metriques': json.dumps(metriques),
            'date_analyse': datetime.now()
        }

        AnalysisLogModel.execute_query(query, params)
        AnalysisLogModel.commit()

        # Récupérer l'ID du dernier insert
        return AnalysisLogModel.execute_scalar("SELECT LAST_INSERT_ID()")

    @staticmethod
    def get_recent_logs(limit=10):
        """
        Récupère les analyses récentes

        Args:
            limit: Nombre de logs à récupérer

        Returns:
            Liste des logs récents
        """
        query = """
            SELECT
                id,
                nom_utilisateur,
                intitule,
                scenario_id,
                date_analyse,
                metriques
            FROM analysis_log
            ORDER BY date_analyse DESC
            LIMIT :limit
        """

        results = AnalysisLogModel.execute_query(query, {'limit': limit})

        # Décoder les JSON
        for result in results:
            if result.get('metriques'):
                result['metriques'] = json.loads(result['metriques'])

        return results

    @staticmethod
    def get_log_by_id(log_id):
        """
        Récupère un log spécifique

        Args:
            log_id: ID du log

        Returns:
            Log complet
        """
        query = """
            SELECT
                id,
                nom_utilisateur,
                intitule,
                motif,
                scenario_id,
                parametres,
                metriques,
                date_analyse
            FROM analysis_log
            WHERE id = :log_id
        """

        results = AnalysisLogModel.execute_query(query, {'log_id': log_id})

        if results:
            result = results[0]
            # Décoder les JSON
            result['parametres'] = json.loads(result['parametres'])
            result['metriques'] = json.loads(result['metriques'])
            return result

        return None
