# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## [1.0.0] - 2024-11-05

### Ajouté
- ✨ Application Flask complète avec architecture MVC
- ✨ Dashboard avec statistiques et analyses récentes
- ✨ Scénario 1: Recherche des montants exécutés
  - Filtres: période, montants, regroupements
  - Agrégations par structure, PEC, date
  - Exports CSV, XLSX, PDF
  - Sauvegarde des analyses
- ✨ Système de pagination
- ✨ Messages flash pour feedback utilisateur
- ✨ Templates responsive avec palette FPM (#006b01)
- ✨ Requêtes SQL paramétrées (sécurité)
- ✨ Protection CSRF
- ✨ Logs d'analyse avec traçabilité
- ✨ Documentation complète (README, QUICKSTART)
- ✨ Script d'initialisation de la base de données
- ✨ Script de vérification de l'installation

### Sécurité
- 🔒 Protection contre injection SQL (requêtes paramétrées)
- 🔒 Protection CSRF (Flask-WTF)
- 🔒 Validation côté serveur
- 🔒 Variables d'environnement pour secrets
- 🔒 HTTPOnly cookies

### Infrastructure
- 🏗️ Architecture MVC claire
- 🏗️ Séparation Models / Services / Controllers
- 🏗️ Templates Jinja2 modulaires
- 🏗️ CSS pur sans framework
- 🏗️ Blueprints Flask pour modularité

### Documentation
- 📚 README.md complet
- 📚 QUICKSTART.md pour démarrage rapide
- 📚 Commentaires dans le code
- 📚 init_db.sql avec schéma complet
- 📚 .env.example pour configuration

## [Futur]

### À venir
- [ ] Scénario 2: Détection d'anomalies
- [ ] Scénario 3: Analyse comparative
- [ ] Scénario 4: Suivi des structures
- [ ] Authentification utilisateur
- [ ] Gestion des rôles (RBAC)
- [ ] API REST
- [ ] Tests unitaires
- [ ] Tests d'intégration
- [ ] Déploiement Docker
- [ ] CI/CD

---

[1.0.0]: https://github.com/fpm/dict-app/releases/tag/v1.0.0
