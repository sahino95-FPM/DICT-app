"""Diagnostic des donnees brutes dans list_acte_acte_trans"""
from app import create_app
from app.models.scenario2 import Scenario2Model

app = create_app('development')

with app.app_context():
    num_pec = '25M000909/2281E'

    # Requete directe sur list_acte_acte_trans pour voir les vraies donnees
    query = """
    SELECT
        at.num_pec,
        a.libelle_acte,
        laa.montant_acte,
        laa.quantite,
        laa.date_execution_acte
    FROM acte_trans at
    JOIN list_acte_acte_trans laa ON laa.id_acte_trans = at.id_acte_trans
    LEFT JOIN acte a ON a.id_acte = laa.id_acte
    WHERE at.num_pec = :num_pec
    ORDER BY laa.date_execution_acte
    """

    results = Scenario2Model.execute_query(query, {'num_pec': num_pec})

    print(f"\n=== Donnees brutes pour {num_pec} ===\n")

    if not results:
        print("Aucune donnee trouvee!")
    else:
        print(f"Nombre de lignes: {len(results)}\n")
        for r in results:
            print(f"Acte: {r.get('libelle_acte')}")
            print(f"  montant_acte: {r.get('montant_acte')} (type: {type(r.get('montant_acte'))})")
            print(f"  quantite: {r.get('quantite')} (type: {type(r.get('quantite'))})")
            print(f"  date: {r.get('date_execution_acte')}")
            print()
