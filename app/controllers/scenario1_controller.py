"""Contrôleur pour le scénario 1: Recherche montants exécutés"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
from datetime import datetime, timedelta
from app.services.analytics_service import AnalyticsService
from app.models.analysis_log import AnalysisLogModel

scenario1_bp = Blueprint('scenario1', __name__)


@scenario1_bp.route('/')
@scenario1_bp.route('/form')
def form():
    """Affiche le formulaire de recherche"""

    # Valeurs par défaut
    defaults = {
        'date_debut': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'date_fin': datetime.now().strftime('%Y-%m-%d'),
        'montant_min': 0,
        'montant_max': 1000000,
        'group_by_structure': True,
        'group_by_pec': True,
        'group_by_date': False,
        'show_details': False,
        'show_sql': False,
        'limit': 500
    }

    # Récupérer les valeurs de la session si elles existent
    saved_filters = session.get('scenario1_filters', {})
    defaults.update(saved_filters)

    return render_template('scenario1/form.html', defaults=defaults)


@scenario1_bp.route('/results', methods=['POST'])
def results():
    """Traite le formulaire et affiche les résultats"""
    try:
        # Récupération des filtres
        filters = _extract_filters_from_request()

        # Validation
        errors = _validate_filters(filters)
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('scenario1.form'))

        # Sauvegarde des filtres dans la session
        session['scenario1_filters'] = filters

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(filters.get('limit', 50), 500)

        pagination = {
            'page': page,
            'per_page': per_page
        }

        # Exécution de l'analyse
        analysis = AnalyticsService.analyze_scenario1(filters, pagination)

        return render_template(
            'scenario1/results.html',
            results=analysis['results'],
            filters=filters,
            pagination={
                'page': analysis['page'],
                'per_page': analysis['per_page'],
                'total_pages': analysis['total_pages'],
                'total_count': analysis['total_count']
            },
            metrics=analysis['metrics'],
            sql_query=analysis.get('sql_query')
        )

    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'analyse: {e}")
        flash(f"Erreur lors de l'analyse: {str(e)}", 'error')
        return redirect(url_for('scenario1.form'))


@scenario1_bp.route('/save-analysis', methods=['POST'])
def save_analysis():
    """Sauvegarde une analyse"""
    try:
        # Récupération des données du formulaire
        nom_utilisateur = request.form.get('nom_utilisateur', 'Anonyme')
        intitule = request.form.get('intitule', 'Analyse sans titre')
        motif = request.form.get('motif', '')

        # Récupération des filtres de la session
        filters = session.get('scenario1_filters', {})

        # Récupération des métriques (calculées à nouveau)
        analysis = AnalyticsService.analyze_scenario1(filters, {'page': 1, 'per_page': 1})
        metriques = analysis['metrics']

        # Sauvegarde
        log_id = AnalyticsService.save_analysis(
            nom_utilisateur=nom_utilisateur,
            intitule=intitule,
            motif=motif,
            scenario_id=1,
            parametres=filters,
            metriques=metriques
        )

        flash(f"Analyse sauvegardée avec succès (ID: {log_id})", 'success')

    except Exception as e:
        current_app.logger.error(f"Erreur lors de la sauvegarde: {e}")
        flash(f"Erreur lors de la sauvegarde: {str(e)}", 'error')

    return redirect(url_for('scenario1.results'))


def _extract_filters_from_request():
    """Extrait les filtres du formulaire"""
    return {
        'date_debut': request.form.get('date_debut'),
        'date_fin': request.form.get('date_fin'),
        'montant_min': _parse_float(request.form.get('montant_min')),
        'montant_max': _parse_float(request.form.get('montant_max')),
        'group_by_structure': request.form.get('group_by_structure') == 'on',
        'group_by_pec': request.form.get('group_by_pec') == 'on',
        'group_by_date': request.form.get('group_by_date') == 'on',
        'show_details': request.form.get('show_details') == 'on',
        'show_sql': request.form.get('show_sql') == 'on',
        'limit': _parse_int(request.form.get('limit', 500), default=500, min_val=50, max_val=5000)
    }


def _validate_filters(filters):
    """Valide les filtres"""
    errors = []

    # Validation des dates
    if not filters['date_debut']:
        errors.append("La date de début est obligatoire")
    if not filters['date_fin']:
        errors.append("La date de fin est obligatoire")

    if filters['date_debut'] and filters['date_fin']:
        try:
            date_debut = datetime.strptime(filters['date_debut'], '%Y-%m-%d')
            date_fin = datetime.strptime(filters['date_fin'], '%Y-%m-%d')

            if date_debut > date_fin:
                errors.append("La date de début doit être antérieure à la date de fin")

            # Limite de 2 ans
            if (date_fin - date_debut).days > 730:
                errors.append("La période ne peut pas excéder 2 ans")

        except ValueError:
            errors.append("Format de date invalide (attendu: YYYY-MM-DD)")

    # Validation des montants
    if filters['montant_min'] is not None and filters['montant_min'] < 0:
        errors.append("Le montant minimum ne peut pas être négatif")

    if filters['montant_max'] is not None and filters['montant_min'] is not None:
        if filters['montant_max'] < filters['montant_min']:
            errors.append("Le montant maximum doit être supérieur au montant minimum")

    # Au moins un regroupement
    if not any([filters['group_by_structure'], filters['group_by_pec'], filters['group_by_date']]):
        errors.append("Vous devez sélectionner au moins un critère de regroupement")

    return errors


def _parse_float(value, default=None):
    """Parse une valeur en float"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _parse_int(value, default=None, min_val=None, max_val=None):
    """Parse une valeur en int avec bornes"""
    if value is None or value == '':
        return default
    try:
        val = int(value)
        if min_val is not None:
            val = max(val, min_val)
        if max_val is not None:
            val = min(val, max_val)
        return val
    except (ValueError, TypeError):
        return default
