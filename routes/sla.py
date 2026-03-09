from flask import Blueprint, jsonify, request, send_file, current_app
from flask_login import login_required
from extensions import csrf
from sla_utils import get_violations, send_sla_alert
from utils_export import generate_csv, PDFReport, format_datetime
from models import db, Intervention, DemandeIntervention, User
from datetime import datetime
from io import BytesIO
from reportlab.lib.units import inch

sla_bp = Blueprint('sla', __name__, url_prefix='/api/sla')


@sla_bp.route('/violations', methods=['GET'])
@login_required
def api_sla_violations():
    violations = get_violations()
    return jsonify({'success': True, 'violations': violations})


@sla_bp.route('/check', methods=['POST'])
@login_required
@csrf.exempt
def api_sla_check():
    data = request.get_json() or {}
    send_alerts = bool(data.get('send_alerts', False))
    send_email = bool(data.get('send_email', False))

    violations = get_violations()
    alerted = 0
    if send_alerts:
        for v in violations:
            ok = send_sla_alert(v, notify_sms=True, notify_email=send_email)
            if ok:
                alerted += 1

    return jsonify({'success': True, 'violations_count': len(violations), 'alerted': alerted})


# ============================================================
# EXPORT ENDPOINTS
# ============================================================

@sla_bp.route('/export/violations', methods=['GET'])
@login_required
def api_export_sla_violations():
    """
    Export SLA violations as CSV or PDF
    
    Query Parameters:
    - format: 'csv' or 'pdf' (default: csv)
    - severity: critical, high, medium, low
    """
    try:
        # Get query parameters
        export_format = request.args.get('format', 'csv').lower()
        severity_filter = request.args.get('severity')
        
        # Validate format
        if export_format not in ['csv', 'pdf']:
            return jsonify({'error': 'Invalid format. Use csv or pdf'}), 400
        
        # Get all violations
        violations = get_violations()
        
        # Prepare data for export
        export_data = []
        for v in violations:
            intervention_id = v.get('intervention_id')
            intervention = db.session.get(Intervention, intervention_id)
            demande = intervention.demande if intervention else None
            technicien = intervention.technicien if intervention else None
            
            # Calculate severity based on escalation level and overdue hours
            overdue_hours = v.get('overdue_seconds', 0) / 3600 if v.get('overdue_seconds') else 0
            escalation_level = v.get('escalation_level', 0)
            
            if overdue_hours > 48 or escalation_level >= 3:
                severity = 'Critique'
            elif overdue_hours > 24 or escalation_level >= 2:
                severity = 'Élevée'
            elif overdue_hours > 12 or escalation_level >= 1:
                severity = 'Moyenne'
            else:
                severity = 'Basse'
            
            # Apply severity filter if specified
            if severity_filter:
                severity_map = {
                    'critical': 'Critique',
                    'high': 'Élevée',
                    'medium': 'Moyenne',
                    'low': 'Basse'
                }
                if severity_map.get(severity_filter.lower()) != severity:
                    continue
            
            export_data.append({
                'ID Intervention': intervention_id,
                'ND Demande': demande.nd if demande else '-',
                'Client': demande.nom_client if demande else '-',
                'Service': demande.service if demande else '-',
                'Technicien': f"{technicien.nom} {technicien.prenom}" if technicien else '-',
                'Statut': intervention.statut if intervention else '-',
                'Priorité': demande.priorite_traitement if demande else '-',
                'SLA Hours': v.get('sla_hours', '-'),
                'Écart (heures)': f"{overdue_hours:.1f}",
                'Niveau Escalade': str(escalation_level),
                'Sévérité': severity,
                'Date Création': format_datetime(intervention.date_creation) if intervention else '-',
                'Dernier Alerte': format_datetime(v.get('last_alerted_at')) if v.get('last_alerted_at') else '-'
            })
        
        # Generate CSV or PDF
        if export_format == 'csv':
            headers = [
                'ID Intervention', 'ND Demande', 'Client', 'Service', 'Technicien',
                'Statut', 'Priorité', 'SLA Hours', 'Écart (heures)', 'Niveau Escalade',
                'Sévérité', 'Date Création', 'Dernier Alerte'
            ]
            csv_data, filename = generate_csv(export_data, headers)
            
            return send_file(
                BytesIO(csv_data),
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
        
        else:  # PDF format
            # Create PDF report
            report = PDFReport(
                'RAPPORT DES VIOLATIONS SLA',
                filename=f"violations_sla_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                landscape_mode=True
            )
            
            # Add title and metadata
            report.add_title('RAPPORT DES VIOLATIONS SLA')
            
            metadata = {
                'Date de rapport': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'Total violations': str(len(export_data))
            }
            if severity_filter:
                metadata['Sévérité'] = severity_filter.upper()
            
            report.add_metadata(metadata)
            
            # Add summary statistics
            report.add_heading('Résumé des Violations')
            
            critiques = sum(1 for d in export_data if d['Sévérité'] == 'Critique')
            elevees = sum(1 for d in export_data if d['Sévérité'] == 'Élevée')
            moyennes = sum(1 for d in export_data if d['Sévérité'] == 'Moyenne')
            basses = sum(1 for d in export_data if d['Sévérité'] == 'Basse')
            
            stats_text = f"<b>Critique:</b> {critiques} | <b>Élevée:</b> {elevees} | <b>Moyenne:</b> {moyennes} | <b>Basse:</b> {basses}"
            report.add_paragraph(stats_text, 'SmallText')
            report.add_spacer(0.1)
            
            # Add table
            if export_data:
                table_data = []
                for d in export_data:
                    table_data.append([
                        str(d['ID Intervention']),
                        d['ND Demande'],
                        d['Client'][:20],
                        d['Service'],
                        d['Technicien'][:20],
                        d['Statut'],
                        d['Priorité'],
                        d['Écart (heures)'],
                        d['Sévérité']
                    ])
                
                report.add_table(
                    table_data,
                    headers=['ID Int.', 'ND', 'Client', 'Service', 'Technicien', 'Statut', 'Priorité', 'Écart (h)', 'Sévérité'],
                    col_widths=[0.6*inch, 0.8*inch, 1*inch, 0.9*inch, 1.2*inch, 0.8*inch, 1*inch, 0.8*inch, 1*inch]
                )
            else:
                report.add_paragraph("Aucune violation SLA détectée.", 'Normal')
            
            # Build PDF and return
            pdf_bytes = report.build()
            
            return send_file(
                BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=report.filename
            )
    
    except Exception as e:
        current_app.logger.error(f"Error exporting SLA violations: {str(e)}")
        return jsonify({'error': str(e)}), 500

