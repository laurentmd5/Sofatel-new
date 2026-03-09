import sys
sys.path.insert(0, '.')

from app import app, db
from models import User, Equipe, Zone
from datetime import date

with app.app_context():
    chef_zone = User.query.filter_by(role='chef_zone').first()
    print(f'Chef zone: {chef_zone.username} id={chef_zone.id}, zone="{chef_zone.zone}"')

    # list zones in DB
    for z in Zone.query.all():
        print(f'Zone in DB: {z.nom} ({z.code})')

    # create new teams with simple and formatted zones
    t1 = Equipe(nom_equipe='Test Simple', date_creation=date.today(), chef_zone_id=chef_zone.id,
                zone='Dakar', technologies='Fibre', service='SAV', prestataire='X', actif=True, publie=False)
    t2 = Equipe(nom_equipe='Test Formatted', date_creation=date.today(), chef_zone_id=chef_zone.id,
                zone='Dakar (DK)', technologies='Fibre', service='SAV', prestataire='X', actif=True, publie=False)
    db.session.add_all([t1, t2])
    db.session.commit()
    print('Created teams:', t1.zone, t2.zone)

    # test filtering
    user_zone = chef_zone.zone
    print('user_zone:', user_zone)
    teams = Equipe.query.filter_by(chef_zone_id=chef_zone.id, zone=user_zone, actif=True).all()
    print('teams with zone simple:', [t.nom_equipe for t in teams])
    # formatted attempt
    zone_obj = Zone.query.filter_by(nom=user_zone).first()
    if zone_obj:
        uzf = f'{zone_obj.nom} ({zone_obj.code})'
        teams2 = Equipe.query.filter_by(chef_zone_id=chef_zone.id, zone=uzf, actif=True).all()
        print('teams with zone formatted', uzf, [t.nom_equipe for t in teams2])

    # publish the teams and test again
    for t in [t1, t2]:
        t.publie = True
        t.date_publication = date.today()
    db.session.commit()
    print('Published both test teams')

    # simulate get_equipes_jour filter (today)
    uz = user_zone
    uzf2 = uzf if zone_obj else None
    eqs = Equipe.query.filter_by(chef_zone_id=chef_zone.id, zone=uz, publie=True, date_publication=date.today(), actif=True).all()
    print('eqs simple filter after publish', [e.nom_equipe for e in eqs])
    if uzf2 and uzf2 != uz:
        eqs_form = Equipe.query.filter_by(chef_zone_id=chef_zone.id, zone=uzf2, publie=True, date_publication=date.today(), actif=True).all()
        print('eqs formatted filter after publish', [e.nom_equipe for e in eqs_form])
