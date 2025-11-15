"""Modèle pour les actes médicaux"""
from app.models.base import BaseModel


class ActeModel(BaseModel):
    """Gestion des données des actes médicaux"""

    @staticmethod
    def get_detailed_pec_data(date_debut, date_fin, montant_min=None, montant_max=None, limit=500, offset=0):
        """
        Récupère les données détaillées des PEC (modèle 1 corrigé)
        Compatible avec le format du fichier Excel généré par admi_claude.py

        Args:
            date_debut: Date de début (YYYY-MM-DD)
            date_fin: Date de fin (YYYY-MM-DD)
            montant_min: Montant minimum
            montant_max: Montant maximum
            limit: Nombre max de résultats
            offset: Décalage pour pagination

        Returns:
            Liste des PEC avec montants exécutés détaillés
        """
        # Cette requête reproduit la logique de admi_claude.py avec une structure simplifiée
        query = """
            SELECT DISTINCT
                at.num_pec,
                (
                    SELECT COALESCE(SUM(COALESCE(laa.montant_acte, 0) * COALESCE(laa.quantite, 1)), 0)
                    FROM acte_trans at2
                    LEFT JOIN list_acte_acte_trans laa ON laa.id_acte_trans = at2.id_acte_trans
                    WHERE at2.num_pec = at.num_pec
                ) + (
                    SELECT COALESCE(SUM(COALESCE(lrh.montant, 0) * COALESCE(lrh.qte, 1)), 0)
                    FROM acte_trans at3
                    LEFT JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at3.id_acte_trans
                    WHERE at3.num_pec = at.num_pec
                ) AS montant_total_pec,
                tp.libelle_type_prestation AS LIBELLE_TYPE_PRESTATION,
                (
                    SELECT eq.libelle_etat_qualificatif
                    FROM list_acte_acte_trans laat
                    LEFT JOIN etat_qualificatif eq ON eq.id_etat_qualificatif = laat.id_etat_qualificatif
                    WHERE laat.id_acte_trans = at.id_acte_trans
                    LIMIT 1
                ) AS libelle_etat_qualificatif,
                s_init.nom_structure AS structure_initiatrice,
                s_prop.nom_structure AS structure_propose,
                s_exec.nom_structure AS structure_executante,
                s_orig.nom_structure AS structure_origine_bulletin,
                CONCAT(COALESCE(p_init.nom_personnel, ''), ' ', COALESCE(p_init.prenoms_personnel, '')) AS ps_initiateur,
                p_init.tel AS tel_initiateur,
                CONCAT(COALESCE(p_exec.nom_personnel, ''), ' ', COALESCE(p_exec.prenoms_personnel, '')) AS ps_executant,
                p_exec.tel AS tel_executant,
                at.date_dmd_acte_trans,
                at.date_debut_execution,
                at.date_fin_execution,
                at.date_accuser_reception,
                at.cle_validation,
                at.nombre_jour_hospitalisation,
                t.num_bnf,
                SUBSTRING_INDEX(t.nom_prenom, ' ', 1) AS nom_beneficiaire,
                SUBSTRING_INDEX(t.nom_prenom, ' ', -1) AS prenom_beneficiaire,
                t.date_naissance,
                t.telephone,
                t.sexe
            FROM acte_trans at
            LEFT JOIN structure s_exec ON s_exec.id_structure = at.id_structure_executante
            LEFT JOIN structure s_init ON s_init.id_structure = at.id_structure_initiatrice
            LEFT JOIN structure s_prop ON s_prop.id_structure = at.id_structure_propose
            LEFT JOIN structure s_orig ON s_orig.id_structure = at.id_structure_origine_bulletin
            LEFT JOIN type_prestation tp ON tp.id_type_prest = at.id_type_prest
            LEFT JOIN personnel p_init ON p_init.id_personnel = at.id_ps_initiateur
            LEFT JOIN personnel p_exec ON p_exec.id_personnel = at.id_ps_executant
            LEFT JOIN `transaction` t ON t.num_trans = at.num_trans
            WHERE DATE(at.date_debut_execution) BETWEEN :date_debut AND :date_fin
              AND at.deleted_at IS NULL
        """

        params = {
            'date_debut': date_debut,
            'date_fin': date_fin,
            'limit': limit,
            'offset': offset
        }

        # Ajout des conditions de montant dans une sous-requête HAVING
        query += " HAVING montant_total_pec > 0"

        if montant_min is not None and montant_min > 0:
            query += " AND montant_total_pec > :montant_min"
            params['montant_min'] = montant_min

        if montant_max is not None:
            query += " AND montant_total_pec < :montant_max"
            params['montant_max'] = montant_max

        query += " ORDER BY at.num_pec"
        query += " LIMIT :limit OFFSET :offset"

        return ActeModel.execute_query(query, params)

    @staticmethod
    def count_detailed_pec(date_debut, date_fin, montant_min=None, montant_max=None):
        """
        Compte le nombre total de PEC pour la pagination

        Returns:
            Nombre total de PEC
        """
        query = """
            SELECT COUNT(DISTINCT at.num_pec) as total
            FROM acte_trans at
            WHERE DATE(at.date_debut_execution) BETWEEN :date_debut AND :date_fin
              AND at.deleted_at IS NULL
              AND (
                  (
                      SELECT COALESCE(SUM(COALESCE(laa.montant_acte, 0) * COALESCE(laa.quantite, 1)), 0)
                      FROM acte_trans at2
                      LEFT JOIN list_acte_acte_trans laa ON laa.id_acte_trans = at2.id_acte_trans
                      WHERE at2.num_pec = at.num_pec
                  ) + (
                      SELECT COALESCE(SUM(COALESCE(lrh.montant, 0) * COALESCE(lrh.qte, 1)), 0)
                      FROM acte_trans at3
                      LEFT JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at3.id_acte_trans
                      WHERE at3.num_pec = at.num_pec
                  )
              ) > 0
        """

        params = {
            'date_debut': date_debut,
            'date_fin': date_fin
        }

        if montant_min is not None and montant_min > 0:
            query += """
              AND (
                  (
                      SELECT COALESCE(SUM(COALESCE(laa.montant_acte, 0) * COALESCE(laa.quantite, 1)), 0)
                      FROM acte_trans at2
                      LEFT JOIN list_acte_acte_trans laa ON laa.id_acte_trans = at2.id_acte_trans
                      WHERE at2.num_pec = at.num_pec
                  ) + (
                      SELECT COALESCE(SUM(COALESCE(lrh.montant, 0) * COALESCE(lrh.qte, 1)), 0)
                      FROM acte_trans at3
                      LEFT JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at3.id_acte_trans
                      WHERE at3.num_pec = at.num_pec
                  )
              ) > :montant_min
            """
            params['montant_min'] = montant_min

        if montant_max is not None:
            query += """
              AND (
                  (
                      SELECT COALESCE(SUM(COALESCE(laa.montant_acte, 0) * COALESCE(laa.quantite, 1)), 0)
                      FROM acte_trans at2
                      LEFT JOIN list_acte_acte_trans laa ON laa.id_acte_trans = at2.id_acte_trans
                      WHERE at2.num_pec = at.num_pec
                  ) + (
                      SELECT COALESCE(SUM(COALESCE(lrh.montant, 0) * COALESCE(lrh.qte, 1)), 0)
                      FROM acte_trans at3
                      LEFT JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at3.id_acte_trans
                      WHERE at3.num_pec = at.num_pec
                  )
              ) < :montant_max
            """
            params['montant_max'] = montant_max

        return ActeModel.execute_scalar(query, params) or 0

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
