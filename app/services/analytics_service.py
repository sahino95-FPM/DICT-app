"""Service d'analyse des données"""
from app.models.acte import ActeModel
from app.models.analysis_log import AnalysisLogModel


class AnalyticsService:
    """Service pour les analyses de données médicales"""

    @staticmethod
    def analyze_scenario1(filters, pagination=None):
        """
        Analyse du scénario 1: Montants exécutés - Vue détaillée par PEC

        MODÈLE CORRIGÉ: Affiche maintenant les données détaillées par PEC avec toutes les colonnes
        du fichier Excel (compatible avec admi_claude.py)

        Args:
            filters: Dict contenant les filtres de recherche
            pagination: Dict avec page et per_page

        Returns:
            Dict avec résultats, métadonnées et requête SQL
        """
        # Extraction des filtres
        date_debut = filters.get('date_debut')
        date_fin = filters.get('date_fin')
        montant_min = filters.get('montant_min')
        montant_max = filters.get('montant_max')

        # Pagination
        page = pagination.get('page', 1) if pagination else 1
        per_page = pagination.get('per_page', 50) if pagination else 50
        offset = (page - 1) * per_page

        # Récupération des données détaillées par PEC (NOUVEAU)
        results = ActeModel.get_detailed_pec_data(
            date_debut=date_debut,
            date_fin=date_fin,
            montant_min=montant_min,
            montant_max=montant_max,
            limit=per_page,
            offset=offset
        )

        # Compte total pour pagination
        total_count = ActeModel.count_detailed_pec(
            date_debut=date_debut,
            date_fin=date_fin,
            montant_min=montant_min,
            montant_max=montant_max
        )

        # Calcul des métriques globales
        metrics = AnalyticsService._calculate_metrics_detailed(results)

        # Construction de la requête SQL (pour affichage si demandé)
        sql_query = None  # Désactivé pour le moment

        return {
            'results': results,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'metrics': metrics,
            'sql_query': sql_query
        }

    @staticmethod
    def _calculate_metrics_detailed(results):
        """Calcule les métriques globales pour les données détaillées par PEC"""
        if not results:
            return {
                'total_pec': 0,
                'montant_total': 0,
                'montant_moyen': 0
            }

        total_pec = len(results)
        montant_total = sum(r.get('montant_total_pec', 0) or 0 for r in results)
        montant_moyen = montant_total / total_pec if total_pec > 0 else 0

        return {
            'total_pec': total_pec,
            'montant_total': montant_total,
            'montant_moyen': montant_moyen
        }

    @staticmethod
    def _calculate_metrics(results):
        """Calcule les métriques globales à partir des résultats (ancienne méthode)"""
        if not results:
            return {
                'total_actes': 0,
                'montant_total': 0,
                'montant_moyen': 0
            }

        total_actes = sum(r.get('nb_actes', 0) for r in results)
        montant_total = sum(r.get('montant_total', 0) for r in results)
        montant_moyen = montant_total / total_actes if total_actes > 0 else 0

        return {
            'total_actes': total_actes,
            'montant_total': montant_total,
            'montant_moyen': montant_moyen
        }

    @staticmethod
    def _build_sql_query(filters):
        """Construit la requête SQL pour affichage (éducatif)"""
        # Ceci est une version simplifiée pour affichage
        # La vraie requête est construite dans le modèle
        select_parts = []

        if filters.get('group_by_structure'):
            select_parts.extend(['s.id', 's.nom_structure'])
        if filters.get('group_by_pec'):
            select_parts.extend(['p.num_pec'])
        if filters.get('group_by_date'):
            select_parts.append('a.date_execution')

        select_parts.extend(['COUNT(a.id) as nb_actes', 'SUM(a.montant_execute) as montant_total'])

        query = f"""
SELECT {', '.join(select_parts)}
FROM acte_trans a
LEFT JOIN structure_sante s ON a.structure_id = s.id
LEFT JOIN pec p ON a.pec_id = p.id
WHERE a.date_execution BETWEEN '{filters.get('date_debut')}' AND '{filters.get('date_fin')}'
"""

        if filters.get('montant_min'):
            query += f"  AND a.montant_execute >= {filters.get('montant_min')}\n"
        if filters.get('montant_max'):
            query += f"  AND a.montant_execute <= {filters.get('montant_max')}\n"

        group_by = []
        if filters.get('group_by_structure'):
            group_by.extend(['s.id', 's.nom_structure'])
        if filters.get('group_by_pec'):
            group_by.append('p.num_pec')
        if filters.get('group_by_date'):
            group_by.append('a.date_execution')

        if group_by:
            query += f"GROUP BY {', '.join(group_by)}\n"

        query += "ORDER BY montant_total DESC"

        return query

    @staticmethod
    def save_analysis(nom_utilisateur, intitule, motif, scenario_id, parametres, metriques):
        """
        Sauvegarde une analyse dans l'historique

        Args:
            nom_utilisateur: Nom de l'utilisateur
            intitule: Titre de l'analyse
            motif: Motif de l'analyse
            scenario_id: ID du scénario
            parametres: Paramètres de recherche
            metriques: Métriques calculées

        Returns:
            ID du log créé
        """
        return AnalysisLogModel.create_log(
            nom_utilisateur=nom_utilisateur,
            intitule=intitule,
            motif=motif,
            scenario_id=scenario_id,
            parametres=parametres,
            metriques=metriques
        )

    @staticmethod
    def get_recent_analyses(limit=10):
        """Récupère les analyses récentes"""
        return AnalysisLogModel.get_recent_logs(limit=limit)

    @staticmethod
    def get_dashboard_stats():
        """Récupère les statistiques pour le dashboard"""
        from app.models.scenario2 import Scenario2Model

        # Récupérer les analyses récentes (avec gestion d'erreur)
        try:
            recent_analyses = AnalysisLogModel.get_recent_logs(limit=5)
        except Exception as e:
            recent_analyses = []

        # Compter les PEC du jour
        try:
            pec_today = Scenario2Model.count_pec_today()
        except Exception as e:
            pec_today = 0

        return {
            'recent_analyses': recent_analyses,
            'total_analyses': len(recent_analyses),
            'pec_today': pec_today
        }
