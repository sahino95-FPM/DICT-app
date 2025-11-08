"""
Script de test pour vérifier l'inclusion de la table PHARMACIE dans le Scénario 2
"""
import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le chemin de l'application
sys.path.insert(0, os.path.dirname(__file__))

from app.models.scenario2 import Scenario2Model

def test_pharmacie_inclusion():
    """
    Teste que les données de pharmacie sont bien incluses dans les résultats
    """
    print("=" * 70)
    print(" TEST: Inclusion de la table PHARMACIE dans le Scénario 2")
    print("=" * 70)
    print()

    # Paramètres de test (à adapter selon vos données)
    # L'utilisateur attend 922 lignes et un total de 1 857 098
    filters = {
        'date_debut': '2025-01-01',
        'date_fin': '2025-12-31',
        'montant_min': None,
        'montant_max': None,
        'include_acte': True,
        'include_rub': True,
        'include_pharmacie': True,  # ✓ PHARMACIE INCLUSE
        'num_pec': '',  # Vide pour tout récupérer, ou spécifier un num_pec
        'num_bnf': None,
        'nom_prenom': None,
        'id_structures': None,
        'sort_by': 'num_pec',
        'sort_order': 'ASC',
        'limit': 10000,  # Grande limite pour tout récupérer
        'offset': 0
    }

    try:
        print("⏳ Récupération des données consolidées...")
        results = Scenario2Model.get_consolidated_data(**filters)

        print(f"✓ Données récupérées avec succès!")
        print()
        print(f"📊 Nombre de lignes: {len(results)}")
        print()

        # Compter les sources
        sources = {}
        total_montant = 0

        for row in results:
            source = row.get('source_ligne', 'UNKNOWN')
            sources[source] = sources.get(source, 0) + 1
            total_montant += float(row.get('montant_execute_total', 0) or 0)

        print("📋 Répartition par source:")
        for source, count in sorted(sources.items()):
            print(f"   - {source}: {count} lignes")

        print()
        print(f"💰 Montant total: {total_montant:,.2f} FCFA")
        print()

        # Vérification des attentes
        print("🎯 Vérification des résultats attendus:")
        print(f"   - Lignes attendues: 922")
        print(f"   - Lignes obtenues: {len(results)}")
        print(f"   - Match: {'✓ OUI' if len(results) == 922 else '✗ NON'}")
        print()
        print(f"   - Total attendu: 1 857 098 FCFA")
        print(f"   - Total obtenu: {total_montant:,.0f} FCFA")
        print(f"   - Match: {'✓ OUI' if abs(total_montant - 1857098) < 1 else '✗ NON'}")
        print()

        # Afficher quelques exemples de lignes PHARMACIE
        pharmacie_lignes = [r for r in results if r.get('source_ligne') == 'PHARMACIE']
        if pharmacie_lignes:
            print(f"✓ PHARMACIE trouvée! ({len(pharmacie_lignes)} lignes)")
            print()
            print("📦 Exemples de lignes PHARMACIE (5 premières):")
            for i, ligne in enumerate(pharmacie_lignes[:5], 1):
                print(f"   {i}. {ligne.get('libelle_acte', 'N/A')} - "
                      f"{ligne.get('montant_execute_total', 0):,.0f} FCFA - "
                      f"Structure: {ligne.get('nom_structure', 'N/A')}")
        else:
            print("⚠️  Aucune ligne PHARMACIE trouvée (vérifiez que la table existe)")

        print()
        print("=" * 70)
        print("✅ TEST TERMINÉ")
        print("=" * 70)

    except Exception as e:
        print(f"❌ ERREUR lors du test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    # Vérifier que les variables d'environnement MariaDB sont configurées
    required_vars = ['MARIADB_HOST', 'MARIADB_NAME', 'MARIADB_USER', 'MARIADB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Variables d'environnement manquantes dans .env:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("Veuillez configurer ces variables dans le fichier .env")
        sys.exit(1)

    test_pharmacie_inclusion()
