"""Modèle pour le scénario 2: Analyse consolidée par dossier et structure"""
from sqlalchemy import text


class Scenario2Model:
    """Gestion des données pour l'analyse consolidée des montants exécutés"""

    @staticmethod
    def execute_query(query, params=None):
        """
        Exécute une requête SQL sur la base MariaDB du scénario 2

        Args:
            query: Requête SQL avec placeholders
            params: Dictionnaire des paramètres

        Returns:
            Liste de dictionnaires (résultats)
        """
        from app import mariadb_session
        try:
            if mariadb_session is None:
                raise Exception("Connexion MariaDB non disponible. Veuillez configurer les paramètres dans le fichier .env")

            result = mariadb_session.execute(text(query), params or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            if mariadb_session:
                mariadb_session.rollback()
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
        from app import mariadb_session
        try:
            if mariadb_session is None:
                raise Exception("Connexion MariaDB non disponible. Veuillez configurer les paramètres dans le fichier .env")

            result = mariadb_session.execute(text(query), params or {})
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            if mariadb_session:
                mariadb_session.rollback()
            raise Exception(f"Erreur lors de l'exécution de la requête: {str(e)}")

    @staticmethod
    def get_consolidated_data(
        date_debut,
        date_fin,
        montant_min=None,
        montant_max=None,
        include_acte=True,
        include_rub=True,
        num_bnf=None,
        nom_prenom=None,
        id_structures=None,
        num_pec=None,
        sort_by='num_pec',
        sort_order='ASC',
        limit=500,
        offset=0
    ):
        """
        Récupère les données consolidées selon la NOUVELLE logique :
        Groupement par (num_pec, structure, source_ligne, libelle_acte, montant_unitaire)

        Le montant cumulé par num_pec sera la SOMME de tous les montants groupés pour ce num_pec
        """

        params = {
            'date_debut': date_debut,
            'date_fin': date_fin,
            'limit': limit,
            'offset': offset
        }

        if montant_min is not None:
            params['montant_min'] = montant_min
        if montant_max is not None:
            params['montant_max'] = montant_max

        # Construction de la CTE lignes avec filtres de dates et montants
        union_parts = []

        if include_rub:
            rub_query = """
                SELECT
                    at.num_pec,
                    at.id_structure_executante              AS id_structure,
                    s.nom_structure                         AS nom_structure,
                    at.num_trans,
                    lrh.id_acte_trans,
                    COALESCE(lrh.id_acte, lrh.id_rub_hospit) AS ref_id,
                    COALESCE(a2.libelle_acte, rh.libelle)   AS libelle_acte,
                    lrh.date_execution_acte                 AS date_execution,
                    lrh.montant                             AS montant,
                    lrh.qte                                 AS nb_orig,
                    'RUB'                                   AS source_ligne
                FROM acte_trans at
                JOIN list_rub_hosp_acte_trans lrh
                    ON lrh.id_acte_trans = at.id_acte_trans
                JOIN structure s
                    ON s.id_structure = at.id_structure_executante
                LEFT JOIN acte a2
                    ON a2.id_acte = lrh.id_acte
                LEFT JOIN rubrique_hospitalisations rh
                    ON rh.id = lrh.id_rub_hospit
                WHERE lrh.date_execution_acte BETWEEN :date_debut AND :date_fin
            """
            if montant_min is not None:
                rub_query += " AND lrh.montant >= :montant_min"
            if montant_max is not None:
                rub_query += " AND lrh.montant <= :montant_max"
            union_parts.append(rub_query)

        if include_acte:
            acte_query = """
                SELECT
                    at.num_pec,
                    at.id_structure_executante              AS id_structure,
                    s.nom_structure                         AS nom_structure,
                    at.num_trans,
                    laa.id_acte_trans,
                    laa.id_acte                             AS ref_id,
                    a.libelle_acte                          AS libelle_acte,
                    laa.date_execution_acte                 AS date_execution,
                    laa.montant_acte                        AS montant,
                    laa.quantite                            AS nb_orig,
                    'ACTE'                                  AS source_ligne
                FROM acte_trans at
                JOIN list_acte_acte_trans laa
                    ON laa.id_acte_trans = at.id_acte_trans
                JOIN structure s
                    ON s.id_structure = at.id_structure_executante
                LEFT JOIN acte a
                    ON a.id_acte = laa.id_acte
                WHERE laa.date_execution_acte BETWEEN :date_debut AND :date_fin
            """
            if montant_min is not None:
                acte_query += " AND laa.montant_acte >= :montant_min"
            if montant_max is not None:
                acte_query += " AND laa.montant_acte <= :montant_max"
            union_parts.append(acte_query)

        if not union_parts:
            return []

        lignes_cte = "\n UNION ALL \n".join(union_parts)

        # Filtres WHERE sur les lignes groupées
        where_conditions = []

        if num_pec:
            where_conditions.append("agg.num_pec LIKE :num_pec")
            params['num_pec'] = f"%{num_pec}%"

        if id_structures:
            placeholders = ','.join([f':struct_{i}' for i in range(len(id_structures))])
            where_conditions.append(f"agg.id_structure IN ({placeholders})")
            for i, struct_id in enumerate(id_structures):
                params[f'struct_{i}'] = struct_id

        # Filtres bénéficiaires
        if num_bnf:
            where_conditions.append("tr.num_bnf LIKE :num_bnf")
            params['num_bnf'] = f"%{num_bnf}%"

        if nom_prenom:
            where_conditions.append("tr.nom_prenom LIKE :nom_prenom")
            params['nom_prenom'] = f"%{nom_prenom}%"

        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Construction CTE pour total cumulé par PEC SANS filtres de dates/montants
        # IMPORTANT: On inclut TOUJOURS ACTE + RUB pour le total, indépendamment des filtres
        lignes_total_cte = """
            SELECT
                at.num_pec,
                lrh.montant * lrh.qte AS montant_total
            FROM acte_trans at
            JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at.id_acte_trans

            UNION ALL

            SELECT
                at.num_pec,
                laa.montant_acte * laa.quantite AS montant_total
            FROM acte_trans at
            JOIN list_acte_acte_trans laa ON laa.id_acte_trans = at.id_acte_trans
        """

        # Requête principale avec groupement correct
        query = f"""
        WITH lignes AS (
            {lignes_cte}
        ),
        lignes_total_pec AS (
            /* TOUTES les lignes du PEC sans filtres de dates/montants */
            {lignes_total_cte}
        ),
        totaux_pec AS (
            /* Calcul du VRAI total cumulé par num_pec (sans filtres) */
            SELECT
                num_pec,
                COALESCE(SUM(montant_total), 0) AS montant_group_numpec
            FROM lignes_total_pec
            GROUP BY num_pec
        ),
        agg AS (
            SELECT
                li.num_pec,
                li.id_structure,
                li.nom_structure,
                li.source_ligne,
                li.libelle_acte,

                /* nb = somme des quantités pour ce couple (libellé, montant_unitaire) */
                SUM(li.nb_orig) AS nb_lignes,

                /* montant groupé = somme des (montant_unitaire * qte) */
                COALESCE(SUM(li.montant * li.nb_orig), 0) AS montant_execute_total,

                MIN(li.date_execution) AS premiere_date_execution,
                MAX(li.date_execution) AS derniere_date_execution,

                /* Récupérer un num_trans pour pouvoir joindre avec transaction */
                MAX(li.num_trans) AS num_trans

            FROM lignes li
            GROUP BY
                li.num_pec,
                li.id_structure,
                li.nom_structure,
                li.source_ligne,
                li.libelle_acte,
                li.montant  /* IMPORTANT : on groupe par montant unitaire */
        ),
        enriched AS (
            SELECT
                agg.*,
                tr.num_bnf,
                tr.nom_prenom,
                tr.telephone,
                tr.sexe,
                tr.date_naissance,
                tt.libelle_type_trans
            FROM agg
            LEFT JOIN `transaction` tr ON tr.num_trans = agg.num_trans
            LEFT JOIN type_transactions tt ON tt.id_type_trans = tr.id_type_trans
            {where_clause}
        )
        SELECT
            enriched.*,
            totaux_pec.montant_group_numpec
        FROM enriched
        LEFT JOIN totaux_pec ON totaux_pec.num_pec = enriched.num_pec
        ORDER BY {Scenario2Model._build_order_clause(sort_by, sort_order)}
        LIMIT :limit OFFSET :offset
        """

        return Scenario2Model.execute_query(query, params)

    @staticmethod
    def count_consolidated_data(
        date_debut,
        date_fin,
        montant_min=None,
        montant_max=None,
        include_acte=True,
        include_rub=True,
        num_bnf=None,
        nom_prenom=None,
        id_structures=None,
        num_pec=None
    ):
        """
        Compte le nombre total de résultats consolidés selon la NOUVELLE logique
        Compte les groupes par (num_pec, structure, source_ligne, libelle_acte, montant_unitaire)
        """

        params = {
            'date_debut': date_debut,
            'date_fin': date_fin
        }

        if montant_min is not None:
            params['montant_min'] = montant_min
        if montant_max is not None:
            params['montant_max'] = montant_max

        # Construction de la CTE lignes avec filtres de dates et montants
        union_parts = []

        if include_rub:
            rub_query = """
                SELECT
                    at.num_pec,
                    at.id_structure_executante              AS id_structure,
                    s.nom_structure                         AS nom_structure,
                    at.num_trans,
                    lrh.id_acte_trans,
                    COALESCE(lrh.id_acte, lrh.id_rub_hospit) AS ref_id,
                    COALESCE(a2.libelle_acte, rh.libelle)   AS libelle_acte,
                    lrh.date_execution_acte                 AS date_execution,
                    lrh.montant                             AS montant,
                    lrh.qte                                 AS nb_orig,
                    'RUB'                                   AS source_ligne
                FROM acte_trans at
                JOIN list_rub_hosp_acte_trans lrh
                    ON lrh.id_acte_trans = at.id_acte_trans
                JOIN structure s
                    ON s.id_structure = at.id_structure_executante
                LEFT JOIN acte a2
                    ON a2.id_acte = lrh.id_acte
                LEFT JOIN rubrique_hospitalisations rh
                    ON rh.id = lrh.id_rub_hospit
                WHERE lrh.date_execution_acte BETWEEN :date_debut AND :date_fin
            """
            if montant_min is not None:
                rub_query += " AND lrh.montant >= :montant_min"
            if montant_max is not None:
                rub_query += " AND lrh.montant <= :montant_max"
            union_parts.append(rub_query)

        if include_acte:
            acte_query = """
                SELECT
                    at.num_pec,
                    at.id_structure_executante              AS id_structure,
                    s.nom_structure                         AS nom_structure,
                    at.num_trans,
                    laa.id_acte_trans,
                    laa.id_acte                             AS ref_id,
                    a.libelle_acte                          AS libelle_acte,
                    laa.date_execution_acte                 AS date_execution,
                    laa.montant_acte                        AS montant,
                    laa.quantite                            AS nb_orig,
                    'ACTE'                                  AS source_ligne
                FROM acte_trans at
                JOIN list_acte_acte_trans laa
                    ON laa.id_acte_trans = at.id_acte_trans
                JOIN structure s
                    ON s.id_structure = at.id_structure_executante
                LEFT JOIN acte a
                    ON a.id_acte = laa.id_acte
                WHERE laa.date_execution_acte BETWEEN :date_debut AND :date_fin
            """
            if montant_min is not None:
                acte_query += " AND laa.montant_acte >= :montant_min"
            if montant_max is not None:
                acte_query += " AND laa.montant_acte <= :montant_max"
            union_parts.append(acte_query)

        if not union_parts:
            return 0

        lignes_cte = "\n UNION ALL \n".join(union_parts)

        # Filtres WHERE
        where_conditions = []

        if num_pec:
            where_conditions.append("agg.num_pec LIKE :num_pec")
            params['num_pec'] = f"%{num_pec}%"

        if id_structures:
            placeholders = ','.join([f':struct_{i}' for i in range(len(id_structures))])
            where_conditions.append(f"agg.id_structure IN ({placeholders})")
            for i, struct_id in enumerate(id_structures):
                params[f'struct_{i}'] = struct_id

        if num_bnf:
            where_conditions.append("tr.num_bnf LIKE :num_bnf")
            params['num_bnf'] = f"%{num_bnf}%"

        if nom_prenom:
            where_conditions.append("tr.nom_prenom LIKE :nom_prenom")
            params['nom_prenom'] = f"%{nom_prenom}%"

        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        query = f"""
        WITH lignes AS (
            {lignes_cte}
        ),
        agg AS (
            SELECT
                li.num_pec,
                li.id_structure,
                li.nom_structure,
                li.source_ligne,
                li.libelle_acte,
                MAX(li.num_trans) AS num_trans
            FROM lignes li
            GROUP BY
                li.num_pec,
                li.id_structure,
                li.nom_structure,
                li.source_ligne,
                li.libelle_acte,
                li.montant  /* IMPORTANT : même groupement que get_consolidated_data */
        )
        SELECT COUNT(*) as total
        FROM agg
        LEFT JOIN `transaction` tr ON tr.num_trans = agg.num_trans
        {where_clause}
        """

        return Scenario2Model.execute_scalar(query, params) or 0

    @staticmethod
    def _build_order_clause(sort_by, sort_order):
        """Construit la clause ORDER BY de manière sécurisée"""
        valid_columns = {
            'num_pec': 'enriched.num_pec',
            'nom_structure': 'enriched.nom_structure',
            'date_execution': 'enriched.premiere_date_execution',
            'montant_total': 'enriched.montant_execute_total',
            'nb_lignes': 'enriched.nb_lignes'
        }

        column = valid_columns.get(sort_by, 'enriched.num_pec')
        order = 'DESC' if sort_order.upper() == 'DESC' else 'ASC'

        return f"{column} {order}, enriched.nom_structure ASC, enriched.libelle_acte ASC"

    @staticmethod
    def get_structures_list():
        """Récupère la liste des structures pour le formulaire"""
        query = """
        SELECT DISTINCT
            id_structure,
            nom_structure
        FROM structure
        WHERE structure_active = 1
          AND deleted_at IS NULL
        ORDER BY nom_structure
        """
        return Scenario2Model.execute_query(query, {})

    @staticmethod
    def get_facture_details(num_pec):
        """
        Récupère les détails groupés par (libelle_acte, montant) pour un num_pec donné
        Retourne le regroupement des actes/rubriques avec nb de lignes, montant cumulé et dates
        Inclut aussi le nom et prénom du bénéficiaire
        """
        query = """
        WITH lignes AS (
          /* (A) ACTE */
          SELECT
              at.num_pec,
              at.id_structure_executante                  AS id_structure,
              s.nom_structure                             AS nom_structure,
              at.num_trans,
              laa.id_acte_trans,
              laa.id_acte                                 AS ref_id,
              a.libelle_acte                              AS libelle_acte,
              laa.date_execution_acte                     AS date_execution,
              laa.montant_acte                            AS montant,
              laa.quantite                                AS nb_orig,
              'ACTE'                                      AS source_ligne
          FROM acte_trans at
          JOIN list_acte_acte_trans laa
            ON laa.id_acte_trans = at.id_acte_trans
          JOIN structure s
            ON s.id_structure = at.id_structure_executante
          LEFT JOIN acte a
            ON a.id_acte = laa.id_acte

          UNION ALL

          /* (B) RUB */
          SELECT
              at.num_pec,
              at.id_structure_executante                  AS id_structure,
              s.nom_structure                             AS nom_structure,
              at.num_trans,
              lrh.id_acte_trans,
              COALESCE(lrh.id_acte, lrh.id_rub_hospit)    AS ref_id,
              COALESCE(a2.libelle_acte, rh.libelle)       AS libelle_acte,
              lrh.date_execution_acte                     AS date_execution,
              lrh.montant                                 AS montant,
              lrh.qte                                     AS nb_orig,
              'RUB'                                       AS source_ligne
          FROM acte_trans at
          JOIN list_rub_hosp_acte_trans lrh
            ON lrh.id_acte_trans = at.id_acte_trans
          JOIN structure s
            ON s.id_structure = at.id_structure_executante
          LEFT JOIN acte a2
            ON a2.id_acte = lrh.id_acte
          LEFT JOIN rubrique_hospitalisations rh
            ON rh.id = lrh.id_rub_hospit
        ),
        beneficiaire_info AS (
          /* Récupérer les infos du bénéficiaire */
          SELECT DISTINCT
            at.num_pec,
            tr.nom_prenom,
            tr.num_bnf
          FROM acte_trans at
          LEFT JOIN `transaction` tr ON tr.num_trans = at.num_trans
          WHERE at.num_pec = :num_pec
          LIMIT 1
        )

        SELECT
          li.num_pec,
          li.id_structure,
          li.nom_structure,
          li.source_ligne,
          li.libelle_acte,

          /* nb = somme des quantités (nb_orig) pour ce couple (libellé, montant_unitaire) */
          SUM(li.nb_orig) AS nb,

          /* montant groupé = somme des (montant_unitaire * qte) */
          SUM(li.montant * li.nb_orig) AS montant,

          /* repères temporels utiles */
          MIN(li.date_execution) AS premiere_date_execution,
          MAX(li.date_execution) AS derniere_date_execution,

          /* Infos bénéficiaire */
          MAX(bi.nom_prenom) AS nom_prenom,
          MAX(bi.num_bnf) AS num_bnf

        FROM lignes li
        LEFT JOIN beneficiaire_info bi ON bi.num_pec = li.num_pec
        WHERE li.num_pec = :num_pec
        GROUP BY
          li.num_pec,
          li.id_structure,
          li.nom_structure,
          li.source_ligne,
          li.libelle_acte,
          /* on groupe par le montant unitaire pour regrouper "libellé + montant" identiques */
          li.montant
        ORDER BY
          li.libelle_acte ASC,
          li.montant ASC
        """

        return Scenario2Model.execute_query(query, {'num_pec': num_pec})
