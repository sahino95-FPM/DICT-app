"""Test de la requête de facture pour déboguer les montants"""
from app import create_app
from app.models.scenario2 import Scenario2Model

app = create_app('development')

with app.app_context():
    # Tester avec un num_pec spécifique (COMPLET avec le slash)
    num_pec = '25M000909/2281E'  # Remplacez par un num_pec de votre choix

    print(f"\n=== Test de la requête facture EXACTE pour '{num_pec}' ===\n")

    details = Scenario2Model.get_facture_details(num_pec)

    if not details:
        print(f"❌ Aucun résultat trouvé pour '{num_pec}'")
        print("\nVérification: ce num_pec existe-t-il EXACTEMENT dans acte_trans?")
    else:
        print(f"✅ Nombre de lignes trouvées: {len(details)}\n")

        # Afficher le num_pec trouvé pour vérifier
        if details:
            print(f"Num_pec trouvé dans les résultats: '{details[0].get('num_pec')}'")
            print(f"Nom bénéficiaire: {details[0].get('nom_prenom')}")
            print(f"Num bénéficiaire: {details[0].get('num_bnf')}")
            print()

        for i, detail in enumerate(details, 1):
            print(f"Ligne {i}:")
            print(f"  Structure: {detail.get('nom_structure')}")
            print(f"  Libellé: {detail.get('libelle_acte')}")
            print(f"  Source: {detail.get('source_ligne')}")
            print(f"  Quantité (nb): {detail.get('nb')}")
            print(f"  Montant: {detail.get('montant')}")
            print(f"  Date début: {detail.get('premiere_date_execution')}")
            print(f"  Date fin: {detail.get('derniere_date_execution')}")
            print()

        # Calculer le total
        total = 0
        for detail in details:
            montant = detail.get('montant')
            if montant is not None:
                try:
                    total += float(montant)
                except (ValueError, TypeError) as e:
                    print(f"Erreur conversion montant: {montant} -> {e}")

        print(f"💰 Montant total calculé: {total} FCFA")
