"""Script de test pour vérifier la connexion à la base de données"""
from app import create_app
from app.models.acte import ActeModel

app = create_app()

with app.app_context():
    try:
        results = ActeModel.get_aggregated_data(
            '2025-10-07',
            '2025-11-06',
            0,
            1000000,
            True,
            True,
            False,
            500,
            0
        )
        print(f'✓ Nombre de résultats: {len(results)}')
        if results:
            print(f'✓ Premiers résultats: {results[:2]}')
        else:
            print('⚠ Aucun résultat trouvé')
    except Exception as e:
        print(f'✗ Erreur: {str(e)}')
