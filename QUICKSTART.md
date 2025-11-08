# 🚀 Guide de démarrage rapide - FPMsigm | Inspections

Ce guide vous permettra de démarrer l'application en **5 minutes**.

## ⚡ Installation rapide

### 1. Prérequis
- Python 3.8+ installé
- MySQL ou PostgreSQL installé et en cours d'exécution

### 2. Installation

```bash
# 1. Cloner ou télécharger le projet
cd DICT-app

# 2. Créer et activer l'environnement virtuel
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copier le fichier de configuration
cp .env.example .env

# Éditer le fichier .env avec vos paramètres
# Modifier au minimum :
# - DB_NAME=fpm_inspections
# - DB_USER=votre_utilisateur
# - DB_PASSWORD=votre_mot_de_passe
# - SECRET_KEY=generer_une_cle_aleatoire
```

**Générer une clé secrète** :
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Initialiser la base de données

```bash
# Se connecter à MySQL
mysql -u root -p

# Exécuter le script d'initialisation
source init_db.sql
# ou
mysql -u root -p < init_db.sql
```

### 5. Lancer l'application

```bash
python run.py
```

L'application est accessible à : **http://localhost:5000**

---

## 🎯 Première utilisation

### Navigation

1. **Dashboard** (`/`) : Vue d'ensemble et statistiques
2. **Scénarios** (`/scenarios`) : Liste des analyses disponibles
3. **Scénario 1** (`/scenarios/1`) : Recherche des montants exécutés

### Effectuer une analyse

1. Aller sur **Scénarios** → **Scénario 1**
2. Remplir les filtres :
   - Date de début / fin
   - Montants min/max (optionnel)
   - Cocher les regroupements souhaités
3. Cliquer sur **Exécuter la recherche**
4. Consulter les résultats
5. Exporter en CSV, XLSX ou PDF si besoin
6. Enregistrer l'analyse pour traçabilité

---

## 📝 Données de test

Le script `init_db.sql` crée automatiquement :
- 5 structures de santé
- 5 dossiers PEC
- 11 actes médicaux

Vous pouvez immédiatement tester l'application avec ces données.

---

## 🔧 Configuration avancée

### Variables d'environnement principales

```env
# Base de données
DB_TYPE=mysql                    # mysql ou postgresql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=fpm_inspections
DB_USER=root
DB_PASSWORD=votre_mot_de_passe

# Flask
SECRET_KEY=votre_cle_secrete_aleatoire
FLASK_ENV=development            # development ou production
FLASK_DEBUG=True                 # True ou False

# Application
ITEMS_PER_PAGE=50                # Nombre d'items par page
MAX_EXPORT_ROWS=5000             # Limite d'export
```

### Personnalisation du logo

Remplacer le fichier `app/static/img/logo_fpm.png` par votre logo.

Format recommandé : PNG, 200x200px minimum, fond transparent.

---

## 🐛 Résolution de problèmes

### Erreur de connexion à la base de données

**Problème** : `Can't connect to MySQL server`

**Solution** :
1. Vérifier que MySQL est démarré
2. Vérifier les identifiants dans `.env`
3. Tester la connexion : `mysql -u root -p`

### Erreur "ModuleNotFoundError"

**Problème** : `ModuleNotFoundError: No module named 'flask'`

**Solution** :
1. Activer l'environnement virtuel : `venv\Scripts\activate`
2. Installer les dépendances : `pip install -r requirements.txt`

### Port 5000 déjà utilisé

**Problème** : `Address already in use`

**Solution** :
```bash
# Changer le port dans .env
FLASK_PORT=5001

# Ou tuer le processus utilisant le port 5000
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS
lsof -i :5000
kill -9 <PID>
```

### Erreur CSRF token

**Problème** : `The CSRF token is missing`

**Solution** :
1. Vérifier que `SECRET_KEY` est défini dans `.env`
2. Vider le cache du navigateur
3. Redémarrer l'application

---

## 📚 Prochaines étapes

Une fois l'application lancée :

1. ✅ Lire le [README.md](README.md) complet
2. ✅ Adapter les modèles à votre schéma de base de données
3. ✅ Connecter à votre base de données de production (lecture seule recommandé)
4. ✅ Personnaliser les scénarios selon vos besoins
5. ✅ Ajouter l'authentification si nécessaire
6. ✅ Configurer pour la production (Gunicorn, nginx)

---

## 🆘 Besoin d'aide ?

- Documentation complète : [README.md](README.md)
- Structure du projet : Voir section "Ajout d'un nouveau scénario"
- Logs : Consulter `app.log`

---

**Bon démarrage ! 🚀**
