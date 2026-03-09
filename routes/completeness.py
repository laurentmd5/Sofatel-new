from flask import Blueprint, jsonify, request, abort
from completeness_utils import compute_intervention_completeness, average_completeness_for_date
from models import Intervention

bp = Blueprint('completeness', __name__)


@bp.route('/api/intervention/<int:intervention_id>/completude', methods=['GET'])
def intervention_completude(intervention_id):
    it = Intervention.query.get(intervention_id)
    if not it:
        abort(404, 'Intervention not found')
    return jsonify(compute_intervention_completeness(it))


@bp.route('/api/interventions/completude', methods=['GET'])
def interventions_completude():
    date = request.args.get('date')
    if not date:
        abort(400, 'date parameter required (YYYY-MM-DD)')
    res = average_completeness_for_date(date)
    return jsonify(res)
