"""Contrôleur pour les exports"""
from flask import Blueprint, request, flash, redirect, url_for, current_app, session
from app.services.analytics_service import AnalyticsService
from app.services.scenario2_service import Scenario2Service
from app.services.export_service import ExportService
import os

exports_bp = Blueprint('exports', __name__)


@exports_bp.route('/scenario1/<format>')
def export_scenario1(format):
    """
    Exporte les résultats du scénario 1

    Args:
        format: csv, xlsx ou pdf
    """
    try:
        # Récupération des filtres de la session
        filters = session.get('scenario1_filters', {})

        if not filters:
            flash("Aucune donnée à exporter. Veuillez d'abord effectuer une recherche.", 'warning')
            return redirect(url_for('scenario1.form'))

        # Exécution de l'analyse (sans pagination pour export complet)
        max_rows = current_app.config['MAX_EXPORT_ROWS']
        analysis = AnalyticsService.analyze_scenario1(
            filters,
            {'page': 1, 'per_page': max_rows}
        )

        results = analysis['results']

        if not results:
            flash("Aucune donnée à exporter", 'warning')
            return redirect(url_for('scenario1.form'))

        # Préparation des données
        export_data = ExportService.prepare_export_data(results, format)

        # Construction des métadonnées
        metadata = {
            'Période': f"{filters.get('date_debut')} au {filters.get('date_fin')}",
            'Nombre de résultats': len(results),
            'Montant total': f"{analysis['metrics']['montant_total']:,.0f} FCFA"
        }

        # Export selon le format
        if format == 'csv':
            return ExportService.export_to_csv(
                data=export_data['data'],
                columns=export_data['columns'],
                filename_prefix='scenario1_montants_executes'
            )

        elif format == 'xlsx':
            return ExportService.export_to_xlsx(
                data=export_data['data'],
                columns=export_data['columns'],
                column_labels=export_data['column_labels'],
                filename_prefix='scenario1_montants_executes',
                sheet_name='Montants exécutés'
            )

        elif format == 'pdf':
            logo_path = os.path.join(current_app.static_folder, 'img', 'logo_fpm.png')

            return ExportService.export_to_pdf(
                data=export_data['data'],
                columns=export_data['columns'],
                column_labels=export_data['column_labels'],
                title='Recherche des montants exécutés',
                filename_prefix='scenario1_montants_executes',
                metadata=metadata,
                logo_path=logo_path if os.path.exists(logo_path) else None
            )

        elif format == 'word':
            logo_path = os.path.join(current_app.static_folder, 'img', 'logo_fpm.png')

            return ExportService.export_to_word(
                data=export_data['data'],
                columns=export_data['columns'],
                column_labels=export_data['column_labels'],
                title='Recherche des montants exécutés',
                filename_prefix='scenario1_montants_executes',
                metadata=metadata,
                logo_path=logo_path if os.path.exists(logo_path) else None
            )

        else:
            flash(f"Format d'export non supporté: {format}", 'error')
            return redirect(url_for('scenario1.results'))

    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'export: {e}")
        flash(f"Erreur lors de l'export: {str(e)}", 'error')
        return redirect(url_for('scenario1.form'))


@exports_bp.route('/scenario2/<format>')
def export_scenario2(format):
    """
    Exporte les résultats du scénario 2

    Args:
        format: csv, xlsx, pdf ou word
    """
    try:
        # Récupération des filtres de la session
        filters = session.get('scenario2_filters', {})

        if not filters:
            flash("Aucune donnée à exporter. Veuillez d'abord effectuer une recherche.", 'warning')
            return redirect(url_for('scenario2.form'))

        # Exécution de l'analyse (sans pagination pour export complet)
        max_rows = current_app.config['MAX_EXPORT_ROWS']
        analysis = Scenario2Service.analyze_scenario2(
            filters,
            {'page': 1, 'per_page': max_rows}
        )

        results = analysis['results']

        if not results:
            flash("Aucune donnée à exporter", 'warning')
            return redirect(url_for('scenario2.form'))

        # Préparation des données pour l'export
        export_data = ExportService.prepare_scenario2_export_data(
            results,
            filters,
            format
        )

        # Construction des métadonnées
        metadata = {
            'Période': f"{filters.get('date_debut')} au {filters.get('date_fin')}",
            'Nombre de résultats': len(results),
            'Total dossiers': analysis['metrics']['total_dossiers'],
            'Total bénéficiaires': analysis['metrics']['total_beneficiaires'],
            'Montant total': f"{analysis['metrics']['montant_total']:,.0f} FCFA"
        }

        # Export selon le format
        if format == 'csv':
            return ExportService.export_to_csv(
                data=export_data['data'],
                columns=export_data['columns'],
                filename_prefix='scenario2_analyse_consolidee'
            )

        elif format == 'xlsx':
            return ExportService.export_to_xlsx(
                data=export_data['data'],
                columns=export_data['columns'],
                column_labels=export_data['column_labels'],
                filename_prefix='scenario2_analyse_consolidee',
                sheet_name='Analyse consolidée'
            )

        elif format == 'pdf':
            logo_path = os.path.join(current_app.static_folder, 'img', 'logo_fpm.png')

            return ExportService.export_to_pdf(
                data=export_data['data'],
                columns=export_data['columns'],
                column_labels=export_data['column_labels'],
                title='Analyse consolidée par dossier et structure',
                filename_prefix='scenario2_analyse_consolidee',
                metadata=metadata,
                logo_path=logo_path if os.path.exists(logo_path) else None
            )

        elif format == 'word':
            logo_path = os.path.join(current_app.static_folder, 'img', 'logo_fpm.png')

            return ExportService.export_to_word(
                data=export_data['data'],
                columns=export_data['columns'],
                column_labels=export_data['column_labels'],
                title='Analyse consolidée par dossier et structure',
                filename_prefix='scenario2_analyse_consolidee',
                metadata=metadata,
                logo_path=logo_path if os.path.exists(logo_path) else None
            )

        else:
            flash(f"Format d'export non supporté: {format}", 'error')
            return redirect(url_for('scenario2.results'))

    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'export: {e}")
        flash(f"Erreur lors de l'export: {str(e)}", 'error')
        return redirect(url_for('scenario2.form'))
