# Guide de Test - Ajout PHARMACIE au Scénario 2

## ✅ Modifications effectuées

### 1. Modèle (`app/models/scenario2.py`)
- ✅ Ajout du paramètre `include_pharmacie=True` dans `get_consolidated_data()`
- ✅ Ajout de la requête UNION ALL pour `list_pharmacie_acte_trans` avec jointure sur table `pharmacie`
- ✅ Ajout de PHARMACIE dans le calcul du total cumulé par PEC (lignes_total_cte)
- ✅ Ajout du paramètre `include_pharmacie=True` dans `count_consolidated_data()`
- ✅ Ajout de PHARMACIE dans `get_facture_details()` (pour cohérence)

### 2. Service (`app/services/scenario2_service.py`)
- ✅ Passage de `include_pharmacie=True` aux appels de modèle

### 3. Template (`app/templates/scenario2/results.html`)
- ✅ Ajout du badge vert pour source PHARMACIE
- ✅ Ajout des styles CSS `.badge-success` et `.badge-secondary`

## 📋 Structure de données attendue

### Table `list_pharmacie_acte_trans`
```sql
- id_acte_trans (FK vers acte_trans)
- id_pharmacie (FK vers pharmacie)
- date_execution (DATE)
- montant (DECIMAL)
- quantite (INT)
```

### Table `pharmacie`
```sql
- id (PK)
- libelle (VARCHAR) -- Nom du médicament/produit
```

## 🧪 Comment tester

### Étape 1: Configuration de .env

Éditez le fichier `.env` et configurez vos credentials MariaDB:

```env
MARIADB_HOST=votre_host
MARIADB_PORT=3306
MARIADB_NAME=admi
MARIADB_USER=votre_user
MARIADB_PASSWORD=votre_password
```

### Étape 2: Installation des dépendances

```bash
pip install -r requirements.txt
```

### Étape 3: Lancer le test automatique

```bash
python test_pharmacie_scenario2.py
```

**Résultats attendus:**
- ✅ Nombre de lignes: **922**
- ✅ Montant total: **1 857 098 FCFA**
- ✅ Présence de lignes avec source PHARMACIE

### Étape 4: Test via l'application web

```bash
python run.py
```

Puis accédez à: `http://localhost:5000/scenarios/2`

**Paramètres de test:**
- Numéro PEC: (laissez vide ou spécifiez un num_pec)
- Période: 2025-01-01 → 2025-12-31
- Cochez ACTE, RUB (pharmacie toujours inclus)

**Vérifications:**
1. Le tableau affiche des lignes avec badge vert "PHARMACIE"
2. La colonne "Libellé Acte/Rubrique" affiche les noms de médicaments
3. Le total correspond à 1 857 098 FCFA
4. Le compteur affiche 922 lignes

## 🐛 Dépannage

### Erreur: "no such table: list_pharmacie_acte_trans"

La table n'existe pas dans votre base MariaDB. Vérifiez que:
- La base de données `admi` contient bien cette table
- Vous êtes connecté à la bonne base de données

### Erreur: "column id_pharmacie not found"

La structure de la table diffère. Adaptez les noms de colonnes dans:
- `app/models/scenario2.py` lignes 158-185, 413-440, 584-605

### Pas de lignes PHARMACIE dans les résultats

Vérifiez que:
- La table `list_pharmacie_acte_trans` contient des données
- Les dates dans la table correspondent à votre filtre
- La table `pharmacie` contient bien les libellés

## 📊 Exemple de résultat attendu

```
📊 Nombre de lignes: 922

📋 Répartition par source:
   - ACTE: 450 lignes
   - PHARMACIE: 300 lignes
   - RUB: 172 lignes

💰 Montant total: 1 857 098,00 FCFA

✓ PHARMACIE trouvée! (300 lignes)

📦 Exemples de lignes PHARMACIE:
   1. PARACETAMOL 500MG - 2 500 FCFA - Structure: CHU Cotonou
   2. AMOXICILLINE 1G - 8 000 FCFA - Structure: Clinique Saint-Luc
   3. INSULINE RAPIDE - 15 000 FCFA - Structure: Polyclinique les Cocotiers
```

## ✅ Validation finale

Une fois le test réussi, vous devriez voir:
- ✅ 922 lignes au total
- ✅ Montant total de 1 857 098 FCFA
- ✅ Badges verts "PHARMACIE" dans le tableau
- ✅ Libellés de médicaments affichés
- ✅ Page facture affiche aussi les pharmacies

---

**Date**: 8 Novembre 2025
**Auteur**: Claude (modifications Scénario 2)
**Statut**: ✅ Prêt pour test
