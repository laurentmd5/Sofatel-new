"""
RH Email Notification System
Gestion des emails automatiques pour les demandes de congés
"""

from flask_mail import Message
from flask import current_app, render_template_string
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# ============================================================
# EMAIL TEMPLATES
# ============================================================

TEMPLATE_LEAVE_REQUEST_CONFIRMATION = """
<h2>Confirmation de demande de congé</h2>

<p>Bonjour {{ employee_name }},</p>

<p>Votre demande de congé a été enregistrée avec succès.</p>

<table style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff;">
    <tr><td><strong>Type:</strong></td><td>{{ leave_type }}</td></tr>
    <tr><td><strong>Période:</strong></td><td>{{ start_date }} au {{ end_date }}</td></tr>
    <tr><td><strong>Jours ouvrables:</strong></td><td>{{ business_days }}</td></tr>
    <tr><td><strong>Motif:</strong></td><td>{{ reason }}</td></tr>
    <tr><td><strong>Référence:</strong></td><td><code>{{ leave_id }}</code></td></tr>
</table>

<p><strong>Statut:</strong> <span style="color: #ffc107; font-weight: bold;">EN ATTENTE D'APPROBATION</span></p>

<p>Votre demande a été transmise à votre responsable. Vous recevrez une notification dès que votre demande aura été traitée.</p>

<p style="margin-top: 30px; font-size: 12px; color: #666;">
    <strong>Ne pas répondre à cet email.</strong> Pour toute question, contactez le département RH.
</p>
"""

TEMPLATE_LEAVE_REQUEST_NOTIFICATION = """
<h2>Nouvelle demande de congé en attente</h2>

<p>Bonjour {{ manager_name }},</p>

<p>Une nouvelle demande de congé est en attente de votre approbation.</p>

<table style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #ffc107;">
    <tr><td><strong>Employé:</strong></td><td>{{ employee_name }}</td></tr>
    <tr><td><strong>Type:</strong></td><td>{{ leave_type }}</td></tr>
    <tr><td><strong>Période:</strong></td><td>{{ start_date }} au {{ end_date }}</td></tr>
    <tr><td><strong>Jours ouvrables:</strong></td><td>{{ business_days }}</td></tr>
    <tr><td><strong>Motif:</strong></td><td>{{ reason }}</td></tr>
    <tr><td><strong>Soumis le:</strong></td><td>{{ submitted_date }}</td></tr>
</table>

<p><a href="{{ approval_link }}" style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0;">
    Consulter la demande
</a></p>

<p style="margin-top: 30px; font-size: 12px; color: #666;">
    Référence: <code>{{ leave_id }}</code>
</p>
"""

TEMPLATE_LEAVE_APPROVED = """
<h2>Votre demande de congé a été approuvée ✓</h2>

<p>Bonjour {{ employee_name }},</p>

<p>Votre demande de congé a été <strong style="color: #28a745;">APPROUVÉE</strong>.</p>

<table style="margin: 20px 0; padding: 15px; background: #d4edda; border-left: 4px solid #28a745;">
    <tr><td><strong>Type:</strong></td><td>{{ leave_type }}</td></tr>
    <tr><td><strong>Période:</strong></td><td>{{ start_date }} au {{ end_date }}</td></tr>
    <tr><td><strong>Jours ouvrables:</strong></td><td>{{ business_days }}</td></tr>
    <tr><td><strong>Approuvé par:</strong></td><td>{{ manager_name }}</td></tr>
</table>

{% if comment %}
<p><strong>Commentaire:</strong></p>
<p style="padding: 10px; background: #f8f9fa; border-left: 4px solid #666;">{{ comment }}</p>
{% endif %}

<p style="margin-top: 30px; font-size: 12px; color: #666;">
    Merci d'informer votre équipe et votre client de votre absence.
</p>
"""

TEMPLATE_LEAVE_REJECTED = """
<h2>Votre demande de congé a été refusée</h2>

<p>Bonjour {{ employee_name }},</p>

<p>Votre demande de congé a été <strong style="color: #dc3545;">REFUSÉE</strong>.</p>

<table style="margin: 20px 0; padding: 15px; background: #f8d7da; border-left: 4px solid #dc3545;">
    <tr><td><strong>Type:</strong></td><td>{{ leave_type }}</td></tr>
    <tr><td><strong>Période:</strong></td><td>{{ start_date }} au {{ end_date }}</td></tr>
    <tr><td><strong>Raison du refus:</strong></td><td>{{ comment }}</td></tr>
</table>

<p>Si vous avez des questions, veuillez contacter votre responsable ou le département RH.</p>

<p style="margin-top: 30px; font-size: 12px; color: #666;">
    Référence: <code>{{ leave_id }}</code>
</p>
"""

TEMPLATE_LEAVE_REMINDER = """
<h2>Rappel: Congé à venir dans 7 jours</h2>

<p>Bonjour {{ employee_name }},</p>

<p>Ceci est un rappel que votre période de congé approche.</p>

<table style="margin: 20px 0; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107;">
    <tr><td><strong>Début:</strong></td><td><strong style="font-size: 16px;">{{ start_date }}</strong></td></tr>
    <tr><td><strong>Fin:</strong></td><td>{{ end_date }}</td></tr>
    <tr><td><strong>Jours:</strong></td><td>{{ business_days }} jour(s) ouvrable(s)</td></tr>
</table>

<p>Pensez à:</p>
<ul>
    <li>Préparer le handover avec votre équipe</li>
    <li>Clôturer vos interventions en cours</li>
    <li>Mettre à jour votre statut de disponibilité</li>
    <li>Notifier votre manager si changement</li>
</ul>

<p style="margin-top: 30px; font-size: 12px; color: #666;">
    Cet email est généré automatiquement par le système RH.
</p>
"""

TEMPLATE_TEAM_ALERT = """
<h2>Alerte Planning: Multiple absences</h2>

<p>Bonjour {{ manager_name }},</p>

<p>Le {{ alert_date }}, les membres suivants seront en congé:</p>

<ul>
{% for employee in employees %}
    <li><strong>{{ employee }}</strong></li>
{% endfor %}
</ul>

<p style="color: #ffc107; font-weight: bold;">⚠️ Vérifiez que les interventions sont couvertes.</p>

<p style="margin-top: 30px; font-size: 12px; color: #666;">
    Alerte automatique du système RH.
</p>
"""

# ============================================================
# EMAIL SENDING FUNCTIONS
# ============================================================

def send_leave_request_confirmation(leave_request):
    """
    Send confirmation email to employee when leave is submitted.
    """
    try:
        technicien = leave_request.technicien
        
        html = render_template_string(
            TEMPLATE_LEAVE_REQUEST_CONFIRMATION,
            employee_name=f"{technicien.prenom} {technicien.nom}",
            leave_type=_get_leave_type_label(leave_request.type),
            start_date=_format_date(leave_request.date_debut),
            end_date=_format_date(leave_request.date_fin),
            business_days=int(leave_request.business_days_count),
            reason=leave_request.reason or '-',
            leave_id=leave_request.id
        )
        
        msg = Message(
            subject=f"Demande de congé - Référence {leave_request.id}",
            recipients=[technicien.email],
            html=html,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'rh@sofatelcom.com')
        )
        
        current_app.extensions['mail'].send(msg)
        logger.info(f"Confirmation email sent to {technicien.email} for leave {leave_request.id}")
        
    except Exception as e:
        logger.error(f"Failed to send leave confirmation email: {str(e)}")


def send_leave_manager_notification(leave_request, manager):
    """
    Send notification to manager when new leave is pending.
    """
    try:
        technicien = leave_request.technicien
        
        # Generate approval link (you may need to adjust URL)
        approval_link = f"http://sofatelcom.local/dashboard/rh?leave_id={leave_request.id}"
        
        html = render_template_string(
            TEMPLATE_LEAVE_REQUEST_NOTIFICATION,
            manager_name=f"{manager.prenom} {manager.nom}",
            employee_name=f"{technicien.prenom} {technicien.nom}",
            leave_type=_get_leave_type_label(leave_request.type),
            start_date=_format_date(leave_request.date_debut),
            end_date=_format_date(leave_request.date_fin),
            business_days=int(leave_request.business_days_count),
            reason=leave_request.reason or '-',
            submitted_date=_format_date(leave_request.created_at),
            approval_link=approval_link,
            leave_id=leave_request.id
        )
        
        msg = Message(
            subject=f"[À VALIDER] Demande de congé de {technicien.prenom} {technicien.nom}",
            recipients=[manager.email],
            html=html,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'rh@sofatelcom.com')
        )
        
        current_app.extensions['mail'].send(msg)
        logger.info(f"Manager notification sent to {manager.email} for leave {leave_request.id}")
        
    except Exception as e:
        logger.error(f"Failed to send manager notification: {str(e)}")


def send_leave_decision_email(leave_request, decision, comment=''):
    """
    Send decision email to employee (approved/rejected).
    """
    try:
        technicien = leave_request.technicien
        
        if decision == 'approved':
            template = TEMPLATE_LEAVE_APPROVED
            subject = "Demande de congé approuvée ✓"
        else:
            template = TEMPLATE_LEAVE_REJECTED
            subject = "Demande de congé refusée"
        
        manager_name = 'Votre responsable'
        if leave_request.manager:
            manager_name = f"{leave_request.manager.prenom} {leave_request.manager.nom}"
        
        html = render_template_string(
            template,
            employee_name=f"{technicien.prenom} {technicien.nom}",
            leave_type=_get_leave_type_label(leave_request.type),
            start_date=_format_date(leave_request.date_debut),
            end_date=_format_date(leave_request.date_fin),
            business_days=int(leave_request.business_days_count),
            manager_name=manager_name,
            comment=comment,
            leave_id=leave_request.id
        )
        
        msg = Message(
            subject=subject,
            recipients=[technicien.email],
            html=html,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'rh@sofatelcom.com')
        )
        
        current_app.extensions['mail'].send(msg)
        logger.info(f"Decision email ({decision}) sent to {technicien.email} for leave {leave_request.id}")
        
    except Exception as e:
        logger.error(f"Failed to send decision email: {str(e)}")


def send_leave_reminder(leave_request):
    """
    Send 7-day reminder to employee before leave starts.
    """
    try:
        technicien = leave_request.technicien
        
        html = render_template_string(
            TEMPLATE_LEAVE_REMINDER,
            employee_name=f"{technicien.prenom} {technicien.nom}",
            start_date=_format_date(leave_request.date_debut),
            end_date=_format_date(leave_request.date_fin),
            business_days=int(leave_request.business_days_count)
        )
        
        msg = Message(
            subject=f"Rappel: Congé à venir ({_format_date(leave_request.date_debut)})",
            recipients=[technicien.email],
            html=html,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'rh@sofatelcom.com')
        )
        
        current_app.extensions['mail'].send(msg)
        logger.info(f"Reminder email sent to {technicien.email} for leave {leave_request.id}")
        
    except Exception as e:
        logger.error(f"Failed to send reminder email: {str(e)}")


def send_team_alert_email(manager, alert_date, employees):
    """
    Send alert to manager when multiple team members are absent.
    """
    try:
        html = render_template_string(
            TEMPLATE_TEAM_ALERT,
            manager_name=f"{manager.prenom} {manager.nom}",
            alert_date=_format_date(alert_date),
            employees=employees
        )
        
        msg = Message(
            subject=f"Alerte Planning: Multiple absences le {_format_date(alert_date)}",
            recipients=[manager.email],
            html=html,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'rh@sofatelcom.com')
        )
        
        current_app.extensions['mail'].send(msg)
        logger.info(f"Team alert sent to {manager.email}")
        
    except Exception as e:
        logger.error(f"Failed to send team alert: {str(e)}")


def send_emergency_cancellation_email(leave_request, reason):
    """
    Send emergency cancellation notification to employee.
    """
    try:
        technicien = leave_request.technicien
        
        html = f"""
        <h2>Annulation d'urgence: Votre congé a été annulé</h2>
        
        <p>Bonjour {technicien.prenom} {technicien.nom},</p>
        
        <p style="color: #dc3545; font-weight: bold;">Votre demande de congé approuvée a été annulée d'urgence.</p>
        
        <table style="margin: 20px 0; padding: 15px; background: #f8d7da; border-left: 4px solid #dc3545;">
            <tr><td><strong>Période:</strong></td><td>{_format_date(leave_request.date_debut)} au {_format_date(leave_request.date_fin)}</td></tr>
            <tr><td><strong>Raison:</strong></td><td>{reason}</td></tr>
        </table>
        
        <p>Contactez immédiatement votre manager pour plus d'informations.</p>
        """
        
        msg = Message(
            subject="URGENT: Annulation de congé",
            recipients=[technicien.email],
            html=html,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'rh@sofatelcom.com')
        )
        
        current_app.extensions['mail'].send(msg)
        logger.info(f"Emergency cancellation email sent to {technicien.email}")
        
    except Exception as e:
        logger.error(f"Failed to send emergency cancellation email: {str(e)}")


# ============================================================
# SCHEDULED TASKS (APScheduler)
# ============================================================

def schedule_leave_reminders():
    """
    Schedule 7-day leave reminders using APScheduler.
    Call this during app initialization.
    """
    from extensions import scheduler
    
    try:
        scheduler.add_job(
            func=_send_scheduled_reminders,
            trigger='cron',
            hour=8,
            minute=0,
            id='send_leave_reminders',
            name='Send 7-day leave reminders',
            replace_existing=True
        )
        logger.info("Scheduled leave reminders task registered")
    except Exception as e:
        logger.error(f"Failed to schedule leave reminders: {str(e)}")


def _send_scheduled_reminders():
    """
    Internal function to send reminders for leaves starting in 7 days.
    """
    from models import LeaveRequest
    from datetime import datetime, timedelta
    
    target_date = datetime.utcnow().date() + timedelta(days=7)
    
    upcoming_leaves = LeaveRequest.query.filter(
        LeaveRequest.date_debut == target_date,
        LeaveRequest.statut == 'approved'
    ).all()
    
    for leave in upcoming_leaves:
        send_leave_reminder(leave)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def _get_leave_type_label(leave_type):
    """Get human-readable leave type label."""
    labels = {
        'conge_paye': 'Congés payés',
        'maladie': 'Maladie',
        'absence': 'Absence justifiée',
        'conge_sans_solde': 'Congé sans solde',
        'rtt': 'RTT'
    }
    return labels.get(leave_type, leave_type)


def _format_date(date_obj):
    """Format date for email display (French locale)."""
    if not date_obj:
        return '-'
    if hasattr(date_obj, 'date'):  # datetime object
        date_obj = date_obj.date()
    return date_obj.strftime('%d/%m/%Y')
