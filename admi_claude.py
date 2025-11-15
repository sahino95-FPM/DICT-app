#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de génération d'état synthétique des PEC
===============================================

Objectif:
    Générer un état synthétique listant tous les num_pec dont la date_debut_execution
    est comprise entre deux dates, avec agrégation des montants depuis SQL_TAMPON.

Entrées:
    - date_debut (YYYY-MM-DD)
    - date_fin (YYYY-MM-DD)
    - Connexion à la base de données

Sortie:
    DataFrame avec les colonnes: num_pec, montant_total_pec, LIBELLE_TYPE_PRESTATION,
    libelle_etat_qualificatif, structure_initiatrice, structure_propose, structure_executante,
    structure_origine_bulletin, ps_initiateur, tel_initiateur, ps_executant, tel_executant,
    date_dmd_acte_trans, date_debut_execution, date_fin_execution, date_accuser_reception,
    cle_validation, nombre_jour_hospitalisation, num_bnf, nom_beneficiaire, prenom_beneficiaire,
    date_naissance, telephone, sexe
"""

import pandas as pd
import pymysql
from datetime import datetime
from typing import Optional, Dict, Any
import sys
import warnings
import io

# Configurer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Supprimer les avertissements pandas
warnings.filterwarnings('ignore')


class GenerateurEtatPEC:
    """Classe pour générer l'état synthétique des PEC"""
    
    def __init__(self, config_db: Dict[str, Any]):
        """
        Initialise le générateur avec la configuration de la base de données
        
        Args:
            config_db: Dictionnaire contenant host, database, user, password, port
        """
        self.config_db = config_db
        self.connection = None
    
    def connecter(self) -> bool:
        """
        Établit la connexion à la base de données
        
        Returns:
            True si la connexion est réussie, False sinon
        """
        
        try:
            self.connection = pymysql.connect(
                host='192.168.10.214',
                user='user_daci',
                password='Prestige2025',
                database='admi',
                port=3306,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print("✓ Connexion à la base de données établie")
            return True
        except Exception as e:
            print(f"✗ Erreur de connexion à la base de données: {e}")
            return False
    
    def deconnecter(self):
        """Ferme la connexion à la base de données"""
        if self.connection and self.connection.open:
            self.connection.close()
            print("✓ Connexion fermée")
    
    def executer_sql_tampon(self, num_pec: str) -> pd.DataFrame:
        """
        Exécute le script SQL_TAMPON pour un num_pec donné
        
        Args:
            num_pec: Numéro de PEC à traiter
            
        Returns:
            DataFrame contenant les lignes de détail avec la colonne montant
        """
        sql_tampon = """
        WITH lignes AS (
          /* (A) Lignes ACTE */
          SELECT
            at.num_pec,
            at.id_structure_executante AS id_structure,
            s.nom_structure,
            at.num_trans,
            laa.id_acte_trans,
            laa.id_acte AS ref_id,
            a.libelle_acte AS libelle_acte,
            laa.date_execution_acte AS date_execution,
            laa.montant_acte AS montant,
            laa.quantite AS nb,
            NULL AS coefficient,
            'ACTE' AS source_ligne
          FROM acte_trans at
          JOIN list_acte_acte_trans laa ON laa.id_acte_trans = at.id_acte_trans
          JOIN structure s ON s.id_structure = at.id_structure_executante
          LEFT JOIN acte a ON a.id_acte = laa.id_acte
          WHERE at.num_pec = %s

          UNION ALL

          /* (B) Lignes RUB (rubriques hospitalisation) */
          SELECT
            at.num_pec,
            at.id_structure_executante AS id_structure,
            s.nom_structure,
            at.num_trans,
            lrh.id_acte_trans,
            COALESCE(lrh.id_acte, lrh.id_rub_hospit) AS ref_id,
            COALESCE(a2.libelle_acte, rh.libelle) AS libelle_acte,
            lrh.date_execution_acte AS date_execution,
            lrh.montant AS montant,
            lrh.qte AS nb,
            NULL AS coefficient,
            'RUB' AS source_ligne
          FROM acte_trans at
          JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at.id_acte_trans
          JOIN structure s ON s.id_structure = at.id_structure_executante
          LEFT JOIN acte a2 ON a2.id_acte = lrh.id_acte
          LEFT JOIN rubrique_hospitalisations rh ON rh.id = lrh.id_rub_hospit
          WHERE at.num_pec = %s
        )
        SELECT
          li.num_pec,
          li.id_structure,
          li.nom_structure,
          li.num_trans,
          li.id_acte_trans,
          li.ref_id,
          li.libelle_acte,
          li.source_ligne,
          li.date_execution,
          li.montant,
          li.nb,
          li.coefficient
        FROM lignes li
        ORDER BY
          li.date_execution ASC,
          li.source_ligne ASC,
          li.ref_id ASC
        """
        
        try:
            # Exécuter la requête avec le cursor (DictCursor)
            with self.connection.cursor() as cursor:
                cursor.execute(sql_tampon, [num_pec, num_pec])
                results = cursor.fetchall()

            # Créer le DataFrame manuellement à partir des dictionnaires
            df = pd.DataFrame(results)
            return df
        except Exception as e:
            print(f"✗ Erreur lors de l'exécution SQL_TAMPON pour {num_pec}: {e}")
            return pd.DataFrame()
    
    def recuperer_pec_eligibles(self, date_debut: str, date_fin: str) -> pd.DataFrame:
        """
        Récupère tous les num_pec éligibles selon le critère de date_debut_execution
        avec les informations du bénéficiaire et l'état qualificatif

        Args:
            date_debut: Date de début au format YYYY-MM-DD
            date_fin: Date de fin au format YYYY-MM-DD

        Returns:
            DataFrame contenant les num_pec éligibles avec infos structure, bénéficiaire et état qualificatif
        """
        sql_eligibles = """
        SELECT DISTINCT
            at.num_pec,
            s.nom_structure AS structure,
            at.id_structure_executante,
            at.id_structure_initiatrice,
            at.id_structure_propose,
            at.id_structure_origine_bulletin,
            at.id_ps_initiateur,
            at.id_ps_executant,
            at.num_trans,
            at.date_debut_execution,
            at.id_acte_trans,
            at.date_dmd_acte_trans,
            at.date_fin_execution,
            at.date_accuser_reception,
            at.cle_validation,
            at.nombre_jour_hospitalisation,
            at.id_type_prest
        FROM acte_trans at
        JOIN structure s ON s.id_structure = at.id_structure_executante
        WHERE DATE(at.date_debut_execution) BETWEEN %s AND %s
          AND at.deleted_at IS NULL
        ORDER BY at.num_pec
        """

        try:
            # Exécuter la requête avec le cursor (DictCursor)
            with self.connection.cursor() as cursor:
                cursor.execute(sql_eligibles, [date_debut, date_fin])
                results = cursor.fetchall()

            # Créer le DataFrame manuellement à partir des dictionnaires
            # (pd.read_sql ne fonctionne pas bien avec DictCursor)
            df_eligibles = pd.DataFrame(results)

            print(f"✓ {len(df_eligibles)} PEC éligibles trouvés")
            return df_eligibles
        except Exception as e:
            print(f"✗ Erreur lors de la récupération des PEC éligibles: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def recuperer_nom_structure(self, id_structure: int) -> str:
        """
        Récupère le nom d'une structure par son ID

        Args:
            id_structure: Identifiant de la structure

        Returns:
            Nom de la structure ou None si non trouvé
        """
        if id_structure is None or pd.isna(id_structure):
            return None

        sql_structure = """
        SELECT nom_structure
        FROM structure
        WHERE id_structure = %s
        LIMIT 1
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql_structure, [id_structure])
                result = cursor.fetchone()

            if result:
                return result.get('nom_structure')
            else:
                return None
        except Exception as e:
            # Afficher l'erreur seulement la première fois
            if not hasattr(self, '_erreur_structure_affichee'):
                print(f"\n⚠️  Erreur récupération structure: {e}")
                self._erreur_structure_affichee = True
            return None

    def recuperer_nom_personnel(self, id_personnel: int) -> dict:
        """
        Récupère le nom complet et le téléphone d'un personnel par son ID

        Args:
            id_personnel: Identifiant du personnel

        Returns:
            Dictionnaire avec 'nom_complet' et 'telephone', ou None pour les deux si non trouvé
        """
        if id_personnel is None or pd.isna(id_personnel):
            return {'nom_complet': None, 'telephone': None}

        sql_personnel = """
        SELECT nom_personnel, prenoms_personnel, tel
        FROM personnel
        WHERE id_personnel = %s
        LIMIT 1
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql_personnel, [id_personnel])
                result = cursor.fetchone()

            if result:
                nom = result.get('nom_personnel', '')
                prenoms = result.get('prenoms_personnel', '')
                telephone = result.get('tel')

                # Concaténer nom et prénoms
                nom_complet = None
                if nom and prenoms:
                    nom_complet = f"{nom} {prenoms}"
                elif nom:
                    nom_complet = nom
                elif prenoms:
                    nom_complet = prenoms

                return {
                    'nom_complet': nom_complet,
                    'telephone': telephone
                }
            else:
                return {'nom_complet': None, 'telephone': None}
        except Exception as e:
            # Afficher l'erreur seulement la première fois
            if not hasattr(self, '_erreur_personnel_affichee'):
                print(f"\n⚠️  Erreur récupération personnel: {e}")
                self._erreur_personnel_affichee = True
            return {'nom_complet': None, 'telephone': None}

    def recuperer_libelle_type_prestation(self, id_type_prest: int) -> str:
        """
        Récupère le libellé du type de prestation par son ID

        Args:
            id_type_prest: Identifiant du type de prestation

        Returns:
            Libellé du type de prestation ou None si non trouvé
        """
        if id_type_prest is None or pd.isna(id_type_prest):
            return None

        sql_type_prestation = """
        SELECT libelle_type_prestation
        FROM type_prestation
        WHERE id_type_prest = %s
        LIMIT 1
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql_type_prestation, [id_type_prest])
                result = cursor.fetchone()

            if result:
                return result.get('libelle_type_prestation')
            else:
                return None
        except Exception as e:
            # Afficher l'erreur seulement la première fois
            if not hasattr(self, '_erreur_type_prestation_affichee'):
                print(f"\n⚠️  Erreur récupération type prestation: {e}")
                print(f"    SQL utilisé: {sql_type_prestation.strip()}")
                print(f"    Paramètre: id_type_prest = '{id_type_prest}'")
                self._erreur_type_prestation_affichee = True
            return None

    def recuperer_etat_qualificatif(self, id_acte_trans: int) -> str:
        """
        Récupère le libellé de l'état qualificatif pour un acte_trans donné

        Args:
            id_acte_trans: Identifiant de l'acte transaction

        Returns:
            Libellé de l'état qualificatif ou None si non trouvé
        """
        sql_etat = """
        SELECT DISTINCT eq.libelle_etat_qualificatif
        FROM list_acte_acte_trans laat
        JOIN etat_qualificatif eq ON eq.id_etat_qualificatif = laat.id_etat_qualificatif
        WHERE laat.id_acte_trans = %s
        LIMIT 1
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql_etat, [id_acte_trans])
                result = cursor.fetchone()

            if result:
                return result.get('libelle_etat_qualificatif')
            else:
                return None
        except Exception as e:
            # Afficher l'erreur seulement la première fois
            if not hasattr(self, '_erreur_etat_qualificatif_affichee'):
                print(f"\n⚠️  Erreur récupération état qualificatif: {e}")
                print(f"    SQL utilisé: {sql_etat.strip()}")
                print(f"    Paramètre: id_acte_trans = '{id_acte_trans}'")
                self._erreur_etat_qualificatif_affichee = True
            return None

    def recuperer_info_beneficiaire(self, num_trans: str) -> Dict[str, Any]:
        """
        Récupère les informations du bénéficiaire directement depuis la table transaction

        Args:
            num_trans: Numéro de transaction

        Returns:
            Dictionnaire contenant num_bnf, nom, prenom, date_naissance, telephone, sexe du bénéficiaire
        """
        sql_beneficiaire = """
        SELECT
            num_bnf,
            nom_prenom,
            date_naissance,
            telephone,
            sexe
        FROM transaction
        WHERE num_trans = %s
        LIMIT 1
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql_beneficiaire, [num_trans])
                result = cursor.fetchone()

            if result:
                # Séparer nom_prenom en nom et prenom
                nom_prenom = result.get('nom_prenom', '')
                if nom_prenom:
                    # On essaie de séparer intelligemment
                    # Format attendu : "NOM PRENOM" ou "NOM Prenom"
                    parties = nom_prenom.split(' ', 1)
                    nom = parties[0] if len(parties) > 0 else None
                    prenom = parties[1] if len(parties) > 1 else None
                else:
                    nom = None
                    prenom = None

                return {
                    'num_bnf': result.get('num_bnf'),
                    'nom_beneficiaire': nom,
                    'prenom_beneficiaire': prenom,
                    'date_naissance': result.get('date_naissance'),
                    'telephone': result.get('telephone'),
                    'sexe': result.get('sexe')
                }
            else:
                return {
                    'num_bnf': None,
                    'nom_beneficiaire': None,
                    'prenom_beneficiaire': None,
                    'date_naissance': None,
                    'telephone': None,
                    'sexe': None
                }
        except Exception as e:
            # Afficher l'erreur seulement la première fois
            if not hasattr(self, '_erreur_beneficiaire_affichee'):
                print(f"\n⚠️  Erreur récupération bénéficiaire: {e}")
                print(f"    SQL utilisé: {sql_beneficiaire.strip()}")
                print(f"    Paramètre: num_trans = '{num_trans}'")
                self._erreur_beneficiaire_affichee = True
            return {
                'num_bnf': None,
                'nom_beneficiaire': None,
                'prenom_beneficiaire': None,
                'date_naissance': None,
                'telephone': None,
                'sexe': None
            }
    
    def calculer_montant_total_pec(self, num_pec: str, debug: bool = False) -> float:
        """
        Calcule le montant total pour un num_pec en exécutant SQL_TAMPON
        et en sommant la colonne montant

        Args:
            num_pec: Numéro de PEC
            debug: Active le mode debug pour afficher plus d'infos

        Returns:
            Montant total (somme des montants)
        """
        df_tampon = self.executer_sql_tampon(num_pec)

        if debug:
            print(f"\n[DEBUG] PEC: {num_pec}")
            print(f"[DEBUG] Nombre de lignes retournées par SQL_TAMPON: {len(df_tampon)}")
            if not df_tampon.empty:
                print(f"[DEBUG] Colonnes: {df_tampon.columns.tolist()}")
                print(f"[DEBUG] Aperçu des montants:")
                print(df_tampon[['num_pec', 'montant', 'nb', 'libelle_acte']].head(10))

        if df_tampon.empty:
            if debug:
                print(f"[DEBUG] Aucune donnée retournée pour {num_pec}")
            return 0.0

        # Calculer montant × quantité pour chaque ligne
        # Si nb (quantité) est NULL, utiliser 1
        df_tampon['nb'] = df_tampon['nb'].fillna(1)
        df_tampon['montant_ligne'] = df_tampon['montant'].fillna(0) * df_tampon['nb']

        # Somme des montants × quantités
        montant_total = df_tampon['montant_ligne'].sum()

        if debug:
            print(f"[DEBUG] Montant total calculé (montant × quantité): {montant_total}")

        return float(montant_total)
    
    def generer_etat_synthetique(self, date_debut: str, date_fin: str,
                                   montant_mini: float = 0, montant_maxi: float = float('inf')) -> pd.DataFrame:
        """
        Génère l'état synthétique complet

        Args:
            date_debut: Date de début au format YYYY-MM-DD
            date_fin: Date de fin au format YYYY-MM-DD
            montant_mini: Montant minimum (par défaut 0)
            montant_maxi: Montant maximum (par défaut infini)

        Returns:
            DataFrame avec l'état synthétique final
        """
        print(f"\n{'='*70}")
        print(f"Génération de l'état synthétique PEC")
        print(f"Période: du {date_debut} au {date_fin}")
        print(f"Montant: de {montant_mini:,.0f} à {montant_maxi:,.0f}")
        print(f"{'='*70}\n")
        
        # Étape 1: Récupérer les PEC éligibles
        df_eligibles = self.recuperer_pec_eligibles(date_debut, date_fin)

        if df_eligibles.empty:
            print("⚠ Aucun PEC éligible trouvé pour la période donnée")
            return pd.DataFrame()

        # DEBUG: Afficher les premières lignes des PEC éligibles
        print("\n[DEBUG] Aperçu des PEC éligibles:")
        print(f"[DEBUG] Colonnes: {df_eligibles.columns.tolist()}")
        print(f"[DEBUG] Premières lignes:")
        print(df_eligibles.head(3))
        print()
        
        # Étape 2: Pour chaque PEC, calculer le montant total et récupérer les infos bénéficiaire
        resultats = []
        total_pec = len(df_eligibles)
        
        for idx, row in df_eligibles.iterrows():
            num_pec = row['num_pec']
            structure = row['structure']
            num_trans = row['num_trans']
            date_debut_execution = row['date_debut_execution']
            id_acte_trans = row['id_acte_trans']

            # Récupérer les IDs pour les structures et le personnel
            id_structure_initiatrice = row.get('id_structure_initiatrice')
            id_structure_propose = row.get('id_structure_propose')
            id_structure_origine_bulletin = row.get('id_structure_origine_bulletin')
            id_ps_initiateur = row.get('id_ps_initiateur')
            id_ps_executant = row.get('id_ps_executant')
            id_type_prestation = row.get('id_type_prest')

            # Récupérer les nouvelles colonnes de date et validation de acte_trans
            date_dmd_acte_trans = row.get('date_dmd_acte_trans')
            date_fin_execution = row.get('date_fin_execution')
            date_accuser_reception = row.get('date_accuser_reception')
            cle_validation = row.get('cle_validation')
            nombre_jour_hospitalisation = row.get('nombre_jour_hospitalisation')

            # Activer le debug pour les 3 premiers PEC
            debug_mode = (idx < 3)

            if not debug_mode:
                print(f"Traitement {idx + 1}/{total_pec}: {num_pec}...", end=" ")

            # Calculer le montant total via SQL_TAMPON
            montant_total_pec = self.calculer_montant_total_pec(num_pec, debug=debug_mode)

            # Récupérer le libellé du type de prestation
            libelle_type_prestation = self.recuperer_libelle_type_prestation(id_type_prestation)

            # Récupérer le libellé de l'état qualificatif
            libelle_etat_qualificatif = self.recuperer_etat_qualificatif(id_acte_trans)

            # Récupérer les infos du bénéficiaire
            info_benef = self.recuperer_info_beneficiaire(num_trans)

            # Récupérer les noms des structures
            structure_initiatrice = self.recuperer_nom_structure(id_structure_initiatrice)
            structure_propose = self.recuperer_nom_structure(id_structure_propose)
            structure_executante = structure  # Déjà récupéré dans la requête initiale
            structure_origine_bulletin = self.recuperer_nom_structure(id_structure_origine_bulletin)

            # Récupérer les noms et téléphones du personnel
            info_ps_initiateur = self.recuperer_nom_personnel(id_ps_initiateur)
            info_ps_executant = self.recuperer_nom_personnel(id_ps_executant)

            ps_initiateur = info_ps_initiateur['nom_complet']
            tel_initiateur = info_ps_initiateur['telephone']
            ps_executant = info_ps_executant['nom_complet']
            tel_executant = info_ps_executant['telephone']

            # Construire la ligne de résultat avec l'ordre des colonnes spécifié :
            # num_pec, montant_total_pec, LIBELLE_TYPE_PRESTATION (après montant_total_pec),
            # libelle_etat_qualificatif,
            # structure_initiatrice, structure_propose, structure_executante, structure_origine_bulletin,
            # ps_initiateur, tel_initiateur (après ps_initiateur),
            # ps_executant, tel_executant (après ps_executant),
            # date_dmd_acte_trans, date_debut_execution, date_fin_execution,
            # date_accuser_reception, cle_validation, nombre_jour_hospitalisation,
            # num_bnf (avant nom_beneficiaire), nom_beneficiaire, prenom_beneficiaire,
            # date_naissance, telephone (après date_naissance), sexe (après date_naissance)
            resultats.append({
                'num_pec': num_pec,
                'montant_total_pec': montant_total_pec,
                'LIBELLE_TYPE_PRESTATION': libelle_type_prestation,
                'libelle_etat_qualificatif': libelle_etat_qualificatif,
                'structure_initiatrice': structure_initiatrice,
                'structure_propose': structure_propose,
                'structure_executante': structure_executante,
                'structure_origine_bulletin': structure_origine_bulletin,
                'ps_initiateur': ps_initiateur,
                'tel_initiateur': tel_initiateur,
                'ps_executant': ps_executant,
                'tel_executant': tel_executant,
                'date_dmd_acte_trans': date_dmd_acte_trans,
                'date_debut_execution': date_debut_execution,
                'date_fin_execution': date_fin_execution,
                'date_accuser_reception': date_accuser_reception,
                'cle_validation': cle_validation,
                'nombre_jour_hospitalisation': nombre_jour_hospitalisation,
                'num_bnf': info_benef['num_bnf'],
                'nom_beneficiaire': info_benef['nom_beneficiaire'],
                'prenom_beneficiaire': info_benef['prenom_beneficiaire'],
                'date_naissance': info_benef['date_naissance'],
                'telephone': info_benef['telephone'],
                'sexe': info_benef['sexe']
            })

            if not debug_mode:
                print(f"✓ Montant: {montant_total_pec:,.0f}")
        
        # Étape 3: Créer le DataFrame final
        df_resultat = pd.DataFrame(resultats)

        # Filtrer pour exclure les lignes avec montant_total_pec = 0
        nb_lignes_avant = len(df_resultat)
        df_resultat = df_resultat[df_resultat['montant_total_pec'] > 0].copy()
        nb_lignes_apres_zero = len(df_resultat)
        nb_lignes_exclues_zero = nb_lignes_avant - nb_lignes_apres_zero

        # Filtrer selon la plage de montant : montant_mini < montant_total_pec < montant_maxi
        df_resultat = df_resultat[
            (df_resultat['montant_total_pec'] > montant_mini) &
            (df_resultat['montant_total_pec'] < montant_maxi)
        ].copy()
        nb_lignes_apres_montant = len(df_resultat)
        nb_lignes_exclues_montant = nb_lignes_apres_zero - nb_lignes_apres_montant

        # Trier par num_pec
        df_resultat = df_resultat.sort_values('num_pec').reset_index(drop=True)

        print(f"\n{'='*70}")
        print(f"✓ État synthétique généré: {nb_lignes_apres_montant} lignes")
        print(f"  ({nb_lignes_exclues_zero} lignes avec montant = 0 exclues)")
        print(f"  ({nb_lignes_exclues_montant} lignes hors plage de montant exclues)")
        print(f"{'='*70}\n")
        
        return df_resultat
    
    def exporter_csv(self, df: pd.DataFrame, fichier_sortie: str):
        """
        Exporte le DataFrame en CSV
        
        Args:
            df: DataFrame à exporter
            fichier_sortie: Chemin du fichier de sortie
        """
        try:
            df.to_csv(fichier_sortie, index=False, encoding='utf-8-sig')
            print(f"✓ Export CSV réussi: {fichier_sortie}")
        except Exception as e:
            print(f"✗ Erreur lors de l'export CSV: {e}")
    
    def exporter_excel(self, df: pd.DataFrame, fichier_sortie: str):
        """
        Exporte le DataFrame en Excel
        
        Args:
            df: DataFrame à exporter
            fichier_sortie: Chemin du fichier de sortie
        """
        try:
            df.to_excel(fichier_sortie, index=False, engine='openpyxl')
            print(f"✓ Export Excel réussi: {fichier_sortie}")
        except Exception as e:
            print(f"✗ Erreur lors de l'export Excel: {e}")
    
    def afficher_apercu(self, df: pd.DataFrame, nb_lignes: int = 10):
        """
        Affiche un aperçu du DataFrame
        
        Args:
            df: DataFrame à afficher
            nb_lignes: Nombre de lignes à afficher
        """
        if df.empty:
            print("⚠ Aucune donnée à afficher")
            return
        
        print(f"\n{'='*70}")
        print(f"APERÇU DES RÉSULTATS (premières {min(nb_lignes, len(df))} lignes)")
        print(f"{'='*70}\n")
        
        # Configuration de l'affichage pandas
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)
        
        print(df.head(nb_lignes).to_string(index=False))
        
        print(f"\n{'='*70}")
        print(f"Total lignes: {len(df)}")
        print(f"Montant total global: {df['montant_total_pec'].sum():,.2f}")
        print(f"{'='*70}\n")


def valider_date(date_str: str) -> bool:
    """
    Valide le format de date YYYY-MM-DD
    
    Args:
        date_str: Chaîne de date à valider
        
    Returns:
        True si le format est valide, False sinon
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def main():
    """Fonction principale"""
    
    # ========================
    # CONFIGURATION
    # ========================
    
    # Configuration de la base de données
    # À ADAPTER selon votre environnement
    config_db = {
        'host': '192.168.10.214',
        'database': 'admi',
        'user': 'user_daci',
        'password': 'Prestige2025',
        'port': 3306
    }
    
    # Paramètres de dates
    # À ADAPTER selon vos besoins
    date_debut = '2025-11-13'
    date_fin = '2025-11-13'

    # Paramètres de filtrage par montant
    # À ADAPTER selon vos besoins
    # montant_mini < montant_total_pec < montant_maxi
    montant_mini = 0        # Montant minimum (exclu)
    montant_maxi = float('inf') # Montant maximum (exclu), float('inf') = pas de limite

    # Fichiers de sortie
    fichier_csv = 'etat_synthetique_pec.csv'
    fichier_excel = 'etat_synthetique_pec.xlsx'
    
    # ========================
    # VALIDATION
    # ========================
    
    if not valider_date(date_debut):
        print(f"✗ Format de date_debut invalide: {date_debut} (attendu: YYYY-MM-DD)")
        sys.exit(1)
    
    if not valider_date(date_fin):
        print(f"✗ Format de date_fin invalide: {date_fin} (attendu: YYYY-MM-DD)")
        sys.exit(1)
    
    if date_debut > date_fin:
        print(f"✗ date_debut ({date_debut}) doit être antérieure à date_fin ({date_fin})")
        sys.exit(1)
    
    # ========================
    # TRAITEMENT
    # ========================
    
    # Créer une instance du générateur
    generateur = GenerateurEtatPEC(config_db)
    
    # Connexion à la base de données
    if not generateur.connecter():
        sys.exit(1)
    
    try:
        # Générer l'état synthétique
        df_resultat = generateur.generer_etat_synthetique(date_debut, date_fin, montant_mini, montant_maxi)
        
        if not df_resultat.empty:
            # Afficher un aperçu
            generateur.afficher_apercu(df_resultat)
            
            # Exporter les résultats
            generateur.exporter_csv(df_resultat, fichier_csv)
            generateur.exporter_excel(df_resultat, fichier_excel)
            
            print("\n✓ Traitement terminé avec succès!")
        else:
            print("\n⚠ Aucun résultat généré")
    
    except Exception as e:
        print(f"\n✗ Erreur lors du traitement: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Déconnexion
        generateur.deconnecter()


if __name__ == "__main__":
    main()
