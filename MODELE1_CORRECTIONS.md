# Corrections du Modèle 1 - Montants Exécutés

## 📋 Résumé des modifications

Le modèle 1 "Montants exécutés" a été **corrigé et amélioré** pour afficher des données détaillées par PEC au lieu d'agrégations, en cohérence avec le fichier Excel de référence généré par `admi_claude.py`.

### 🆕 Dernière correction (2025-11-13 20:15)
**Problème résolu** : Erreur SQL avec syntaxe `WITH` (CTE) causant des erreurs d'exécution

**Solution appliquée** : Réécriture complète de la requête SQL en utilisant des sous-requêtes scalaires au lieu de CTE, ce qui est plus compatible avec MariaDB et évite les problèmes de jointures multiples.

## 🎯 Objectifs atteints

### 1. ✅ Affichage détaillé par PEC
- **Avant** : Le modèle affichait des agrégations (regroupements par structure/PEC/date)
- **Après** : Le modèle affiche maintenant une ligne par PEC avec toutes les informations détaillées

### 2. ✅ Colonnes complètes (24 colonnes + Facture)
Le tableau affiche maintenant toutes les colonnes du fichier Excel de référence :

| # | Colonne | Description |
|---|---------|-------------|
| 1 | num_pec | Numéro de PEC |
| 2 | montant_total_pec | Montant total exécuté (calculé depuis SQL_TAMPON) |
| 3 | LIBELLE_TYPE_PRESTATION | Type de prestation |
| 4 | libelle_etat_qualificatif | État qualificatif du PEC |
| 5 | structure_initiatrice | Structure ayant initié le PEC |
| 6 | structure_propose | Structure proposée |
| 7 | structure_executante | Structure exécutant les soins |
| 8 | structure_origine_bulletin | Structure origine du bulletin |
| 9 | ps_initiateur | Personnel soignant initiateur |
| 10 | tel_initiateur | Téléphone du PS initiateur |
| 11 | ps_executant | Personnel soignant exécutant |
| 12 | tel_executant | Téléphone du PS exécutant |
| 13 | date_dmd_acte_trans | Date de demande de l'acte |
| 14 | date_debut_execution | Date de début d'exécution |
| 15 | date_fin_execution | Date de fin d'exécution |
| 16 | date_accuser_reception | Date d'accusé de réception |
| 17 | cle_validation | Clé de validation |
| 18 | nombre_jour_hospitalisation | Nombre de jours d'hospitalisation |
| 19 | num_bnf | Numéro du bénéficiaire |
| 20 | nom_beneficiaire | Nom du bénéficiaire |
| 21 | prenom_beneficiaire | Prénom du bénéficiaire |
| 22 | date_naissance | Date de naissance |
| 23 | telephone | Téléphone du bénéficiaire |
| 24 | sexe | Sexe du bénéficiaire |
| 25 | **Facture** | 🔍 Bouton pour voir les détails |

### 3. ✅ Calcul correct des montants
Le calcul des montants utilise maintenant la logique de `admi_claude.py` :
- Agrégation des montants depuis `list_acte_acte_trans` (montant × quantité)
- Ajout des montants depuis `list_rub_hosp_acte_trans` (montant × quantité)
- Exclusion automatique des PEC avec montant = 0

### 4. ✅ Colonne "Facture" avec détails
- Bouton "🔍 Détails" sur chaque ligne
- Clic sur le bouton → Modal affichant les détails de la facture :
  - Nombre de lignes d'actes
  - Montant total
  - Tableau détaillé des actes (structure, libellé, date, quantité, montant)

### 5. ✅ Exports dans tous les formats
Les exports ont été mis à jour pour inclure toutes les nouvelles colonnes :

- **📗 Excel (.xlsx)** : Toutes les colonnes avec formatage et styles
- **📘 Word (.docx)** : Document formaté (colonnes principales)
- **📄 CSV** : Fichier CSV avec toutes les colonnes
- **📕 PDF** : Document PDF (colonnes principales pour raison d'espace)

## 🔧 Fichiers modifiés

### 1. Modèle de données
**Fichier** : `app/models/acte.py`

**Nouvelles méthodes** :
```python
ActeModel.get_detailed_pec_data()  # Récupère les données détaillées par PEC
ActeModel.count_detailed_pec()     # Compte le nombre total de PEC
```

**Requête SQL** : Utilise des CTE (Common Table Expressions) pour :
1. Récupérer les PEC éligibles avec toutes leurs métadonnées
2. Calculer les montants totaux depuis `list_acte_acte_trans` + `list_rub_hosp_acte_trans`
3. Joindre toutes les tables nécessaires (structures, personnel, transaction, type_prestation, état_qualificatif)

### 2. Service d'analytics
**Fichier** : `app/services/analytics_service.py`

**Modifications** :
- `analyze_scenario1()` : Utilise maintenant `get_detailed_pec_data()` au lieu de `get_aggregated_data()`
- `_calculate_metrics_detailed()` : Nouvelle méthode pour calculer les métriques (total PEC, montant total, montant moyen)

### 3. Contrôleur
**Fichier** : `app/controllers/scenario1_controller.py`

**Modifications** :
- Simplification du formulaire (suppression des options de regroupement)
- Nouvelle route API : `/api/facture-details/<num_pec>` pour récupérer les détails d'une facture
- Requête SQL_TAMPON intégrée (UNION entre actes et rubriques hospitalisation)

### 4. Template de résultats
**Fichier** : `app/templates/scenario1/results.html`

**Modifications** :
- Tableau élargi avec 25 colonnes (scroll horizontal automatique)
- Métriques mises à jour (Total PEC au lieu de Total actes)
- Modal JavaScript pour afficher les détails de facture
- Styles CSS pour le modal

### 5. Service d'export
**Fichier** : `app/services/export_service.py`

**Modifications** :
- `prepare_export_data()` : Mise à jour avec les 24 colonnes du modèle détaillé
- Labels des colonnes en français

### 6. Contrôleur d'exports
**Fichier** : `app/controllers/exports_controller.py`

**Modifications** :
- Ajout de l'export Word pour le scénario 1

## 📊 Comparaison Avant/Après

### Avant (Agrégations)
```
Structure Exécutante | Numéro PEC | Date Exécution | Nb Actes | Montant Total
-------------------------------------------------------------------------------
Clinique A          | 25M000875  | 2025-11-13     | 5        | 50,000 FCFA
```

### Après (Détails complets)
```
Numéro PEC | Montant | Type | État | Structure Init | ... | Nom Bénéf | Prénom | Facture
------------------------------------------------------------------------------------------
25M000875  | 10,000  | AMBU | EXEC | CMA 1er BAT   | ... | ZAGO      | TIPKA  | 🔍 Détails
```

## 🚀 Utilisation

### 1. Accéder au modèle 1
1. Lancez l'application Flask : `python run.py`
2. Accédez à http://localhost:5000
3. Cliquez sur "Modèle 1 - Montants exécutés"

### 2. Filtrer les données
- **Période** : Sélectionnez date de début et date de fin
- **Montants** : (Optionnel) Définissez montant min/max
- Cliquez sur "Rechercher"

### 3. Consulter les résultats
- Le tableau affiche toutes les colonnes
- Scroll horizontal disponible si nécessaire
- Clic sur "🔍 Détails" pour voir le détail des actes

### 4. Exporter les données
Cliquez sur le bouton d'export souhaité :
- **📗 Excel** : Fichier complet avec toutes les colonnes
- **📘 Word** : Document formaté
- **📄 CSV** : Pour import dans d'autres outils
- **📕 PDF** : Document imprimable

## 🔍 Détails techniques

### Calcul des montants (Nouvelle approche - Sous-requêtes scalaires)
```sql
SELECT DISTINCT
    at.num_pec,
    -- Calcul montant via sous-requêtes scalaires
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
    -- ... autres colonnes
FROM acte_trans at
LEFT JOIN structure s_exec ON s_exec.id_structure = at.id_structure_executante
-- ... autres jointures
WHERE DATE(at.date_debut_execution) BETWEEN :date_debut AND :date_fin
  AND at.deleted_at IS NULL
HAVING montant_total_pec > 0
```

**Avantages de cette approche** :
- ✅ Évite les problèmes de CTE non supportées ou mal optimisées
- ✅ Pas de problème de cardinalité avec les jointures multiples
- ✅ Plus performant sur MariaDB pour ce cas d'usage
- ✅ Filtrage `HAVING` sur montant calculé directement

### API Détails de facture
**Endpoint** : `GET /scenario1/api/facture-details/<num_pec>`

**Réponse JSON** :
```json
{
  "num_pec": "25M000875/2281D",
  "nb_lignes": 5,
  "montant_total": 10000,
  "lignes": [
    {
      "nom_structure": "CLINIQUE DIVINES GRACES",
      "libelle_acte": "Consultation",
      "date_execution": "2025-11-13 14:37:52",
      "nb": 1,
      "montant": 10000
    }
  ]
}
```

## ✨ Améliorations futures possibles

1. **Filtres avancés** :
   - Filtrage par structure
   - Filtrage par type de prestation
   - Filtrage par état qualificatif

2. **Statistiques supplémentaires** :
   - Répartition par structure
   - Évolution temporelle
   - Graphiques

3. **Performance** :
   - Mise en cache des requêtes fréquentes
   - Index sur les colonnes de filtrage

4. **Export** :
   - Template Excel personnalisé
   - Graphiques dans les exports
   - Envoi par email

## 📝 Notes importantes

- Les PEC avec montant = 0 sont automatiquement exclus
- Le calcul des montants est identique à `admi_claude.py`
- Les données sont filtrées sur `date_debut_execution`
- La pagination est activée (50 résultats par page par défaut)

---

**Date de modification** : 2025-11-13
**Version** : 2.0
**Auteur** : Claude Code
