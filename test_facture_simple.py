"""Test simple de la requête de facture"""
from app import create_app
from app.models.scenario2 import Scenario2Model

app = create_app('development')

with app.app_context():
    # Tester avec un num_pec spécifique (COMPLET avec le slash)
    num_pec = '25M000909/2281E'

    print(f"\n=== Test facture pour: {num_pec} ===\n")

    details = Scenario2Model.get_facture_details(num_pec)

    if not details:
        print(f"Aucun resultat trouve pour {num_pec}")
    else:
        print(f"Nombre de lignes trouvees: {len(details)}\n")

        # Afficher les infos de base
        if details:
            print(f"Num_pec: {details[0].get('num_pec')}")
            print(f"Beneficiaire: {details[0].get('nom_prenom')}")
            print(f"Num bnf: {details[0].get('num_bnf')}\n")

        # Calculer le total
        total = 0
        for detail in details:
            montant = detail.get('montant')
            if montant is not None:
                total += float(montant)
                print(f"- {detail.get('libelle_acte')}: {montant} FCFA")

        print(f"\nMontant total: {total} FCFA")
