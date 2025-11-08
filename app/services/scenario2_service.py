"""Service d'analyse pour le scénario 2"""
from app.models.scenario2 import Scenario2Model
from app.models.analysis_log import AnalysisLogModel
import re


class Scenario2Service:
    """Service pour l'analyse consolidée des montants exécutés"""

    @staticmethod
    def analyze_scenario2(filters, pagination=None):
        """
        Analyse du scénario 2: Montants consolidés par dossier et structure

        Args:
            filters: Dict contenant les filtres de recherche
            pagination: Dict avec page et per_page

        Returns:
            Dict avec résultats, métadonnées et requête SQL
        """
        # Extraction et validation des filtres
        date_debut = filters.get('date_debut')
        date_fin = filters.get('date_fin')
        montant_min = filters.get('montant_min')
        montant_max = filters.get('montant_max')
        include_acte = filters.get('include_acte', True)
        include_rub = filters.get('include_rub', True)
        num_bnf = Scenario2Service._sanitize_like_input(filters.get('num_bnf'))
        nom_prenom = Scenario2Service._sanitize_like_input(filters.get('nom_prenom'))
        num_pec = Scenario2Service._sanitize_like_input(filters.get('num_pec'))

        # Structures sélectionnées
        id_structures_raw = filters.get('id_structures', [])
        id_structures = [int(s) for s in id_structures_raw if s] if id_structures_raw else None

        # Options d'affichage et tri
        sort_by = filters.get('sort_by', 'num_pec')
        sort_order = filters.get('sort_order', 'ASC')

        # Pagination
        page = pagination.get('page', 1) if pagination else 1
        per_page = pagination.get('per_page', 50) if pagination else 50
        offset = (page - 1) * per_page

        # Récupération des données consolidées
        results = Scenario2Model.get_consolidated_data(
            date_debut=date_debut,
            date_fin=date_fin,
            montant_min=montant_min,
            montant_max=montant_max,
            include_acte=include_acte,
            include_rub=include_rub,
            include_pharmacie=True,  # Toujours inclure la pharmacie
            num_bnf=num_bnf,
            nom_prenom=nom_prenom,
            id_structures=id_structures,
            num_pec=num_pec,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=per_page,
            offset=offset
        )

        # Compte total pour pagination
        total_count = Scenario2Model.count_consolidated_data(
            date_debut=date_debut,
            date_fin=date_fin,
            montant_min=montant_min,
            montant_max=montant_max,
            include_acte=include_acte,
            include_rub=include_rub,
            include_pharmacie=True,  # Toujours inclure la pharmacie
            num_bnf=num_bnf,
            nom_prenom=nom_prenom,
            id_structures=id_structures,
            num_pec=num_pec
        )

        # Calcul des métriques globales
        metrics = Scenario2Service._calculate_metrics(results)

        # Construction de la requête SQL (pour affichage si demandé)
        sql_query = Scenario2Service._build_display_sql(filters) if filters.get('show_sql') else None

        return {
            'results': results,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page if total_count > 0 else 0,
            'metrics': metrics,
            'sql_query': sql_query
        }

    @staticmethod
    def _calculate_metrics(results):
        """Calcule les métriques globales à partir des résultats"""
        if not results:
            return {
                'total_lignes': 0,
                'total_dossiers': 0,
                'total_beneficiaires': 0,
                'montant_total': 0,
                'montant_moyen_dossier': 0
            }

        total_lignes = sum((r.get('nb_lignes') or 0) for r in results)
        montant_total = sum((r.get('montant_execute_total') or 0) for r in results)

        # Dossiers uniques
        dossiers_uniques = set(r.get('num_pec') for r in results if r.get('num_pec'))
        total_dossiers = len(dossiers_uniques)

        # Bénéficiaires uniques
        beneficiaires_uniques = set(r.get('num_bnf') for r in results if r.get('num_bnf'))
        total_beneficiaires = len(beneficiaires_uniques)

        montant_moyen_dossier = montant_total / total_dossiers if total_dossiers > 0 else 0

        return {
            'total_lignes': total_lignes,
            'total_dossiers': total_dossiers,
            'total_beneficiaires': total_beneficiaires,
            'montant_total': montant_total,
            'montant_moyen_dossier': montant_moyen_dossier
        }

    @staticmethod
    def _sanitize_like_input(value):
        """
        Nettoie les entrées pour les requêtes LIKE
        Échappe les caractères spéciaux SQL
        """
        if not value:
            return None

        # Supprimer les % et _ existants (wildcards)
        # et échapper les caractères spéciaux
        value = str(value).strip()
        if not value:
            return None

        # Échapper les caractères spéciaux
        value = value.replace('\\', '\\\\')
        value = value.replace('%', '\\%')
        value = value.replace('_', '\\_')

        return value

    @staticmethod
    def _build_display_sql(filters):
        """Construit une version simplifiée de la requête SQL pour affichage"""
        date_debut = filters.get('date_debut', 'YYYY-MM-DD')
        date_fin = filters.get('date_fin', 'YYYY-MM-DD')
        montant_min = filters.get('montant_min', 0)
        montant_max = filters.get('montant_max')
        montant_max_display = montant_max if montant_max is not None else 'MAX'

        include_acte = filters.get('include_acte', True)
        include_rub = filters.get('include_rub', True)

        sources = []
        if include_acte:
            sources.append("ACTE")
        if include_rub:
            sources.append("RUB")
        sources_str = ", ".join(sources) if sources else "AUCUNE SOURCE"

        query = f"""
-- 🎯 Scénario 2: Analyse consolidée par dossier et structure exécutante
-- Sources: {sources_str}
-- Période: {date_debut} → {date_fin}
-- Montants: {montant_min} → {montant_max_display}

WITH lignes AS (
"""

        if include_rub:
            query += """
  /* (A) Rubriques d'hospitalisation */
  SELECT
      at.id_structure_executante    AS id_structure,
      s.nom_structure               AS nom_structure,
      at.num_pec                    AS num_pec,
      la.date_execution_acte        AS date_execution_acte,
      la.montant                    AS montant,
      at.num_trans                  AS num_trans,
      'RUB'                         AS source_ligne
  FROM acte_trans at
  JOIN list_rub_hosp_acte_trans la ON la.id_acte_trans = at.id_acte_trans
  JOIN structure s ON s.id_structure = at.id_structure_executante
  WHERE la.date_execution_acte BETWEEN '{date_debut}' AND '{date_fin}'
"""
            if montant_min is not None or montant_max is not None:
                max_val = montant_max if montant_max is not None else 999999999
                query += f"    AND la.montant BETWEEN {montant_min} AND {max_val}\n"

        if include_acte:
            if include_rub:
                query += "\n  UNION ALL\n\n"
            query += """
  /* (B) Actes */
  SELECT
      at.id_structure_executante    AS id_structure,
      s.nom_structure               AS nom_structure,
      at.num_pec                    AS num_pec,
      l.date_execution_acte         AS date_execution_acte,
      l.montant_acte                AS montant,
      at.num_trans                  AS num_trans,
      'ACTE'                        AS source_ligne
  FROM acte_trans at
  JOIN list_acte_acte_trans l ON l.id_acte_trans = at.id_acte_trans
  JOIN structure s ON s.id_structure = at.id_structure_executante
  WHERE l.date_execution_acte BETWEEN '{date_debut}' AND '{date_fin}'
"""
            if montant_min is not None or montant_max is not None:
                max_val = montant_max if montant_max is not None else 999999999
                query += f"    AND l.montant_acte BETWEEN {montant_min} AND {max_val}\n"

        query += """
),
agg AS (
  SELECT
    li.id_structure                 AS id_structure_executante,
    li.nom_structure                AS nom_structure_executante,
    li.num_pec                      AS num_pec,
    tr.num_bnf                      AS num_bnf,
    tr.nom_prenom                   AS nom_prenom,
    tr.telephone                    AS telephone,
    tr.sexe                         AS sexe,
    tr.date_naissance               AS date_naissance,
    tt.libelle_type_trans           AS libelle_type_trans,
    li.date_execution_acte          AS date_executante_soin,
    COUNT(*)                        AS nb_lignes,
    SUM(li.montant)                 AS montant_execute_total,
    GROUP_CONCAT(DISTINCT li.source_ligne) AS source_ligne
  FROM lignes li
  LEFT JOIN `transaction` tr ON tr.num_trans = li.num_trans
  LEFT JOIN type_transactions tt ON tt.id_type_trans = tr.id_type_trans
  GROUP BY li.id_structure, li.nom_structure, li.num_pec,
           tr.num_bnf, tr.nom_prenom, tr.telephone, tr.sexe, tr.date_naissance,
           tt.libelle_type_trans, li.date_execution_acte
)

SELECT
  a.*,
  SUM(a.montant_execute_total) OVER (PARTITION BY a.num_pec) AS montant_group_numpec
FROM agg a
ORDER BY a.num_pec ASC, a.nom_structure_executante ASC, a.date_executante_soin ASC;
"""

        return query

    @staticmethod
    def get_structures_for_select():
        """Récupère la liste des structures pour le dropdown du formulaire"""
        return Scenario2Model.get_structures_list()

    @staticmethod
    def save_analysis(nom_utilisateur, intitule, motif, parametres, metriques):
        """
        Sauvegarde une analyse dans l'historique

        Args:
            nom_utilisateur: Nom de l'utilisateur
            intitule: Titre de l'analyse
            motif: Motif de l'analyse
            parametres: Paramètres de recherche
            metriques: Métriques calculées

        Returns:
            ID du log créé
        """
        return AnalysisLogModel.create_log(
            nom_utilisateur=nom_utilisateur,
            intitule=intitule,
            motif=motif,
            scenario_id=2,  # Scénario 2
            parametres=parametres,
            metriques=metriques
        )

    @staticmethod
    def mask_phone_number(phone):
        """
        Masque un numéro de téléphone (XXXXX1234)

        Args:
            phone: Numéro de téléphone complet

        Returns:
            Numéro masqué
        """
        if not phone or len(str(phone)) < 4:
            return phone

        phone_str = str(phone)
        return 'X' * (len(phone_str) - 4) + phone_str[-4:]
