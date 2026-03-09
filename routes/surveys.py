"""
Module surveys — gestion des surveys (formulaires de visite client).
Routes : /survey/create, /surveys, /survey/<id>, /uploads/<filename>
"""

import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app, send_from_directory, Blueprint
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from forms import SurveyForm
from models import Survey
from utils import log_activity
from extensions import csrf


surveys_bp = Blueprint('surveys', __name__)


@surveys_bp.route('/survey/create', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def create_survey():
    form = SurveyForm()
    if form.validate_on_submit():
        survey = Survey()

        # Remplir les champs du survey à partir du formulaire
        for field in form:
            if field.name != 'csrf_token' and field.name not in [
                    'photo_batiment', 'photo_environ'
            ]:
                setattr(survey, field.name, field.data)

        # Traiter les photos
        if form.photo_batiment.data:
            filename = secure_filename(
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}_batiment.jpg")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                    filename)
            form.photo_batiment.data.save(filepath)
            survey.photo_batiment = filename

        if form.photo_environ.data:
            filename = secure_filename(
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}_environ.jpg")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                    filename)
            form.photo_environ.data.save(filepath)
            survey.photo_environ = filename

        # Ajouter le technicien
        survey.technicien_id = current_user.id

        try:
            db.session.add(survey)
            db.session.commit()
            log_activity(
                user_id=current_user.id,
                action='create',
                module='surveys',
                entity_id=survey.id,
                entity_name=f"Survey {survey.n_demande}",
                details={
                    'client': f"{survey.nom_raison_sociale}",
                    'technicien': f"{current_user.prenom} {current_user.nom}",
                    'service_demande': survey.service_demande
                }
            )
            flash('Survey enregistré avec succès', 'success')
            return redirect(url_for('list_surveys'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'enregistrement du survey: {str(e)}',
                  'error')

    return render_template('survey_form.html', form=form)


@surveys_bp.route('/surveys')
@login_required
def list_surveys():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 25, type=int), 100)

    if current_user.role == 'technicien':
        query = Survey.query.filter_by(technicien_id=current_user.id).order_by(
            Survey.date_creation.desc())
    else:
        query = Survey.query.order_by(Survey.date_creation.desc())

    surveys = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('surveys.html', surveys=surveys)


@surveys_bp.route('/survey/<int:id>')
@login_required
def view_survey(id):
    survey = db.session.get(Survey, id)
    if not survey:
        abort(404)
    return render_template('survey_detail.html', survey=survey)


@surveys_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
