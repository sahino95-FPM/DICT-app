"""Contrôleur pour le scénario 1: Recherche montants exécutés"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session, jsonify
from datetime import datetime, timedelta
from app.services.analytics_service import AnalyticsService
from app.models.analysis_log import AnalysisLogModel
from app.models.acte import ActeModel
from app.socketio_events import emit_progress
import uuid
import threading
import time

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
        'limit': 500
    }

    # Récupérer les valeurs de la session si elles existent
    saved_filters = session.get('scenario1_filters', {})
    defaults.update(saved_filters)

    return render_template('scenario1/form.html', defaults=defaults)


@scenario1_bp.route('/analyze', methods=['POST'])
def analyze():
    """
    Lance l'analyse avec progression en temps réel via WebSocket
    Retourne un task_id pour suivre la progression
    """
    try:
        # Récupération des filtres
        filters = _extract_filters_from_request()

        # Validation
        errors = _validate_filters(filters)
        if errors:
            return jsonify({'error': ', '.join(errors)}), 400

        # Générer un ID unique pour cette tâche
        task_id = str(uuid.uuid4())

        # Sauvegarde des filtres dans la session avec le task_id
        session[f'task_{task_id}_filters'] = filters

        # Lancer l'analyse en arrière-plan avec socketio.start_background_task
        from app import socketio
        socketio.start_background_task(_run_analysis_with_progress, task_id, filters)

        return jsonify({
            'success': True,
            'task_id': task_id
        })

    except Exception as e:
        current_app.logger.error(f"Erreur lors du lancement de l'analyse: {e}")
        return jsonify({'error': str(e)}), 500


@scenario1_bp.route('/results', methods=['GET', 'POST'])
def results():
    """Affiche les résultats d'une analyse"""
    try:
        # Si POST, récupérer les filtres du formulaire (mode classique sans WebSocket)
        if request.method == 'POST':
            filters = _extract_filters_from_request()
            errors = _validate_filters(filters)
            if errors:
                for error in errors:
                    flash(error, 'error')
                return redirect(url_for('scenario1.form'))
            session['scenario1_filters'] = filters
        else:
            # Si GET, récupérer les filtres de la session
            task_id = request.args.get('task_id')
            if task_id:
                filters = session.get(f'task_{task_id}_filters')
                if not filters:
                    flash('Session expirée. Veuillez relancer l\'analyse.', 'error')
                    return redirect(url_for('scenario1.form'))
            else:
                filters = session.get('scenario1_filters')
                if not filters:
                    flash('Aucune analyse en cours. Veuillez démarrer une nouvelle recherche.', 'error')
                    return redirect(url_for('scenario1.form'))

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


@scenario1_bp.route('/api/facture-details/<num_pec>')
def get_facture_details(num_pec):
    """
    Récupère les détails d'une facture (endpoint API)

    Args:
        num_pec: Numéro de PEC

    Returns:
        JSON avec les détails de la facture
    """
    try:
        # Requête SQL_TAMPON similaire à admi_claude.py
        query = """
        WITH lignes AS (
          /* (A) Lignes ACTE */
          SELECT
            at.num_pec,
            at.id_structure_executante AS id_structure,
            s.nom_structure,
            at.num_trans,
            laa.id_acte_trans,
            laa.id_acte AS ref_id,
            a.libelle_acte AS libelle_acte,
            laa.date_execution_acte AS date_execution,
            laa.montant_acte AS montant,
            laa.quantite AS nb,
            NULL AS coefficient,
            'ACTE' AS source_ligne
          FROM acte_trans at
          JOIN list_acte_acte_trans laa ON laa.id_acte_trans = at.id_acte_trans
          JOIN structure s ON s.id_structure = at.id_structure_executante
          LEFT JOIN acte a ON a.id_acte = laa.id_acte
          WHERE at.num_pec = :num_pec

          UNION ALL

          /* (B) Lignes HOSPI (rubriques hospitalisation) */
          SELECT
            at.num_pec,
            at.id_structure_executante AS id_structure,
            s.nom_structure,
            at.num_trans,
            lrh.id_acte_trans,
            COALESCE(lrh.id_acte, lrh.id_rub_hospit) AS ref_id,
            COALESCE(a2.libelle_acte, rh.libelle) AS libelle_acte,
            lrh.date_execution_acte AS date_execution,
            lrh.montant AS montant,
            lrh.qte AS nb,
            NULL AS coefficient,
            'HOSPI' AS source_ligne
          FROM acte_trans at
          JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at.id_acte_trans
          JOIN structure s ON s.id_structure = at.id_structure_executante
          LEFT JOIN acte a2 ON a2.id_acte = lrh.id_acte
          LEFT JOIN rubrique_hospitalisations rh ON rh.id = lrh.id_rub_hospit
          WHERE at.num_pec = :num_pec
        )
        SELECT
          li.num_pec,
          li.id_structure,
          li.nom_structure,
          li.num_trans,
          li.id_acte_trans,
          li.ref_id,
          li.libelle_acte,
          li.source_ligne,
          li.date_execution,
          li.montant,
          li.nb,
          li.coefficient
        FROM lignes li
        ORDER BY
          li.date_execution ASC,
          li.source_ligne ASC,
          li.ref_id ASC
        """

        lignes = ActeModel.execute_query(query, {'num_pec': num_pec})

        if not lignes:
            return jsonify({'error': 'Aucun détail trouvé pour ce PEC'}), 404

        # Calculer le montant total
        montant_total = sum((ligne.get('montant', 0) or 0) * (ligne.get('nb', 1) or 1) for ligne in lignes)

        return jsonify({
            'num_pec': num_pec,
            'nb_lignes': len(lignes),
            'montant_total': montant_total,
            'lignes': lignes
        })

    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des détails de facture: {e}")
        return jsonify({'error': str(e)}), 500


def _extract_filters_from_request():
    """Extrait les filtres du formulaire"""
    return {
        'date_debut': request.form.get('date_debut'),
        'date_fin': request.form.get('date_fin'),
        'montant_min': _parse_float(request.form.get('montant_min')),
        'montant_max': _parse_float(request.form.get('montant_max')),
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


def _run_analysis_with_progress(task_id, filters):
    """
    Exécute l'analyse avec émission de mises à jour de progression via WebSocket

    Args:
        task_id: ID unique de la tâche
        filters: Filtres de recherche
    """
    from app import socketio

    try:
        # Étape 1: Initialisation (5%)
        emit_progress(task_id, 5, 'Initialisation de l\'analyse...', 'running')
        socketio.sleep(0.5)

        # Étape 2: Comptage du nombre total de PEC (15%)
        emit_progress(task_id, 15, 'Comptage du nombre total de PEC...', 'running')
        total_count = ActeModel.count_detailed_pec(
            date_debut=filters.get('date_debut'),
            date_fin=filters.get('date_fin'),
            montant_min=filters.get('montant_min'),
            montant_max=filters.get('montant_max')
        )
        emit_progress(task_id, 25, f'{total_count} PEC trouvés', 'running')
        socketio.sleep(0.5)

        # Étape 3: Récupération des données (30% - 80%)
        emit_progress(task_id, 30, 'Récupération des données détaillées...', 'running')

        results = ActeModel.get_detailed_pec_data(
            date_debut=filters.get('date_debut'),
            date_fin=filters.get('date_fin'),
            montant_min=filters.get('montant_min'),
            montant_max=filters.get('montant_max'),
            limit=filters.get('limit', 500),
            offset=0
        )

        emit_progress(task_id, 80, f'{len(results)} enregistrements récupérés', 'running')
        socketio.sleep(0.5)

        # Étape 4: Calcul des métriques (90%)
        emit_progress(task_id, 90, 'Calcul des métriques...', 'running')
        socketio.sleep(0.3)

        # Étape 5: Finalisation (100%)
        emit_progress(task_id, 100, 'Analyse terminée avec succès !', 'completed')

    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'analyse avec progression: {e}")
        import traceback
        traceback.print_exc()
        emit_progress(task_id, 0, f'Erreur: {str(e)}', 'error')
