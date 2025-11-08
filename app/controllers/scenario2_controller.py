"""Contrôleur pour le scénario 2: Analyse consolidée des montants"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
from datetime import datetime, timedelta
from app.services.scenario2_service import Scenario2Service
from app.models.scenario2 import Scenario2Model

scenario2_bp = Blueprint('scenario2', __name__)


@scenario2_bp.route('/')
@scenario2_bp.route('/form')
def form():
    """Affiche le formulaire de recherche du scénario 2"""

    # Valeurs par défaut
    defaults = {
        'date_debut': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
        'date_fin': datetime.now().strftime('%Y-%m-%d'),
        'montant_min': 5000,
        'montant_max': 25000,
        'include_acte': True,
        'include_rub': True,
        'num_bnf': '',
        'nom_prenom': '',
        'num_pec': '',
        'id_structures': [],
        'sort_by': 'num_pec',
        'sort_order': 'ASC',
        'show_sql': False,
        'show_details': False,
        'mask_phone': False,
        'limit': 500,
        # Colonnes d'affichage
        'show_beneficiaire': True,
        'show_type_trans': True,
        'show_nb_lignes': True,
        'show_telephone': True,
        'show_sexe': True,
        'show_date_naissance': True
    }

    # Récupérer les valeurs de la session si elles existent
    saved_filters = session.get('scenario2_filters', {})
    defaults.update(saved_filters)

    # Récupérer la liste des structures pour le formulaire
    try:
        structures = Scenario2Service.get_structures_for_select()
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des structures: {e}")
        structures = []
        flash("Impossible de charger la liste des structures", 'warning')

    return render_template('scenario2/form.html', defaults=defaults, structures=structures)


@scenario2_bp.route('/results', methods=['POST'])
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
            return redirect(url_for('scenario2.form'))

        # Sauvegarde des filtres dans la session
        session['scenario2_filters'] = filters

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(filters.get('limit', 50), 5000)

        pagination = {
            'page': page,
            'per_page': per_page
        }

        # Exécution de l'analyse
        analysis = Scenario2Service.analyze_scenario2(filters, pagination)

        # Masquage des téléphones si demandé
        if filters.get('mask_phone'):
            for result in analysis['results']:
                if result.get('telephone'):
                    result['telephone'] = Scenario2Service.mask_phone_number(result['telephone'])

        return render_template(
            'scenario2/results.html',
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
        return redirect(url_for('scenario2.form'))


@scenario2_bp.route('/save-analysis', methods=['POST'])
def save_analysis():
    """Sauvegarde une analyse"""
    try:
        # Récupération des données du formulaire
        nom_utilisateur = request.form.get('nom_utilisateur', 'Anonyme')
        intitule = request.form.get('intitule', 'Analyse sans titre')
        motif = request.form.get('motif', '')

        # Récupération des filtres de la session
        filters = session.get('scenario2_filters', {})

        # Récupération des métriques (calculées à nouveau)
        analysis = Scenario2Service.analyze_scenario2(filters, {'page': 1, 'per_page': 1})
        metriques = analysis['metrics']

        # Sauvegarde
        log_id = Scenario2Service.save_analysis(
            nom_utilisateur=nom_utilisateur,
            intitule=intitule,
            motif=motif,
            parametres=filters,
            metriques=metriques
        )

        flash(f"Analyse sauvegardée avec succès (ID: {log_id})", 'success')

    except Exception as e:
        current_app.logger.error(f"Erreur lors de la sauvegarde: {e}")
        flash(f"Erreur lors de la sauvegarde: {str(e)}", 'error')

    return redirect(url_for('scenario2.results'))


@scenario2_bp.route('/facture/<path:num_pec>')
def facture(num_pec):
    """Affiche la facture détaillée pour un num_pec donné"""
    try:
        # Récupérer les détails groupés de la facture
        details = Scenario2Model.get_facture_details(num_pec)

        # S'assurer que details est une liste
        if details is None:
            details = []

        if not details:
            flash(f"Aucune donnée trouvée pour le dossier {num_pec}", 'warning')
            return redirect(url_for('scenario2.results'))

        # Calculer le montant total cumulé
        montant_total = sum(float(item['montant']) if item['montant'] is not None else 0 for item in details)

        # Récupérer les infos de base (premier élément)
        info_base = details[0] if details else {}

        return render_template(
            'scenario2/facture.html',
            num_pec=num_pec,
            details=details or [],
            montant_total=montant_total,
            nom_structure=info_base.get('nom_structure', 'N/A'),
            nom_prenom=info_base.get('nom_prenom', 'N/A'),
            num_bnf=info_base.get('num_bnf', 'N/A')
        )

    except Exception as e:
        current_app.logger.error(f"Erreur lors de la génération de la facture: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f"Erreur lors de la génération de la facture: {str(e)}", 'error')
        return redirect(url_for('scenario2.results'))


def _extract_filters_from_request():
    """Extrait les filtres du formulaire"""
    # Structures sélectionnées (peut être une liste)
    id_structures = request.form.getlist('id_structures')

    return {
        'date_debut': request.form.get('date_debut'),
        'date_fin': request.form.get('date_fin'),
        'montant_min': _parse_float(request.form.get('montant_min')),
        'montant_max': _parse_float(request.form.get('montant_max')),
        'include_acte': request.form.get('include_acte') == 'on',
        'include_rub': request.form.get('include_rub') == 'on',
        'num_bnf': request.form.get('num_bnf', '').strip(),
        'nom_prenom': request.form.get('nom_prenom', '').strip(),
        'num_pec': request.form.get('num_pec', '').strip(),
        'id_structures': id_structures,
        'sort_by': request.form.get('sort_by', 'num_pec'),
        'sort_order': request.form.get('sort_order', 'ASC'),
        'show_sql': request.form.get('show_sql') == 'on',
        'show_details': request.form.get('show_details') == 'on',
        'mask_phone': request.form.get('mask_phone') == 'on',
        'limit': _parse_int(request.form.get('limit', 500), default=500, min_val=50, max_val=50000),
        # Colonnes d'affichage
        'show_beneficiaire': request.form.get('show_beneficiaire', 'on') == 'on',
        'show_type_trans': request.form.get('show_type_trans', 'on') == 'on',
        'show_nb_lignes': request.form.get('show_nb_lignes', 'on') == 'on',
        'show_telephone': request.form.get('show_telephone', 'on') == 'on',
        'show_sexe': request.form.get('show_sexe', 'on') == 'on',
        'show_date_naissance': request.form.get('show_date_naissance', 'on') == 'on'
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

            # Limite de 3 ans
            if (date_fin - date_debut).days > 1095:
                errors.append("La période ne peut pas excéder 3 ans")

        except ValueError:
            errors.append("Format de date invalide (attendu: YYYY-MM-DD)")

    # Validation des montants
    if filters['montant_min'] is not None and filters['montant_min'] < 0:
        errors.append("Le montant minimum ne peut pas être négatif")

    if filters['montant_max'] is not None and filters['montant_min'] is not None:
        if filters['montant_max'] < filters['montant_min']:
            errors.append("Le montant maximum doit être supérieur au montant minimum")

    # Au moins une source
    if not filters['include_acte'] and not filters['include_rub']:
        errors.append("Vous devez sélectionner au moins une source (ACTE ou RUB)")

    # Validation limite
    if filters['limit'] > 50000:
        errors.append("La limite de résultats ne peut pas excéder 50 000")

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
