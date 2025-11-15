"""Test du comptage des PEC du jour"""
from app import create_app
from app.models.scenario2 import Scenario2Model

app = create_app('development')

with app.app_context():
    print("\n=== Test du comptage des PEC du jour ===\n")

    try:
        count = Scenario2Model.count_pec_today()
        print(f"Nombre de PEC aujourd'hui: {count}")
        print(f"Type: {type(count)}")
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

    # Test de la requête directe
    print("\n=== Test requete directe ===\n")
    try:
        query = """
        SELECT COUNT(DISTINCT num_pec) as count_pec
        FROM acte_trans
        WHERE date_debut_execution = CURDATE()
        """
        result = Scenario2Model.execute_query(query, {})
        print(f"Resultat brut: {result}")
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

    # Vérifier quelles dates existent
    print("\n=== Verification des dates dans acte_trans ===\n")
    try:
        query2 = """
        SELECT
            DATE(date_debut_execution) as date_exec,
            COUNT(DISTINCT num_pec) as count_pec
        FROM acte_trans
        WHERE date_debut_execution IS NOT NULL
        GROUP BY DATE(date_debut_execution)
        ORDER BY date_exec DESC
        LIMIT 10
        """
        result2 = Scenario2Model.execute_query(query2, {})
        print("Dates recentes avec nombre de PEC:")
        for r in result2:
            print(f"  {r['date_exec']}: {r['count_pec']} PEC")
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
