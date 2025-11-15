"""Test du service analytics pour le dashboard"""
from app import create_app
from app.services.analytics_service import AnalyticsService

app = create_app('development')

with app.app_context():
    print("\n=== Test get_dashboard_stats() ===\n")

    try:
        stats = AnalyticsService.get_dashboard_stats()
        print(f"Stats retournees: {stats}")
        print(f"\nPEC today: {stats.get('pec_today')}")
        print(f"Type: {type(stats.get('pec_today'))}")
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
