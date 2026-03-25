from app import app, db
from models import EmplacementStock, Zone

with app.app_context():
    print("--- Checking and fixing Emplacements ---")
    zones = Zone.query.all()
    zone_map = {z.nom.upper(): z.id for z in zones}
    print(f"Zones available: {zone_map}")
    
    # Common mappings
    mappings = {
        'DAKAR': 'ZONE1',
        'MBOUR': 'ZONE2',
        'KAOLACK': 'ZONE3',
        'FATICK': 'ZONE4'
    }
    
    for zone_name, emp_code in mappings.items():
        if zone_name in zone_map:
            z_id = zone_map[zone_name]
            emp = EmplacementStock.query.filter_by(code=emp_code).first()
            if emp:
                if emp.zone_id != z_id:
                    print(f"Linking {emp_code} to zone {zone_name} (ID {z_id})")
                    emp.zone_id = z_id
                else:
                    print(f"{emp_code} already linked to {zone_name}")
            else:
                print(f"Emplacement {emp_code} not found")
        else:
            print(f"Zone {zone_name} not found in DB")
            
    # Also link any that have "Dakar", "Mbour", etc in designation
    for emp in EmplacementStock.query.filter(EmplacementStock.zone_id == None).all():
        for zone_name, z_id in zone_map.items():
            if zone_name.upper() in emp.designation.upper() or zone_name.upper() in emp.code.upper():
                print(f"Auto-linking {emp.code} ({emp.designation}) to zone {zone_name} (ID {z_id})")
                emp.zone_id = z_id
                break
                
    db.session.commit()
    print("Done.")
