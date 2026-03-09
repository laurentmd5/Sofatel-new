"""
STEP 2: DASHBOARD KPI WEB ROUTE
IMPLEMENTATION GUIDE FOR SOFATELCOM
Created: January 22, 2026

This code creates the missing /dashboard/kpi route that displays the KPI dashboard.

✅ READY TO ADD TO: routes.py (after line 100, near other @app.route('/dashboard...'))
✅ NEW ROUTE: /dashboard/kpi
✅ NEW ACCESS: Chef PUR + Admin only
✅ USES: dashboard_kpi.html template (already exists, 719 lines)
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db, app
from models import User
from kpi_models import KpiScore, KpiAlerte
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ROUTE: /dashboard/kpi
# ============================================================================

@app.route('/dashboard/kpi')
@login_required
def dashboard_kpi_web():
    """
    Dashboard KPI Web - Vue principale des scores KPI
    
    ✅ ACCESS CONTROL: Chef PUR, Admin only
    ✅ PARAMETERS:
        - period: 'day', 'week', 'month', 'year' (default: month)
        - sort: 'score', 'tendance', 'anomalie' (default: score)
    ✅ TEMPLATE: dashboard_kpi.html (719 lines, already created)
    
    Returns:
        Renders dashboard_kpi.html with KPI data, alerts, statistics
    """
    
    # ===== STEP 1: ACCESS CONTROL =====
    if current_user.role not in ['chef_pur', 'admin']:
        flash('🔒 Accès refusé: Seuls Chef PUR et Admin peuvent accéder au KPI', 'danger')
        return redirect(url_for('dashboard'))
    
    logger.info(f"[KPI Dashboard] Accès par {current_user.username} ({current_user.role})")
    
    # ===== STEP 2: GET QUERY PARAMETERS =====
    period = request.args.get('period', 'month')  # day, week, month, year
    sort_by = request.args.get('sort', 'score')   # score, tendance, anomalie
    
    # Validate parameters
    valid_periods = ['day', 'week', 'month', 'year']
    valid_sorts = ['score', 'tendance', 'anomalie']
    
    if period not in valid_periods:
        period = 'month'
    if sort_by not in valid_sorts:
        sort_by = 'score'
    
    logger.info(f"[KPI Dashboard] Period: {period}, Sort: {sort_by}")
    
    # ===== STEP 3: DETERMINE DATE RANGE =====
    today = date.today()
    
    if period == 'day':
        period_start = today
    elif period == 'week':
        period_start = today - timedelta(days=7)
    elif period == 'month':
        period_start = today - relativedelta(months=1)
    else:  # year
        period_start = today - relativedelta(years=1)
    
    logger.info(f"[KPI Dashboard] Date range: {period_start} to {today}")
    
    # ===== STEP 4: FETCH KPI SCORES =====
    try:
        # Get KPI scores for period
        query = KpiScore.query.filter(
            KpiScore.periode_fin >= period_start,
            KpiScore.periode_fin <= today,
            KpiScore.score_total != None
        )
        
        # ===== STEP 5: APPLY SORTING =====
        if sort_by == 'tendance':
            # Sort by trend (up/down/stable)
            query = query.order_by(KpiScore.tendance.desc())
        elif sort_by == 'anomalie':
            # Sort by anomalies (most critical first)
            query = query.order_by(KpiScore.anomalie_detectee.desc())
        else:  # sort_by == 'score' (default)
            # Sort by score descending
            query = query.order_by(KpiScore.score_total.desc())
        
        # Limit to top 100 scores
        scores = query.limit(100).all()
        
        logger.info(f"[KPI Dashboard] Found {len(scores)} scores")
        
    except Exception as e:
        logger.error(f"[KPI Dashboard] Error fetching scores: {str(e)}", exc_info=True)
        flash(f'❌ Erreur lors du chargement des scores KPI: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    
    # ===== STEP 6: FETCH ACTIVE ALERTS =====
    try:
        # Get unresolved alerts (critical for proactive management)
        active_alerts = KpiAlerte.query.filter(
            KpiAlerte.date_resolution == None
        ).order_by(KpiAlerte.date_creation.desc()).all()
        
        logger.info(f"[KPI Dashboard] Found {len(active_alerts)} active alerts")
        
    except Exception as e:
        logger.error(f"[KPI Dashboard] Error fetching alerts: {str(e)}", exc_info=True)
        active_alerts = []
    
    # ===== STEP 7: CALCULATE STATISTICS =====
    try:
        total_scores = len(scores)
        
        if scores:
            avg_score = sum(s.score_total for s in scores) / total_scores
            min_score = min(s.score_total for s in scores)
            max_score = max(s.score_total for s in scores)
        else:
            avg_score = 0
            min_score = 0
            max_score = 0
        
        # Count anomalies
        anomalies_count = len([s for s in scores if s.anomalie_detectee])
        
        alerts_count = len(active_alerts)
        
        # Build statistics dictionary
        statistics = {
            'total_scores': total_scores,
            'avg_score': round(avg_score, 2),
            'min_score': round(min_score, 2),
            'max_score': round(max_score, 2),
            'anomalies_count': anomalies_count,
            'alerts_count': alerts_count
        }
        
        logger.info(f"[KPI Dashboard] Statistics: {statistics}")
        
    except Exception as e:
        logger.error(f"[KPI Dashboard] Error calculating statistics: {str(e)}", exc_info=True)
        statistics = {
            'total_scores': 0,
            'avg_score': 0,
            'min_score': 0,
            'max_score': 0,
            'anomalies_count': 0,
            'alerts_count': 0
        }
    
    # ===== STEP 8: PREPARE TEMPLATE DATA =====
    template_data = {
        # KPI Scores
        'scores': scores,
        
        # Alerts
        'active_alerts': active_alerts,
        
        # Period info
        'period': period,
        'period_start': period_start.isoformat(),
        'period_end': today.isoformat(),
        'period_display': {
            'day': 'Aujourd\'hui',
            'week': 'Cette semaine (7 derniers jours)',
            'month': 'Ce mois (30 derniers jours)',
            'year': 'Cette année (365 derniers jours)'
        }.get(period, 'Custom'),
        
        # Sort info
        'sort_by': sort_by,
        'sort_display': {
            'score': 'Score (décroissant)',
            'tendance': 'Tendance',
            'anomalie': 'Anomalies détectées'
        }.get(sort_by, 'Score'),
        
        # Statistics
        'total_scores': statistics['total_scores'],
        'avg_score': statistics['avg_score'],
        'min_score': statistics['min_score'],
        'max_score': statistics['max_score'],
        'anomalies_count': statistics['anomalies_count'],
        'alerts_count': statistics['alerts_count'],
        
        # User info
        'current_user': current_user
    }
    
    logger.info(f"[KPI Dashboard] Rendering with {len(scores)} scores, {len(active_alerts)} alerts")
    
    # ===== STEP 9: RENDER TEMPLATE =====
    return render_template('dashboard_kpi.html', **template_data)


# ============================================================================
# HELPER ROUTE: /dashboard/kpi/export (Optional, can add later)
# ============================================================================

@app.route('/dashboard/kpi/export')
@login_required
def dashboard_kpi_export():
    """
    Export KPI scores to CSV
    ✅ Query params: format='csv' (default) or 'json'
    ✅ Returns: CSV file download
    """
    from io import BytesIO, StringIO
    import csv
    from flask import send_file
    
    # Access control
    if current_user.role not in ['chef_pur', 'admin']:
        return {'error': 'Access denied'}, 403
    
    format_type = request.args.get('format', 'csv')
    period = request.args.get('period', 'month')
    
    # Determine date range
    today = date.today()
    if period == 'month':
        period_start = today - relativedelta(months=1)
    elif period == 'year':
        period_start = today - relativedelta(years=1)
    else:
        period_start = today - timedelta(days=7)  # default week
    
    # Fetch scores
    scores = KpiScore.query.filter(
        KpiScore.periode_fin >= period_start,
        KpiScore.periode_fin <= today,
        KpiScore.score_total != None
    ).order_by(KpiScore.score_total.desc()).all()
    
    if format_type == 'json':
        # JSON export
        from flask import jsonify
        data = [s.to_dict() for s in scores]
        return jsonify({'success': True, 'count': len(data), 'data': data})
    
    # CSV export
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Technicien', 'Équipe', 'Période',
        'Score Total', 'Résolution 1ère visite', 'SLA', 'Qualité', 'Satisfaction', 'Stock',
        'Rang Équipe', 'Rang Global', 'Tendance', 'Variation', 'Alerte'
    ])
    
    # Rows
    for score in scores:
        writer.writerow([
            f"{score.technicien.prenom} {score.technicien.nom}",
            score.equipe.nom_equipe if score.equipe else 'N/A',
            f"{score.periode_debut.isoformat()} à {score.periode_fin.isoformat()}",
            score.score_total,
            score.score_resolution_1ere_visite,
            score.score_respect_sla,
            score.score_qualite_rapports,
            score.score_satisfaction_client,
            score.score_consommation_stock,
            score.rang_equipe,
            score.rang_global,
            score.tendance,
            score.variation_periode_precedente,
            score.alerte_active
        ])
    
    # Return as download
    output.seek(0)
    mem = BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"kpi_export_{today.isoformat()}.csv"
    )


# ============================================================================
# ✅ IMPLEMENTATION CHECKLIST
# ============================================================================
"""
STEP 1: ADD TO routes.py
- [ ] Copy the @app.route('/dashboard/kpi') function
- [ ] Paste after line 100 (near other @app.route('/dashboard...'))
- [ ] Keep imports at top

STEP 2: VERIFY IMPORTS
In routes.py header, ensure these exist:
- [ ] from datetime import date, timedelta
- [ ] from dateutil.relativedelta import relativedelta
- [ ] from kpi_models import KpiScore, KpiAlerte

STEP 3: TEST LOCAL
- [ ] flask run --host=0.0.0.0
- [ ] Go to: http://localhost:5000/dashboard/kpi
- [ ] Should see dashboard_kpi.html template with KPI data

STEP 4: TEST PARAMETERS
- [ ] ?period=day → Show today's scores
- [ ] ?period=week → Show 7 days
- [ ] ?period=month → Show 30 days
- [ ] ?sort=tendance → Sort by trend
- [ ] ?sort=anomalie → Sort by anomalies

STEP 5: TEST ALERTS
- [ ] Should display KpiAlerte items
- [ ] Should show count of active alerts
- [ ] Should show anomalies detected

STEP 6: DEPLOY
- [ ] Test on staging
- [ ] Monitor logs for errors
- [ ] Deploy to production
"""

# ============================================================================
# ✅ QUICK REFERENCE - URL PATTERNS
# ============================================================================
"""
Available URLs after implementation:

BASE:
  GET /dashboard/kpi
  → Shows KPI dashboard (default: 1 month, sorted by score)

WITH PERIODS:
  GET /dashboard/kpi?period=day
  GET /dashboard/kpi?period=week
  GET /dashboard/kpi?period=month
  GET /dashboard/kpi?period=year

WITH SORTING:
  GET /dashboard/kpi?sort=score
  GET /dashboard/kpi?sort=tendance
  GET /dashboard/kpi?sort=anomalie

COMBINED:
  GET /dashboard/kpi?period=year&sort=anomalie
  → Show 1 year of scores, sorted by anomalies first

EXPORT:
  GET /dashboard/kpi/export?format=csv&period=month
  → Download CSV with scores
  
  GET /dashboard/kpi/export?format=json&period=year
  → Get JSON data (API compatible)
"""

# ============================================================================
# ✅ TROUBLESHOOTING
# ============================================================================
"""
Problem: "404 - Route not found"
Solution: 
  1. Ensure route is added to routes.py
  2. Restart Flask: Ctrl+C then flask run

Problem: "Template not found - dashboard_kpi.html"
Solution:
  ✅ Template already exists at: templates/dashboard_kpi.html (719 lines)
  
Problem: "No KPI data showing"
Solution:
  1. Check if KpiScore table has data: 
     sqlite> SELECT COUNT(*) FROM kpi_score;
  2. If empty, trigger KPI calculation first:
     GET /api/kpi/calculate
  3. Or populate test data

Problem: "AlertError - KpiAlerte not found"
Solution:
  ✅ Table is optional - errors are caught and alerts_count = 0
  
Problem: "Performance slow loading"
Solution:
  1. Add index on kpi_score (periode_fin, score_total)
  2. Implement Redis caching (see OPTIMIZATION section)
  3. Limit to top 100 scores (already done)
"""
