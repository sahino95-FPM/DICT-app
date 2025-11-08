# FPMsigm | Inspections - Application d'analyse DICT

Application web Python/Flask pour le **Département d'Inspection et de Contrôle Technique (DICT)** du FPM Santé.

![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-lightgrey.svg)

## 📋 Table des matières

- [Description](#description)
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Scénarios d'analyse](#scénarios-danalyse)
- [Ajout d'un nouveau scénario](#ajout-dun-nouveau-scénario)
- [Structure du projet](#structure-du-projet)
- [Technologies utilisées](#technologies-utilisées)
- [Sécurité](#sécurité)
- [Contribuer](#contribuer)

## 🎯 Description

Cette application permet d'effectuer des **recherches avancées et exports** sur les données médicales du FPM pour le Département d'Inspection et de Contrôle Technique. Elle offre une interface intuitive pour analyser les prestations médicales, détecter des anomalies et générer des rapports.

## ✨ Fonctionnalités

- **Dashboard** avec statistiques et analyses récentes
- **Scénarios d'analyse** multiples (extensible)
- **Filtres dynamiques** : dates, montants, structures, dossiers
- **Agrégations** : regroupement par structure, PEC, date
- **Exports** : CSV, XLSX, PDF avec logo FPM
- **Historique** : sauvegarde et traçabilité des analyses
- **Interface responsive** avec palette FPM (vert #006b01)
- **Requêtes SQL paramétrées** (sécurité anti-injection)
- **Pagination** des résultats
- **Messages flash** pour feedback utilisateur

## 🏗️ Architecture

L'application suit le pattern **MVC (Model-View-Controller)** avec une architecture en couches :

```
┌─────────────────────────────────────┐
│          TEMPLATES (Views)          │
│  Jinja2 - HTML - CSS                │
└─────────────────────────────────────┘
                 ↕
┌─────────────────────────────────────┐
│      CONTROLLERS (Routes)           │
│  Flask Blueprints                   │
└─────────────────────────────────────┘
                 ↕
┌─────────────────────────────────────┐
│         SERVICES (Logique)          │
│  Analytics - Export                 │
└─────────────────────────────────────┘
                 ↕
┌─────────────────────────────────────┐
│      MODELS (Accès données)         │
│  SQLAlchemy - Requêtes paramétrées  │
└─────────────────────────────────────┘
                 ↕
┌─────────────────────────────────────┐
│         BASE DE DONNÉES             │
│  MySQL / PostgreSQL                 │
└─────────────────────────────────────┘
```

## 📦 Installation

### Prérequis

- Python 3.8 ou supérieur
- MySQL 8.0+ ou PostgreSQL 12+
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner le dépôt** (ou télécharger le code)

```bash
git clone <url-du-depot>
cd DICT-app
```

2. **Créer un environnement virtuel**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

3. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

4. **Configurer les variables d'environnement**

Copier le fichier `.env.example` vers `.env` et modifier les valeurs :

```bash
cp .env.example .env
```

Éditer `.env` avec vos paramètres :

```env
# Base de données
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=fpm_inspections
DB_USER=votre_utilisateur
DB_PASSWORD=votre_mot_de_passe

# Flask
SECRET_KEY=votre_cle_secrete_tres_longue_et_aleatoire
FLASK_ENV=development
FLASK_DEBUG=True
```

5. **Créer la base de données**

Créer la base de données et les tables nécessaires :

```sql
-- Exemple pour MySQL
CREATE DATABASE fpm_inspections CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Tables nécessaires (à adapter selon votre schéma)
USE fpm_inspections;

-- Table pour les logs d'analyse
CREATE TABLE analysis_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom_utilisateur VARCHAR(100) NOT NULL,
    intitule VARCHAR(255) NOT NULL,
    motif TEXT,
    scenario_id INT NOT NULL,
    parametres JSON,
    metriques JSON,
    date_analyse DATETIME NOT NULL,
    INDEX idx_date (date_analyse),
    INDEX idx_scenario (scenario_id)
);

-- Autres tables selon votre schéma existant
-- (acte_trans, structure_sante, pec, etc.)
```

## ⚙️ Configuration

### Variables d'environnement

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `DB_TYPE` | Type de base de données (`mysql` ou `postgresql`) | `mysql` |
| `DB_HOST` | Hôte de la base de données | `localhost` |
| `DB_PORT` | Port de la base de données | `3306` |
| `DB_NAME` | Nom de la base de données | `fpm_inspections` |
| `DB_USER` | Utilisateur de la base de données | - |
| `DB_PASSWORD` | Mot de passe de la base de données | - |
| `SECRET_KEY` | Clé secrète Flask (CSRF, sessions) | - |
| `FLASK_ENV` | Environnement (`development` ou `production`) | `development` |
| `FLASK_DEBUG` | Mode debug | `True` |
| `ITEMS_PER_PAGE` | Nombre d'éléments par page | `50` |
| `MAX_EXPORT_ROWS` | Nombre max de lignes exportées | `5000` |

### Logo FPM

Placer votre logo FPM dans :

```
app/static/img/logo_fpm.png
```

Format recommandé : PNG, 200x200px minimum

## 🚀 Utilisation

### Démarrage de l'application

```bash
# Activer l'environnement virtuel
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/macOS

# Lancer l'application
python run.py
```

L'application sera accessible à : **http://localhost:5000**

### Utilisation en production

Pour la production, utiliser un serveur WSGI comme **Gunicorn** :

```bash
# Installer Gunicorn
pip install gunicorn

# Lancer avec Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## 📊 Scénarios d'analyse

### Scénario 1 : Recherche des montants exécutés

**Objectif** : Obtenir la synthèse des actes exécutés (nombre et montant total) regroupés par structure, dossier et/ou période.

**Filtres disponibles** :
- 📅 Période de soins (date début - date fin)
- 💰 Plage de montants (min - max)
- 📊 Regroupement par : structure / PEC / date
- 🧮 Affichage du détail des actes
- 🧑‍💻 Affichage de la requête SQL
- ⏱️ Limitation du nombre de résultats (50-5000)

**Exports** : CSV, XLSX, PDF

**Sauvegarde** : Possibilité d'enregistrer l'analyse avec motif et intitulé

### Scénarios futurs (placeholders)

- **Scénario 2** : Détection d'anomalies (à implémenter)
- **Scénario 3** : Analyse comparative (à implémenter)
- **Scénario 4** : Suivi des structures (à implémenter)

## 🛠️ Ajout d'un nouveau scénario

Pour ajouter un nouveau scénario d'analyse (exemple : Scénario 2) :

### 1. Créer le modèle (si nécessaire)

```python
# app/models/scenario2_model.py
from app.models.base import BaseModel

class Scenario2Model(BaseModel):
    @staticmethod
    def get_data_scenario2(filters):
        query = "SELECT ... WHERE ..."
        return Scenario2Model.execute_query(query, filters)
```

### 2. Créer le service

```python
# app/services/scenario2_service.py
from app.models.scenario2_model import Scenario2Model

class Scenario2Service:
    @staticmethod
    def analyze(filters):
        results = Scenario2Model.get_data_scenario2(filters)
        # Logique d'analyse...
        return results
```

### 3. Créer le contrôleur

```python
# app/controllers/scenario2_controller.py
from flask import Blueprint, render_template, request
from app.services.scenario2_service import Scenario2Service

scenario2_bp = Blueprint('scenario2', __name__)

@scenario2_bp.route('/')
def form():
    return render_template('scenario2/form.html')

@scenario2_bp.route('/results', methods=['POST'])
def results():
    filters = request.form.to_dict()
    results = Scenario2Service.analyze(filters)
    return render_template('scenario2/results.html', results=results)
```

### 4. Créer les templates

```
app/templates/scenario2/
├── form.html
└── results.html
```

### 5. Enregistrer le blueprint

Dans `app/__init__.py`, ajouter :

```python
from app.controllers.scenario2_controller import scenario2_bp
app.register_blueprint(scenario2_bp, url_prefix='/scenarios/2')
```

### 6. Ajouter au registre

Dans `app/controllers/main_controller.py`, modifier la liste `scenarios` :

```python
{
    'id': 2,
    'titre': 'Mon Scénario 2',
    'description': 'Description du scénario 2',
    'route': 'scenario2.form',
    'active': True,
    'icon': 'chart'
}
```

## 📁 Structure du projet

```
DICT-app/
│
├── app/
│   ├── __init__.py              # Factory Flask
│   ├── config.py                # Configuration
│   │
│   ├── models/                  # Accès données
│   │   ├── base.py
│   │   ├── acte.py
│   │   └── analysis_log.py
│   │
│   ├── services/                # Logique métier
│   │   ├── analytics_service.py
│   │   └── export_service.py
│   │
│   ├── controllers/             # Routes Flask
│   │   ├── main_controller.py
│   │   ├── scenario1_controller.py
│   │   └── exports_controller.py
│   │
│   ├── templates/               # Vues Jinja2
│   │   ├── layouts/
│   │   │   └── base.html
│   │   ├── partials/
│   │   │   ├── header.html
│   │   │   ├── sidebar.html
│   │   │   ├── footer.html
│   │   │   ├── messages.html
│   │   │   └── pagination.html
│   │   ├── dashboard.html
│   │   ├── scenarios/
│   │   │   └── index.html
│   │   ├── scenario1/
│   │   │   ├── form.html
│   │   │   └── results.html
│   │   └── errors/
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   └── static/                  # Ressources statiques
│       ├── css/
│       │   └── style.css
│       ├── img/
│       │   └── logo_fpm.png
│       └── js/
│
├── run.py                       # Point d'entrée
├── requirements.txt             # Dépendances
├── .env.example                 # Variables d'environnement (exemple)
├── .env                         # Variables d'environnement (local, ignoré par git)
├── .gitignore                   # Fichiers ignorés par git
└── README.md                    # Ce fichier
```

## 🛡️ Technologies utilisées

- **Backend** : Flask 3.0.0, SQLAlchemy 2.0
- **Base de données** : MySQL 8.0+ / PostgreSQL 12+
- **Frontend** : HTML5, CSS3 (pur, sans framework)
- **Templates** : Jinja2
- **Exports** : openpyxl (XLSX), reportlab (PDF), csv (CSV)
- **Sécurité** : Flask-WTF (CSRF), requêtes paramétrées
- **Environnement** : python-dotenv

## 🔒 Sécurité

### Bonnes pratiques implémentées

✅ **Requêtes SQL paramétrées** - Protection contre l'injection SQL
✅ **CSRF tokens** - Protection contre les attaques CSRF
✅ **Variables d'environnement** - Secrets non versionnés
✅ **Validation serveur** - Tous les inputs sont validés
✅ **Pagination** - Limitation du nombre de résultats
✅ **Logs** - Traçabilité des analyses
✅ **HTTPOnly cookies** - Protection des sessions

### Recommandations pour la production

- [ ] Utiliser HTTPS (certificat SSL/TLS)
- [ ] Configurer `SESSION_COOKIE_SECURE=True`
- [ ] Ajouter un système d'authentification (OAuth2, LDAP, etc.)
- [ ] Implémenter des rôles utilisateurs (RBAC)
- [ ] Configurer des limites de débit (rate limiting)
- [ ] Activer les logs détaillés
- [ ] Mettre en place des sauvegardes régulières
- [ ] Utiliser un reverse proxy (nginx, Apache)

## 🤝 Contribuer

Pour contribuer au projet :

1. Créer une branche pour votre fonctionnalité
2. Implémenter la fonctionnalité avec tests
3. Suivre les conventions de code (PEP 8)
4. Soumettre une pull request avec description détaillée

## 📝 Licence

© 2024 FPM Santé - Tous droits réservés

---

**Contact** : Département d'Inspection et de Contrôle Technique (DICT)
**Version** : 1.0.0
**Dernière mise à jour** : Novembre 2024
