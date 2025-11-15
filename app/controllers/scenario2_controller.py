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


@scenario2_bp.route('/results', methods=['GET', 'POST'])
def results():
    """Traite le formulaire et redirige directement vers la facture"""
    try:
        # Récupération des filtres
        filters = _extract_filters_from_request()

        # Validation
        errors = _validate_filters(filters)
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('scenario2.form'))

        # Récupérer le num_pec
        num_pec = filters.get('num_pec')

        if not num_pec:
            flash("Le numéro de dossier (PEC) est requis", 'error')
            return redirect(url_for('scenario2.form'))

        # Redirection directe vers la facture avec le num_pec
        return redirect(url_for('scenario2.facture', num_pec=num_pec))

    except Exception as e:
        current_app.logger.error(f"Erreur lors du traitement: {e}")
        flash(f"Erreur lors du traitement: {str(e)}", 'error')
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


@scenario2_bp.route('/facture/<path:num_pec>', methods=['GET'])
def facture(num_pec):
    """Affiche la facture détaillée pour un num_pec donné"""
    try:
        # Log du num_pec reçu pour debug
        current_app.logger.info(f"Recherche facture pour num_pec: '{num_pec}'")

        # Récupérer les détails groupés de la facture
        details = Scenario2Model.get_facture_details(num_pec)

        # S'assurer que details est une liste
        if details is None:
            details = []

        if not details:
            flash(f"Aucune donnée trouvée pour le dossier {num_pec}", 'warning')
            return redirect(url_for('main.scenarios_list'))

        # Calculer le montant total cumulé (gérer les valeurs None)
        montant_total = 0
        for item in details:
            montant = item.get('montant')
            if montant is not None:
                try:
                    montant_total += float(montant)
                except (ValueError, TypeError):
                    current_app.logger.warning(f"Montant invalide ignoré: {montant}")
                    pass

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
        return redirect(url_for('main.scenarios_list'))


def _extract_filters_from_request():
    """Extrait les filtres du formulaire"""
    # Valeurs par défaut pour le formulaire simplifié (uniquement num_pec)
    # On définit une large période par défaut pour capturer tous les actes/rubriques
    default_date_debut = (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d')  # 10 ans
    default_date_fin = datetime.now().strftime('%Y-%m-%d')

    # Structures sélectionnées (peut être une liste)
    id_structures = request.form.getlist('id_structures')

    return {
        # Dates: par défaut sur 10 ans pour tout capturer
        'date_debut': request.form.get('date_debut', default_date_debut),
        'date_fin': request.form.get('date_fin', default_date_fin),
        # Montants: pas de filtre par défaut
        'montant_min': _parse_float(request.form.get('montant_min')),
        'montant_max': _parse_float(request.form.get('montant_max')),
        # Sources: toujours inclure ACTE et HOSPI pour le total complet
        'include_acte': request.form.get('include_acte', 'on') == 'on',
        'include_rub': request.form.get('include_rub', 'on') == 'on',
        # Filtres de recherche
        'num_bnf': request.form.get('num_bnf', '').strip(),
        'nom_prenom': request.form.get('nom_prenom', '').strip(),
        'num_pec': request.form.get('num_pec', '').strip(),
        'id_structures': id_structures,
        # Options d'affichage
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

            # Pas de limite de période pour le formulaire simplifié
            # (nous utilisons une large période par défaut pour capturer tous les actes)

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
        errors.append("Vous devez sélectionner au moins une source (ACTE ou HOSPI)")

    # Validation du numéro PEC (obligatoire pour le formulaire simplifié)
    if not filters.get('num_pec'):
        errors.append("Le numéro de dossier (PEC) est obligatoire")

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
