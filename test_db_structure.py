"""Script pour tester la structure de la base de données MariaDB"""
import mariadb
import sys

try:
    # Connexion à MariaDB
    conn = mariadb.connect(
        user="user_daci",
        password="Prestige2025",
        host="192.168.10.214",
        port=3306,
        database="admi"
    )

    cursor = conn.cursor()

    # Liste des tables à vérifier
    tables = [
        'acte_trans',
        'list_acte_acte_trans',
        'list_rub_hosp_acte_trans',
        'structure',
        'transaction',
        'type_transactions'
    ]

    for table in tables:
        print(f"\n{'='*60}")
        print(f"Structure de la table: {table}")
        print('='*60)

        cursor.execute(f"DESCRIBE {table}")

        for (field, type, null, key, default, extra) in cursor:
            print(f"{field:30} {type:20} {null:5} {key:5}")

    # Test de requête simple
    print(f"\n{'='*60}")
    print("Test de requête simple sur acte_trans")
    print('='*60)

    cursor.execute("""
        SELECT COUNT(*) as total
        FROM acte_trans
    """)

    result = cursor.fetchone()
    print(f"Nombre total d'enregistrements dans acte_trans: {result[0]}")

    print(f"\n{'='*60}")
    print("Test de requête simple sur list_acte_acte_trans")
    print('='*60)

    cursor.execute("""
        SELECT COUNT(*) as total
        FROM list_acte_acte_trans
    """)

    result = cursor.fetchone()
    print(f"Nombre total d'enregistrements dans list_acte_acte_trans: {result[0]}")

    print(f"\n{'='*60}")
    print("Test de requête simple sur list_rub_hosp_acte_trans")
    print('='*60)

    cursor.execute("""
        SELECT COUNT(*) as total
        FROM list_rub_hosp_acte_trans
    """)

    result = cursor.fetchone()
    print(f"Nombre total d'enregistrements dans list_rub_hosp_acte_trans: {result[0]}")

    cursor.close()
    conn.close()

    print("\n✓ Connexion et tests réussis!")

except mariadb.Error as e:
    print(f"Erreur MariaDB: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Erreur: {e}")
    sys.exit(1)
