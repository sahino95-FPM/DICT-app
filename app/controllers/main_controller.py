"""Contrôleur principal (Dashboard, Scénarios)"""
from flask import Blueprint, render_template, current_app
from app.services.analytics_service import AnalyticsService

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    """Page d'accueil / Dashboard"""
    try:
        stats = AnalyticsService.get_dashboard_stats()

        return render_template(
            'dashboard.html',
            stats=stats
        )
    except Exception as e:
        current_app.logger.error(f"Erreur dashboard: {e}")
        return render_template('dashboard.html', stats={'recent_analyses': []})


@main_bp.route('/test-websocket')
def test_websocket():
    """Page de test WebSocket"""
    return render_template('test_websocket.html')


@main_bp.route('/scenarios')
def scenarios_list():
    """Liste des scénarios disponibles"""

    # Registre des scénarios
    scenarios = [
        {
            'id': 1,
            'titre': 'Recherche des montants exécutés',
            'description': 'Analyse des actes exécutés par structure, dossier et période avec agrégations et exports.',
            'route': 'scenario1.form',
            'active': True,
            'icon': 'search'
        },
        {
            'id': 2,
            'titre': 'Analyse consolidée par dossier',
            'description': 'Montants exécutés par dossier (num_pec) et structure avec infos bénéficiaire, type transaction et source (ACTE/HOSPI).',
            'route': 'scenario2.form',
            'active': True,
            'icon': 'chart'
        },
        {
            'id': 3,
            'titre': 'Scénario 3',
            'description': 'Description du scénario 3 (à implémenter)',
            'route': None,
            'active': False,
            'icon': 'table'
        },
        {
            'id': 4,
            'titre': 'Scénario 4',
            'description': 'Description du scénario 4 (à implémenter)',
            'route': None,
            'active': False,
            'icon': 'stats'
        }
    ]

    return render_template('scenarios/index.html', scenarios=scenarios)
