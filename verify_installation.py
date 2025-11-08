"""
Script de vérification de l'installation
Exécutez ce script pour vérifier que tout est correctement configuré
"""
import sys
import os
from pathlib import Path

def check_python_version():
    """Vérifie la version de Python"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Version 3.8+ requise")
        return False

def check_dependencies():
    """Vérifie les dépendances Python"""
    required_packages = [
        'flask',
        'sqlalchemy',
        'pymysql',
        'flask_wtf',
        'dotenv',
        'openpyxl',
        'reportlab'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} - OK")
        except ImportError:
            print(f"✗ {package} - MANQUANT")
            missing.append(package)

    if missing:
        print(f"\n⚠ Packages manquants: {', '.join(missing)}")
        print("Exécutez: pip install -r requirements.txt")
        return False
    return True

def check_env_file():
    """Vérifie la présence du fichier .env"""
    if Path('.env').exists():
        print("✓ Fichier .env - OK")
        return True
    else:
        print("✗ Fichier .env - MANQUANT")
        print("Copiez .env.example vers .env et configurez-le")
        return False

def check_structure():
    """Vérifie la structure des dossiers"""
    required_dirs = [
        'app',
        'app/models',
        'app/services',
        'app/controllers',
        'app/templates',
        'app/static',
        'app/static/css',
        'app/static/img'
    ]

    all_ok = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✓ {dir_path}/ - OK")
        else:
            print(f"✗ {dir_path}/ - MANQUANT")
            all_ok = False

    return all_ok

def check_database_config():
    """Vérifie la configuration de la base de données"""
    try:
        from dotenv import load_dotenv
        load_dotenv()

        required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'SECRET_KEY']
        missing = []

        for var in required_vars:
            value = os.getenv(var)
            if value:
                # Masquer les valeurs sensibles
                if var in ['DB_PASSWORD', 'SECRET_KEY']:
                    display = '***'
                else:
                    display = value
                print(f"✓ {var} = {display}")
            else:
                print(f"✗ {var} - NON DÉFINI")
                missing.append(var)

        if missing:
            print(f"\n⚠ Variables manquantes dans .env: {', '.join(missing)}")
            return False
        return True

    except Exception as e:
        print(f"✗ Erreur lors de la vérification: {e}")
        return False

def check_database_connection():
    """Test de connexion à la base de données"""
    try:
        from dotenv import load_dotenv
        from sqlalchemy import create_engine
        load_dotenv()

        db_type = os.getenv('DB_TYPE', 'mysql')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT', '3306')
        db_name = os.getenv('DB_NAME')

        if db_type == 'mysql':
            uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        elif db_type == 'postgresql':
            uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            print(f"✗ Type de base de données non supporté: {db_type}")
            return False

        engine = create_engine(uri)
        connection = engine.connect()
        connection.close()

        print(f"✓ Connexion à la base de données - OK")
        return True

    except Exception as e:
        print(f"✗ Connexion à la base de données - ÉCHEC")
        print(f"  Erreur: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("=" * 60)
    print("FPMsigm | Inspections - Vérification de l'installation")
    print("=" * 60)
    print()

    checks = [
        ("Version Python", check_python_version),
        ("Dépendances Python", check_dependencies),
        ("Structure des dossiers", check_structure),
        ("Fichier .env", check_env_file),
        ("Configuration base de données", check_database_config),
        ("Connexion base de données", check_database_connection)
    ]

    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"✗ Erreur: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    if all(results):
        print("✓ INSTALLATION COMPLÈTE - Vous pouvez lancer l'application!")
        print("\nExécutez: python run.py")
    else:
        print("✗ INSTALLATION INCOMPLÈTE - Veuillez corriger les erreurs")
        print("\nConsultez QUICKSTART.md pour plus d'aide")
    print("=" * 60)

if __name__ == "__main__":
    main()
