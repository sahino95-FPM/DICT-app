# Guide de contribution

Merci de votre intérêt pour contribuer au projet FPMsigm | Inspections !

## 🤝 Comment contribuer

### Signaler un bug

1. Vérifier que le bug n'a pas déjà été signalé
2. Créer une issue avec :
   - Description claire du problème
   - Étapes pour reproduire
   - Comportement attendu vs comportement réel
   - Environnement (OS, Python version, etc.)
   - Logs d'erreur si disponibles

### Proposer une fonctionnalité

1. Créer une issue "Feature Request"
2. Décrire clairement :
   - Le besoin métier
   - La solution proposée
   - Les alternatives envisagées
   - Impact sur l'existant

### Soumettre du code

1. **Fork** le projet
2. Créer une **branche** pour votre fonctionnalité
   ```bash
   git checkout -b feature/ma-fonctionnalite
   ```
3. **Coder** en suivant les conventions
4. **Tester** votre code
5. **Commiter** avec des messages clairs
   ```bash
   git commit -m "feat: ajout du scénario 2 pour détection d'anomalies"
   ```
6. **Push** vers votre fork
   ```bash
   git push origin feature/ma-fonctionnalite
   ```
7. Créer une **Pull Request**

## 📝 Conventions de code

### Python (PEP 8)

```python
# Imports groupés
from flask import Blueprint, render_template
from app.services import MyService

# Nommage
class MyClass:  # PascalCase pour classes
    pass

def my_function():  # snake_case pour fonctions
    pass

MY_CONSTANT = "value"  # UPPER_CASE pour constantes

# Docstrings
def my_function(param1, param2):
    """
    Description courte de la fonction

    Args:
        param1: Description du paramètre 1
        param2: Description du paramètre 2

    Returns:
        Description du retour
    """
    pass
```

### SQL

- **TOUJOURS** utiliser des requêtes paramétrées
- **JAMAIS** de concaténation de chaînes
- Nommage des tables: `snake_case`
- Nommage des colonnes: `snake_case`
- Indices: `idx_nom_colonne`

```python
# ✓ BON
query = "SELECT * FROM users WHERE id = :user_id"
result = execute_query(query, {'user_id': user_id})

# ✗ MAUVAIS
query = f"SELECT * FROM users WHERE id = {user_id}"  # Injection SQL !
```

### HTML/CSS

- Indentation: 2 espaces
- Classes CSS: `kebab-case`
- IDs: `camelCase`
- Sémantique HTML5

### Git Commits

Format: `type(scope): description`

Types:
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation
- `style`: Formatage (pas de changement de code)
- `refactor`: Refactoring
- `test`: Ajout de tests
- `chore`: Tâches de maintenance

Exemples:
```
feat(scenario2): ajout du scénario de détection d'anomalies
fix(export): correction du format de date dans les exports PDF
docs(readme): mise à jour des instructions d'installation
```

## 🧪 Tests

Avant de soumettre une PR:

1. Vérifier l'installation
   ```bash
   python verify_installation.py
   ```

2. Tester manuellement
   - Lancer l'application
   - Tester toutes les pages modifiées
   - Vérifier les logs d'erreur

3. Tests unitaires (quand disponibles)
   ```bash
   pytest
   ```

## 📋 Checklist PR

- [ ] Le code suit les conventions PEP 8
- [ ] Les requêtes SQL sont paramétrées
- [ ] La documentation est à jour
- [ ] Les tests passent
- [ ] Les commits sont clairs et bien formatés
- [ ] Aucun secret n'est commité
- [ ] Le code est commenté si nécessaire

## 🏗️ Ajout d'un nouveau scénario

Voir la section "Ajout d'un nouveau scénario" dans README.md

En résumé:
1. Créer le modèle (`models/scenarioX_model.py`)
2. Créer le service (`services/scenarioX_service.py`)
3. Créer le contrôleur (`controllers/scenarioX_controller.py`)
4. Créer les templates (`templates/scenarioX/`)
5. Enregistrer le blueprint dans `app/__init__.py`
6. Ajouter au registre dans `main_controller.py`

## 🔒 Sécurité

Si vous découvrez une faille de sécurité:

1. **NE PAS** créer d'issue publique
2. Contacter directement l'équipe
3. Fournir les détails de la faille
4. Attendre la correction avant publication

## 📧 Contact

Pour toute question: contact@fpm-sante.org

---

Merci pour votre contribution ! 🙏
