"""Script pour tester la requête du scénario 2"""
from app import create_app
from app.models.scenario2 import Scenario2Model

app = create_app()

with app.app_context():
    try:
        print("Test de la requete get_structures_list()...")
        structures = Scenario2Model.get_structures_list()
        print(f"OK - Nombre de structures trouvees: {len(structures)}")
        if structures:
            print(f"  Premiere structure: {structures[0]}")

        print("\nTest de la requete get_consolidated_data()...")
        results = Scenario2Model.get_consolidated_data(
            date_debut='2025-01-01',
            date_fin='2025-01-31',
            montant_min=None,
            montant_max=None,
            include_acte=True,
            include_rub=True,
            limit=10
        )
        print(f"OK - Nombre de resultats trouves: {len(results)}")
        if results:
            print(f"  Premier resultat:")
            for key, value in results[0].items():
                print(f"    {key}: {value}")

        print("\nTest de count_consolidated_data()...")
        count = Scenario2Model.count_consolidated_data(
            date_debut='2025-01-01',
            date_fin='2025-01-31',
            include_acte=True,
            include_rub=True
        )
        print(f"OK - Nombre total de resultats: {count}")

        print("\nOK - Tous les tests reussis!")

    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
