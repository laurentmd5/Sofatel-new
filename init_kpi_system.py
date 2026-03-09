"""
KPI System Initialization Script

Initialize default KPI metrics and sample technician objectives
Run this after creating the database tables
"""

from datetime import datetime, date
from extensions import db
from kpi_models import KpiMetric, KpiObjectif
from models import User
import json


def init_kpi_metrics():
    """Initialize the 5 default KPI metrics"""
    
    metrics = [
        {
            'nom': 'Résolution 1ère visite',
            'description': 'Taux de résolution au premier passage du technicien',
            'poids': 0.30,
            'seuil_min': 0,
            'seuil_max': 100,
            'seuil_alerte': 75,
            'formule': '(resolved_first_visit / total_interventions) * 100',
            'unite': '%'
        },
        {
            'nom': 'Respect SLA',
            'description': 'Respect des délais de service convenus',
            'poids': 0.25,
            'seuil_min': 0,
            'seuil_max': 100,
            'seuil_alerte': 90,
            'formule': '(interventions_in_sla / total_interventions) * 100',
            'unite': '%'
        },
        {
            'nom': 'Qualité des rapports',
            'description': 'Qualité et complétude des rapports d\'intervention',
            'poids': 0.20,
            'seuil_min': 0,
            'seuil_max': 100,
            'seuil_alerte': 80,
            'formule': '(quality_ok_reports / total_interventions) * 100',
            'unite': '%'
        },
        {
            'nom': 'Satisfaction client',
            'description': 'Évaluation de satisfaction client pour les interventions',
            'poids': 0.15,
            'seuil_min': 0,
            'seuil_max': 100,
            'seuil_alerte': 75,
            'formule': 'average(client_satisfaction_ratings) / 5.0 * 100',
            'unite': '%'
        },
        {
            'nom': 'Consommation stock',
            'description': 'Maîtrise de la consommation de pièces vs budget',
            'poids': 0.10,
            'seuil_min': 0,
            'seuil_max': 100,
            'seuil_alerte': 80,
            'formule': '100 if total_cost <= budget else 100 - min(50, (overage/budget)*100)',
            'unite': '%'
        }
    ]
    
    for metric_data in metrics:
        # Check if metric already exists
        existing = KpiMetric.query.filter_by(nom=metric_data['nom']).first()
        if not existing:
            metric = KpiMetric(
                nom=metric_data['nom'],
                description=metric_data['description'],
                poids=metric_data['poids'],
                seuil_min=metric_data['seuil_min'],
                seuil_max=metric_data['seuil_max'],
                seuil_alerte=metric_data['seuil_alerte'],
                formule=metric_data['formule'],
                unite=metric_data['unite'],
                date_creation=datetime.now()
            )
            db.session.add(metric)
            print(f"✓ Created metric: {metric_data['nom']}")
        else:
            print(f"→ Metric already exists: {metric_data['nom']}")
    
    db.session.commit()
    print("\n✓ KPI Metrics initialized successfully")


def init_technician_objectives(year=None):
    """Initialize default objectives for all technicians"""
    
    if year is None:
        year = datetime.now().year
    
    # Default objectives
    default_objectives = {
        'objectif_resolution_1ere_visite': 80,
        'objectif_respect_sla': 95,
        'objectif_qualite_rapports': 85,
        'objectif_satisfaction_client': 80,
        'objectif_consommation_stock': 80
    }
    
    # Get all active technicians
    technicians = User.query.filter_by(role='technicien', actif=True).all()
    
    count_created = 0
    count_existing = 0
    
    for tech in technicians:
        # Check if objectives already exist for this year
        existing = KpiObjectif.query.filter_by(
            technicien_id=tech.id,
            annee=year
        ).first()
        
        if not existing:
            objectif = KpiObjectif(
                technicien_id=tech.id,
                annee=year,
                objectif_resolution_1ere_visite=default_objectives['objectif_resolution_1ere_visite'],
                objectif_respect_sla=default_objectives['objectif_respect_sla'],
                objectif_qualite_rapports=default_objectives['objectif_qualite_rapports'],
                objectif_satisfaction_client=default_objectives['objectif_satisfaction_client'],
                objectif_consommation_stock=default_objectives['objectif_consommation_stock'],
                date_debut=date(year, 1, 1),
                date_fin=date(year, 12, 31),
                date_creation=datetime.now()
            )
            db.session.add(objectif)
            count_created += 1
        else:
            count_existing += 1
    
    db.session.commit()
    
    print(f"\n✓ Technician objectives initialized for {year}")
    print(f"  - Created: {count_created}")
    print(f"  - Already existing: {count_existing}")


def print_summary():
    """Print initialization summary"""
    
    metrics_count = KpiMetric.query.count()
    objectives_count = KpiObjectif.query.count()
    
    print("\n" + "="*50)
    print("KPI SYSTEM INITIALIZATION SUMMARY")
    print("="*50)
    print(f"Metrics configured: {metrics_count}/5")
    print(f"Technician objectives: {objectives_count}")
    
    if metrics_count == 5:
        print("\n✓ Metrics are properly configured")
        # Show metrics
        metrics = KpiMetric.query.all()
        for metric in metrics:
            print(f"  • {metric.nom} ({metric.poids*100:.0f}% weight, threshold: {metric.seuil_alerte})")
    else:
        print("\n✗ Metrics initialization incomplete")
    
    print("\n" + "="*50)


if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        print("Initializing KPI System...")
        print("-" * 50)
        
        try:
            init_kpi_metrics()
            init_technician_objectives()
            print_summary()
            print("\n✓ KPI System initialization complete!")
        except Exception as e:
            print(f"\n✗ Error during initialization: {e}")
            import traceback
            traceback.print_exc()
