"""
Script pour initialiser une base de données SQLite
Alternative rapide à MySQL pour les tests
"""
import sqlite3
from datetime import datetime, timedelta

def init_sqlite_db(db_path='fpm_inspections.db'):
    """Initialise la base de données SQLite"""

    print("=" * 60)
    print("Initialisation de la base de données SQLite")
    print("=" * 60)
    print()

    # Connexion
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Table analysis_log
    print("✓ Création de la table analysis_log...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_utilisateur TEXT NOT NULL,
            intitule TEXT NOT NULL,
            motif TEXT,
            scenario_id INTEGER NOT NULL,
            parametres TEXT,
            metriques TEXT,
            date_analyse DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table structure_sante
    print("✓ Création de la table structure_sante...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS structure_sante (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            nom_structure TEXT NOT NULL,
            type_structure TEXT,
            region TEXT,
            ville TEXT,
            actif INTEGER DEFAULT 1,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table pec
    print("✓ Création de la table pec...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pec (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_pec TEXT UNIQUE NOT NULL,
            adherent_id INTEGER,
            date_ouverture DATE,
            date_cloture DATE,
            statut TEXT DEFAULT 'OUVERT',
            montant_total REAL DEFAULT 0
        )
    """)

    # Table acte_trans
    print("✓ Création de la table acte_trans...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acte_trans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pec_id INTEGER NOT NULL,
            structure_id INTEGER NOT NULL,
            date_execution DATE NOT NULL,
            code_acte TEXT,
            libelle_acte TEXT,
            montant_demande REAL,
            montant_execute REAL NOT NULL,
            quantite INTEGER DEFAULT 1,
            statut TEXT DEFAULT 'VALIDE',
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pec_id) REFERENCES pec(id) ON DELETE CASCADE,
            FOREIGN KEY (structure_id) REFERENCES structure_sante(id) ON DELETE RESTRICT
        )
    """)

    # Insertion des données de test
    print("✓ Insertion des structures de santé...")
    structures = [
        ('STRUCT001', 'Hôpital Central de Cotonou', 'Hôpital', 'Littoral', 'Cotonou'),
        ('STRUCT002', 'Clinique Saint-Luc', 'Clinique', 'Littoral', 'Cotonou'),
        ('STRUCT003', 'Centre de Santé de Godomey', 'Centre de santé', 'Atlantique', 'Godomey'),
        ('STRUCT004', 'Polyclinique les Cocotiers', 'Polyclinique', 'Littoral', 'Cotonou'),
        ('STRUCT005', 'Hôpital de Zone de Parakou', 'Hôpital', 'Borgou', 'Parakou')
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO structure_sante (code, nom_structure, type_structure, region, ville)
        VALUES (?, ?, ?, ?, ?)
    """, structures)

    print("✓ Insertion des PEC...")
    today = datetime.now()
    pecs = [
        ('PEC-2024-001', 1001, (today - timedelta(days=100)).strftime('%Y-%m-%d'), 'CLOS'),
        ('PEC-2024-002', 1002, (today - timedelta(days=80)).strftime('%Y-%m-%d'), 'CLOS'),
        ('PEC-2024-003', 1003, (today - timedelta(days=60)).strftime('%Y-%m-%d'), 'OUVERT'),
        ('PEC-2024-004', 1004, (today - timedelta(days=40)).strftime('%Y-%m-%d'), 'OUVERT'),
        ('PEC-2024-005', 1005, (today - timedelta(days=20)).strftime('%Y-%m-%d'), 'OUVERT')
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO pec (num_pec, adherent_id, date_ouverture, statut)
        VALUES (?, ?, ?, ?)
    """, pecs)

    print("✓ Insertion des actes...")
    actes = [
        # PEC-2024-001
        (1, 1, (today - timedelta(days=99)).strftime('%Y-%m-%d'), 'CONS001', 'Consultation générale', 5000, 5000, 1),
        (1, 1, (today - timedelta(days=99)).strftime('%Y-%m-%d'), 'EXAM001', 'Examen radiologique', 15000, 15000, 1),
        (1, 2, (today - timedelta(days=97)).strftime('%Y-%m-%d'), 'LABO001', 'Analyse sanguine', 8000, 8000, 1),

        # PEC-2024-002
        (2, 3, (today - timedelta(days=79)).strftime('%Y-%m-%d'), 'CONS001', 'Consultation générale', 5000, 5000, 1),
        (2, 3, (today - timedelta(days=79)).strftime('%Y-%m-%d'), 'MED001', 'Médicaments', 25000, 22000, 1),

        # PEC-2024-003
        (3, 4, (today - timedelta(days=59)).strftime('%Y-%m-%d'), 'CONS002', 'Consultation spécialisée', 10000, 10000, 1),
        (3, 4, (today - timedelta(days=58)).strftime('%Y-%m-%d'), 'CHIR001', 'Intervention chirurgicale mineure', 150000, 150000, 1),

        # PEC-2024-004
        (4, 5, (today - timedelta(days=39)).strftime('%Y-%m-%d'), 'HOSP001', 'Hospitalisation', 50000, 50000, 3),
        (4, 5, (today - timedelta(days=38)).strftime('%Y-%m-%d'), 'EXAM002', 'Scanner', 45000, 45000, 1),

        # PEC-2024-005
        (5, 1, (today - timedelta(days=19)).strftime('%Y-%m-%d'), 'CONS001', 'Consultation générale', 5000, 5000, 1),
        (5, 2, (today - timedelta(days=18)).strftime('%Y-%m-%d'), 'LABO002', 'Test COVID-19', 12000, 12000, 1)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO acte_trans
        (pec_id, structure_id, date_execution, code_acte, libelle_acte, montant_demande, montant_execute, quantite)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, actes)

    # Commit et fermeture
    conn.commit()
    conn.close()

    print()
    print("=" * 60)
    print("✅ Base de données SQLite initialisée avec succès!")
    print(f"📁 Fichier: {db_path}")
    print("=" * 60)
    print()
    print("Vous pouvez maintenant lancer l'application:")
    print("  python run.py")
    print()

if __name__ == '__main__':
    init_sqlite_db()
