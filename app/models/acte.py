"""Modèle pour les actes médicaux"""
from app.models.base import BaseModel


class ActeModel(BaseModel):
    """Gestion des données des actes médicaux"""

    @staticmethod
    def get_actes_by_filters(date_debut, date_fin, montant_min=None, montant_max=None,
                             structure_id=None, num_pec=None, limit=500, offset=0):
        """
        Récupère les actes selon les filtres fournis

        Args:
            date_debut: Date de début (YYYY-MM-DD)
            date_fin: Date de fin (YYYY-MM-DD)
            montant_min: Montant minimum
            montant_max: Montant maximum
            structure_id: ID de la structure
            num_pec: Numéro de PEC
            limit: Nombre max de résultats
            offset: Décalage pour pagination

        Returns:
            Liste d'actes
        """
        query = """
            SELECT
                a.id,
                a.date_execution,
                a.montant_execute,
                a.code_acte,
                a.libelle_acte,
                s.id as structure_id,
                s.nom_structure,
                p.num_pec,
                p.id as pec_id
            FROM acte_trans a
            LEFT JOIN structure_sante s ON a.structure_id = s.id
            LEFT JOIN pec p ON a.pec_id = p.id
            WHERE a.date_execution BETWEEN :date_debut AND :date_fin
        """

        params = {
            'date_debut': date_debut,
            'date_fin': date_fin,
            'limit': limit,
            'offset': offset
        }

        if montant_min is not None:
            query += " AND a.montant_execute >= :montant_min"
            params['montant_min'] = montant_min

        if montant_max is not None:
            query += " AND a.montant_execute <= :montant_max"
            params['montant_max'] = montant_max

        if structure_id:
            query += " AND s.id = :structure_id"
            params['structure_id'] = structure_id

        if num_pec:
            query += " AND p.num_pec = :num_pec"
            params['num_pec'] = num_pec

        query += " ORDER BY a.date_execution DESC, s.nom_structure"
        query += " LIMIT :limit OFFSET :offset"

        return ActeModel.execute_query(query, params)

    @staticmethod
    def get_aggregated_data(date_debut, date_fin, montant_min=None, montant_max=None,
                           group_by_structure=True, group_by_pec=True, group_by_date=True,
                           limit=500, offset=0):
        """
        Récupère les données agrégées des actes

        Args:
            date_debut: Date de début
            date_fin: Date de fin
            montant_min: Montant minimum
            montant_max: Montant maximum
            group_by_structure: Grouper par structure
            group_by_pec: Grouper par PEC
            group_by_date: Grouper par date
            limit: Limite de résultats
            offset: Décalage pour pagination

        Returns:
            Liste de résultats agrégés
        """
        # Construction dynamique du SELECT et GROUP BY
        select_fields = []
        group_by_fields = []

        if group_by_structure:
            select_fields.append("s.id as structure_id")
            select_fields.append("s.nom_structure")
            group_by_fields.append("s.id")
            group_by_fields.append("s.nom_structure")

        if group_by_pec:
            select_fields.append("p.num_pec")
            select_fields.append("p.id as pec_id")
            group_by_fields.append("p.num_pec")
            group_by_fields.append("p.id")

        if group_by_date:
            select_fields.append("a.date_execution")
            group_by_fields.append("a.date_execution")

        # Agrégations
        select_fields.append("COUNT(a.id) as nb_actes")
        select_fields.append("SUM(a.montant_execute) as montant_total")

        query = f"""
            SELECT {', '.join(select_fields)}
            FROM acte_trans a
            LEFT JOIN structure_sante s ON a.structure_id = s.id
            LEFT JOIN pec p ON a.pec_id = p.id
            WHERE a.date_execution BETWEEN :date_debut AND :date_fin
        """

        params = {
            'date_debut': date_debut,
            'date_fin': date_fin,
            'limit': limit,
            'offset': offset
        }

        if montant_min is not None:
            query += " AND a.montant_execute >= :montant_min"
            params['montant_min'] = montant_min

        if montant_max is not None:
            query += " AND a.montant_execute <= :montant_max"
            params['montant_max'] = montant_max

        if group_by_fields:
            query += f" GROUP BY {', '.join(group_by_fields)}"

        query += " ORDER BY montant_total DESC"
        query += " LIMIT :limit OFFSET :offset"

        return ActeModel.execute_query(query, params)

    @staticmethod
    def count_actes_by_filters(date_debut, date_fin, montant_min=None, montant_max=None,
                               group_by_structure=True, group_by_pec=True, group_by_date=True):
        """
        Compte le nombre total de résultats agrégés (pour pagination)

        Returns:
            Nombre total de groupes
        """
        group_by_fields = []

        if group_by_structure:
            group_by_fields.extend(["s.id", "s.nom_structure"])
        if group_by_pec:
            group_by_fields.extend(["p.num_pec", "p.id"])
        if group_by_date:
            group_by_fields.append("a.date_execution")

        query = f"""
            SELECT COUNT(*) as total
            FROM (
                SELECT 1
                FROM acte_trans a
                LEFT JOIN structure_sante s ON a.structure_id = s.id
                LEFT JOIN pec p ON a.pec_id = p.id
                WHERE a.date_execution BETWEEN :date_debut AND :date_fin
        """

        params = {
            'date_debut': date_debut,
            'date_fin': date_fin
        }

        if montant_min is not None:
            query += " AND a.montant_execute >= :montant_min"
            params['montant_min'] = montant_min

        if montant_max is not None:
            query += " AND a.montant_execute <= :montant_max"
            params['montant_max'] = montant_max

        if group_by_fields:
            query += f" GROUP BY {', '.join(group_by_fields)}"

        query += ") as subquery"

        return ActeModel.execute_scalar(query, params) or 0
