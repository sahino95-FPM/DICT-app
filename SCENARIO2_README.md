# Scénario 2 : Analyse consolidée des montants exécutés

## 🎯 Objectif

Obtenir une vue consolidée des montants exécutés, regroupés par **dossier (num_pec)** et **structure exécutante**, avec :
- Le total cumulé par dossier (num_pec)
- L'origine des lignes agrégées (ACTE et/ou RUB)
- Les métadonnées bénéficiaire (numbnf, nomprenom, téléphone, sexe, date_naissance)
- Le type de transaction (libelle_type_trans)
- La date d'exécution

Le résultat est **paginable**, **exportable** (CSV/XLSX/PDF/WORD) et **filtrable** dynamiquement.

---

## 🗄️ Configuration de la base de données

### Connexion MariaDB

Le Scénario 2 utilise une **connexion MariaDB distincte** pour se connecter à la base de données `admi`.

#### Fichier `.env`

Configurez les paramètres de connexion dans le fichier `.env` :

```env
# ======================================================
# Configuration MariaDB pour Scénario 2
# ======================================================

# Hôte du serveur MariaDB
MARIADB_HOST=localhost

# Port du serveur MariaDB (défaut: 3306)
MARIADB_PORT=3306

# Nom de la base de données
MARIADB_NAME=admi

# Utilisateur de la base de données (compte en lecture seule recommandé)
MARIADB_USER=readonly_user

# Mot de passe de l'utilisateur
MARIADB_PASSWORD=votre_mot_de_passe_ici
```

⚠️ **Recommandation** : Utilisez un compte en **lecture seule** pour des raisons de sécurité.

### Dépendances Python

Installez le connecteur MariaDB pour Python :

```bash
pip install mariadb
```

Ou ajoutez à `requirements.txt` :
```
mariadb>=1.1.0
```

---

## 🧱 Structure des données

### Tables utilisées

1. **`acte_trans`** : Table des transactions d'actes
   - `id_acte_trans`
   - `num_pec`
   - `num_trans`
   - `id_structure_executante`

2. **`list_acte_acte_trans`** : Détails des actes
   - `id_acte_trans`
   - `date_execution_acte`
   - `montant_acte`

3. **`list_rub_hosp_acte_trans`** : Rubriques d'hospitalisation
   - `id_acte_trans`
   - `date_execution_acte`
   - `montant`

4. **`structure`** : Informations sur les structures
   - `id_structure`
   - `nom_structure`

5. **`transaction`** : Informations sur les transactions
   - `num_trans`
   - `num_bnf`
   - `nom_prenom`
   - `telephone`
   - `sexe`
   - `date_naissance`
   - `id_type_trans`

6. **`type_transactions`** : Types de transactions
   - `id_type_trans`
   - `libelle_type_trans`

---

## 📋 Fonctionnalités du formulaire

### 1) Filtres de base

| Champ | Type | Description |
|-------|------|-------------|
| **Période de soins** | Deux dates | Filtre `date_execution_acte` (date_debut → date_fin) |
| **Plage de montants** | Deux numériques | Filtre montant des lignes élémentaires (montant_min → montant_max) |

### 2) Source des données

- ☑️ **ACTE** : Inclure les données de `list_acte_acte_trans`
- ☑️ **RUB** : Inclure les données de `list_rub_hosp_acte_trans`

> Au moins une source doit être sélectionnée.

### 3) Filtres bénéficiaire

- **Numéro bénéficiaire** : Recherche LIKE sur `num_bnf`
- **Nom & Prénom** : Recherche LIKE sur `nom_prenom`
- **Numéro PEC** : Recherche LIKE sur `num_pec`

### 4) Structures exécutantes

Sélection multiple de structures via dropdown (maintenez Ctrl/Cmd pour sélectionner plusieurs).

### 5) Colonnes d'affichage

Choisissez les colonnes à afficher :
- ☑️ Informations bénéficiaire
- ☑️ Téléphone
- ☑️ Sexe
- ☑️ Date de naissance
- ☑️ Type de transaction
- ☑️ Nombre de lignes

### 6) Tri des résultats

- **Trier par** : num_pec | nom_structure | date_execution | montant_total | nb_lignes
- **Ordre** : Croissant (ASC) | Décroissant (DESC)

### 7) Options avancées

- 🔒 Masquer les numéros de téléphone (XXXXX1234)
- 🧮 Afficher le détail des lignes
- 🧑‍💻 Afficher la requête SQL générée
- ⏱️ Limiter le nombre de résultats (50 - 50 000)

---

## 📊 Format de sortie

### Colonnes du tableau de résultats

| Colonne | Description |
|---------|-------------|
| **Structure exécutante** | Nom de la structure |
| **Numéro PEC** | Numéro du dossier |
| **Date exécution** | Date d'exécution des soins |
| **Num. bénéficiaire** | Numéro du bénéficiaire |
| **Nom & Prénom** | Identité du bénéficiaire |
| **Téléphone** | Numéro de téléphone |
| **Sexe** | Sexe du bénéficiaire |
| **Date naissance** | Date de naissance |
| **Type transaction** | Libellé du type de transaction |
| **Nb lignes** | Nombre de lignes agrégées |
| **Montant total** | Montant total exécuté (FCFA) |
| **Source(s)** | ACTE, RUB ou ACTE,RUB |
| **Total cumulé PEC** | Total cumulé pour le num_pec (fenêtre) |

---

## 📦 Exports

Le Scénario 2 supporte les formats d'export suivants :

### 1. CSV
- Export brut des données
- Compatible avec Excel, LibreOffice, etc.
- Encodage UTF-8

### 2. XLSX (Excel)
- Formatage professionnel
- En-têtes colorés
- Ajustement automatique des colonnes
- Alignement des chiffres à droite

### 3. PDF
- Logo FPM en en-tête
- Titre du document
- Métadonnées (période, nombre de résultats, montant total)
- Tableau formaté (limité à 100 lignes)
- Pied de page avec date de génération

### 4. WORD (DOCX)
- Logo FPM en en-tête
- Titre du document
- Métadonnées détaillées
- Tableau formaté (limité à 100 lignes)
- Pied de page avec date de génération

---

## 🔐 Sécurité & Conformité

### Variables d'environnement

- Toutes les informations sensibles (mots de passe, hôtes) sont stockées dans `.env`
- Le fichier `.env` **DOIT** être ajouté au `.gitignore`

### Moindre privilège

- Utilisez un compte **en lecture seule** (SELECT uniquement) pour la connexion MariaDB
- Aucune requête d'écriture n'est exécutée

### Prévention injection SQL

- Toutes les requêtes utilisent des **paramètres liés** (`:param_name`)
- Aucune concaténation naïve de chaînes SQL
- Échappement des caractères spéciaux dans les filtres LIKE

### Traces d'accès

- Journalisation des requêtes (IP, user, filtres, horodatage)
- Logs dans `app.log`

### RGPD / Confidentialité

- Option de masquage des numéros de téléphone
- Limitation des exports nominativisés selon les besoins

---

## ⚙️ Performance & Indexation

### Index recommandés sur MariaDB

Pour améliorer les performances des requêtes, créez les index suivants :

```sql
-- Index sur acte_trans
CREATE INDEX idx_acte_trans_struct_pec
ON acte_trans(id_structure_executante, num_pec, num_trans);

-- Index sur list_acte_acte_trans
CREATE INDEX idx_list_acte_date_montant
ON list_acte_acte_trans(id_acte_trans, date_execution_acte, montant_acte);

-- Index sur list_rub_hosp_acte_trans
CREATE INDEX idx_list_rub_date_montant
ON list_rub_hosp_acte_trans(id_acte_trans, date_execution_acte, montant);

-- Index sur transaction
CREATE INDEX idx_transaction_num_bnf
ON `transaction`(num_trans, num_bnf, id_type_trans);

-- Index sur type_transactions
CREATE INDEX idx_type_trans
ON type_transactions(id_type_trans);
```

### Bonnes pratiques

- Préférez les filtres **sargables** (bornage dates, montants)
- Évitez `LIKE '%...%'` sur très grands volumes
- Utilisez la pagination pour limiter les résultats
- Limitez la période de recherche (max 3 ans recommandé)

---

## 🧪 Tests

### Test de connexion

Pour tester la connexion à MariaDB :

```bash
python -c "from app import create_app; app = create_app(); print('✓ Connexion MariaDB OK')"
```

### Test des requêtes

Lancez l'application et accédez au formulaire :
```
http://localhost:5000/scenarios/2
```

Testez avec des données de test :
- **Période** : 2025-01-01 → 2025-12-31
- **Montants** : 5 000 → 25 000
- **Sources** : ACTE, RUB

---

## 📝 Notes de mise en œuvre

### Architecture

```
app/
├── models/
│   └── scenario2.py              # Modèle de données (requêtes SQL)
├── services/
│   └── scenario2_service.py      # Service d'analyse
├── controllers/
│   ├── scenario2_controller.py   # Contrôleur des routes
│   └── exports_controller.py     # Exports (mis à jour)
├── templates/
│   └── scenario2/
│       ├── form.html             # Formulaire de recherche
│       └── results.html          # Affichage des résultats
└── __init__.py                   # Initialisation (2 connexions DB)
```

### Mapping des champs

Les champs du formulaire sont mappés vers les paramètres SQL :

| Formulaire | SQL |
|------------|-----|
| `date_debut` | `:date_debut` dans `WHERE date_execution_acte BETWEEN` |
| `date_fin` | `:date_fin` |
| `montant_min` | `:montant_min` dans `WHERE montant BETWEEN` |
| `num_bnf` | `:num_bnf` dans `WHERE num_bnf LIKE` |

### Gestion des time-zones

- Les dates sont au format **ISO 8601** (YYYY-MM-DD)
- Les dates/heures de génération utilisent le fuseau horaire du serveur

---

## 🆘 Dépannage

### Erreur : "Connexion MariaDB non disponible"

**Cause** : Les paramètres de connexion dans `.env` sont incorrects ou le serveur MariaDB est inaccessible.

**Solution** :
1. Vérifiez les paramètres dans `.env` :
   - `MARIADB_HOST`
   - `MARIADB_PORT`
   - `MARIADB_USER`
   - `MARIADB_PASSWORD`
   - `MARIADB_NAME`

2. Testez la connexion manuellement :
   ```bash
   mysql -h <MARIADB_HOST> -P <MARIADB_PORT> -u <MARIADB_USER> -p<MARIADB_PASSWORD> <MARIADB_NAME>
   ```

3. Vérifiez que le pare-feu autorise les connexions sur le port 3306

### Erreur : "no such table: acte_trans"

**Cause** : La requête est exécutée sur la mauvaise base de données.

**Solution** : Assurez-vous que le modèle `Scenario2Model` utilise `mariadb_session` et non `db_session`.

### Requêtes lentes

**Solutions** :
1. Créez les index recommandés (voir section Performance)
2. Réduisez la période de recherche
3. Augmentez les valeurs de `montant_min` et `montant_max`
4. Limitez le nombre de résultats

---

## 🚀 Prochaines étapes

- [ ] Ajouter un cache pour les requêtes fréquentes
- [ ] Implémenter le drill-down (détail des lignes par groupe)
- [ ] Ajouter des graphiques de visualisation
- [ ] Export incrémental pour très gros volumes
- [ ] Audit trail détaillé des exports

---

## 📞 Support

Pour toute question ou problème, consultez :
- La documentation Flask : https://flask.palletsprojects.com/
- La documentation SQLAlchemy : https://www.sqlalchemy.org/
- La documentation MariaDB : https://mariadb.com/kb/

---

**Généré pour le projet DICT-app - Département d'Inspection et de Contrôle Technique**
