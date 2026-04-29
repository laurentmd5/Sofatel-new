import os
import pandas as pd
from datetime import date, datetime, timedelta
from app import db
from models import *
from flask_mail import Message as MailMessage
from flask import current_app, request
import json
from sqlalchemy import case, not_, func, or_, and_


def determine_file_type(df_columns):
    """Détermine si le fichier est de type SAV ou Production en fonction des colonnes"""
    sav_columns = {'ND', 'ZONE', 'PRIORITE DE TRAITEMENT', 'ORIGINE'}
    prod_columns = {
        'ND', 'OLT', 'DEMANDE', 'COMMANDECLIENT', 'NOMDUCLIENT', 'CONTACTCLIENT',
        'NOM DU CLIENT', 'CONTACT CLIENT', 'DATE VALIDATION', "DATE D'INTERVENTION", 'TÂCHES'
    }
    
    sav_count = len(sav_columns.intersection(df_columns))
    prod_count = len(prod_columns.intersection(df_columns))
    
    if prod_count > sav_count:
        return 'production'
    return 'sav'

def process_excel_file(filepath, service, importe_par):
    """Traite un fichier Excel et importe les demandes d'intervention SAV"""
    try:
        # Créer l'enregistrement d'import
        fichier_import = FichierImport(
            nom_fichier=filepath.split('/')[-1],
            importe_par=importe_par,
            statut='en_cours',
            service=service  # Ajout du service
        )
        db.session.add(fichier_import)
        db.session.flush()
        
        # Lire le fichier Excel
        df = pd.read_excel(filepath)
        df.columns = [str(col).strip().upper().replace('\xa0', '').replace('\u200b', '') for col in df.columns]
        df = df.dropna(how='all')
        
        # Vérifier le type de fichier
        file_type = determine_file_type(set(df.columns))
        
        if file_type == 'production':
            return process_excel_file_production(filepath, service, importe_par, fichier_import, df)
        
        # Pour chaque champ attendu, liste des variantes possibles pour SAV
        expected_columns = {
            'nd': ['ND'],
            'zone': ['ZONE', 'OLT', 'REPART'],
            'priorite_traitement': ['PRIORITE DE TRAITEMENT'],
            'origine': ['ORIGINE'],
            'offre': ['OFFRE', 'Offre'],
            'type_techno': ['TYPE'],
            'segment': ['SEGMENT', 'Segment'],
            'produit': ['PRODUIT'],
            'age': ['AGE'],
            'nom_client': ['NOM_DU_CLIENT', 'NomduClient', 'NOM UTILISATEUR', 'NOMDUCLIENT'],
            'prenom_client': ['PRENOM_DU_CLIENT', 'PrenomduClient'],
            'contact_client': ['CONTACT_CLIENT', 'Contactclient', 'CONTACTCLIENT', 'CONTACT_MOB'],
            'commentaire_contact': ['COMMENTAIRE_CONTACT'],
            'rep_srp': ['REP-SRP'],
            'constitution': ['CONSTITUTION'],
            'specialite': ['SPECIALITE_CHOISIE'],
            'resultat_essai': ['RESULT_ESS'],
            'commentaire_essai': ['COMMENTAIRE_ESSAI'],
            'agent_essai': ['AGENT_ESS'],
            'date_demande_intervention': ['DATE_DEMANDE_INT', "DATED'INTERVENTION"],
            'commentaire_interv': ['COMMENTAIRE_INTERV'],
            'id_ot': ['ID_OT'],
            'zone_rs': ['ZONE_RS'],
            'id_drgt': ['ID_DRGT'],
            'libel_sig': ['LIBEL_SIG'],
            'date_sig': ['DATE_SIG'],
            'compteur': ['COMPTEUR'],
            'libelle_commune': ['LIBELLE_COMMUNE', 'ADRESSE'],
            'libelle_quartier': ['LIBELLE_QUARTIER', 'Adresse', 'ADRESSE_INSTALL'],
            'demande': ['DEMANDE', 'Demande'],
            'taches': ['TACHE', 'Tâches', 'TACHES'],
            'st': ['ST'],
            'equipe': ['EQUIPE', 'EQUIPES', 'EQUI', 'PILOTE', 'NOM EQUIPE']
        }
        
        # Construction du mapping dynamique
        rename_dict = {}
        for standard_col, variants in expected_columns.items():
            found = False
            for variant in variants:
                if variant in df.columns:
                    rename_dict[variant] = standard_col
                    found = True
                    print(f"Colonne trouvée: {variant} -> {standard_col}")
                    break
            if not found:
                print(f"Attention: Colonne non trouvée pour {standard_col}")
        # Renommer les colonnes selon le mapping
        df = df.rename(columns=rename_dict)
        print("Colonnes du fichier après renommage :", df.columns.tolist())
        
        nb_lignes = 0
        nb_erreurs = 0
        erreurs = []
        
        # Normaliser les valeurs - MUST BE DEFINED BEFORE LOOP
        def safe_str(val):
            if pd.isna(val):
                return ''
            return str(val).strip()
        
        for index, row in df.iterrows():
            try:
                # Vérifier que les champs obligatoires sont présents
                nd_val = row.get('nd')
                nom_client_val = row.get('nom_client')
                #type_techno_val = row.get('type_techno')
                zone_val = row.get('zone')
                
                if (pd.isna(nd_val) or pd.isna(nom_client_val) or pd.isna(zone_val) or
                    not str(nd_val).strip() or not str(nom_client_val).strip() or 
                    not str(zone_val).strip()):
                    nb_erreurs += 1
                    erreurs.append(
                    f"Ligne {index+2}: ND, nom client ou zone manquant ou vide"
                    )
                    print(f"Erreur ligne {index}: ND, nom client ou zone manquant ou vide")
                    continue
                
                # 🔒 DUPLICATE PREVENTION: Check if ND already exists
                # This prevents re-importing the same intervention across multiple files
                nd_str = safe_str(row.get('nd')) if 'nd' in row else str(nd_val).strip()
                existing_demand = DemandeIntervention.query.filter_by(nd=nd_str).first()
                if existing_demand:
                    nb_erreurs += 1
                    source_file = (existing_demand.fichier_import.nom_fichier 
                                 if existing_demand.fichier_import else 'unknown')
                    erreurs.append(
                        f"Ligne {index+2}: ND '{nd_str}' already exists "
                        f"(previous import: {source_file})"
                    )
                    print(f"Erreur ligne {index}: ND '{nd_str}' already exists")
                    continue
                
                # Traitement de la date
                date_demande = row.get('date_demande_intervention')
                if pd.isna(date_demande):
                    date_demande = datetime.now()
                elif isinstance(date_demande, str):
                    try:
                        date_demande = datetime.strptime(date_demande, '%Y-%m-%d')
                    except:
                        date_demande = datetime.now()
                
                # Normaliser type_techno
                type_techno = safe_str(row.get('type_techno'))
                if type_techno == 'CUIVRE':
                    type_techno = 'Cuivre'
                elif type_techno == 'FIBRE':
                    type_techno = 'Fibre'
                elif type_techno == '5G':
                    type_techno = '5G'
                
                # Définir le prestataire en fonction du service
                prestataire = "SAV"  # Par défaut pour les imports SAV
                
                # Créer la demande d'intervention
                demande = DemandeIntervention(
                    nd=safe_str(row.get('nd')),
                    demandee=safe_str(row.get('demande')),
                    zone=safe_str(row.get('zone')).upper(),
                    priorite_traitement=safe_str(row.get('priorite_traitement')),
                    origine=safe_str(row.get('origine')),
                    offre=safe_str(row.get('offre')),
                    type_techno=type_techno,
                    produit=safe_str(row.get('produit')),
                    age=safe_str(row.get('age')),
                    nom_client=safe_str(row.get('nom_client')),
                    prenom_client=safe_str(row.get('prenom_client')),
                    rep_srp=safe_str(row.get('rep_srp')),
                    constitution=safe_str(row.get('constitution')),
                    specialite=safe_str(row.get('specialite')),
                    resultat_essai=safe_str(row.get('resultat_essai')),
                    commentaire_essai=safe_str(row.get('commentaire_essai')),
                    agent_essai=safe_str(row.get('agent_essai')),
                    date_demande_intervention=date_demande,
                    commentaire_interv=safe_str(row.get('commentaire_interv')),
                    id_ot=safe_str(row.get('id_ot')),
                    fichier_importe_id=fichier_import.id,
                    equipe=safe_str(row.get('equipe')),
                    section_id=safe_str(row.get('section_id')),
                    statut='nouveau',
                    libelle_commune=safe_str(row.get('libelle_commune')),
                    libelle_quartier=safe_str(row.get('libelle_quartier')),
                    prestataire=prestataire,  # Utilisation de la variable prestataire
                    taches=safe_str(row.get('taches')),
                    service=service,

                    contact_client=safe_str(row.get('contact_client')),
                    commentaire_contact=safe_str(row.get('commentaire_contact')),
                    zone_rs=safe_str(row.get('zone_rs')),
                    id_drgt=safe_str(row.get('id_drgt')),
                    libel_sig=safe_str(row.get('libel_sig')),
                    date_sig=row.get('date_sig'),
                    compteur=safe_str(row.get('compteur'))
                )
                
                db.session.add(demande)
                nb_lignes += 1
                
            except Exception as e:
                nb_erreurs += 1
                print(f"Erreur ligne {index}: {str(e)}")
        
        # Mettre à jour l'enregistrement d'import
        fichier_import.nb_lignes = nb_lignes
        fichier_import.nb_erreurs = nb_erreurs
        fichier_import.statut = 'termine'
        
        db.session.commit()
        
        return {
            'success': True,
            'nb_lignes': nb_lignes,
            'nb_erreurs': nb_erreurs,
            'erreurs': erreurs
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }

def process_excel_file_production(filepath, service, importe_par, fichier_import, df):
    """Traite un fichier Excel de production et importe les demandes d'intervention"""
    try:
        # Mettre à jour le service du fichier d'import
        fichier_import.service = service
        db.session.commit()
        
        # Mapping des colonnes spécifiques à la production
        expected_columns = {
            'nd': ['ND'],
            'olt': ['OLT'],
            'demande': ['DEMANDE'],
            'commande_client': ['COMMANDECLIENT', 'DEMANDE'],
            'date_validation': ['DATEVALIDATION', 'DATE VALIDATION'],
            'nom_client': ['NOMDUCLIENT', 'NOM DU CLIENT'],
            'contact_client': ['CONTACTCLIENT', 'CONTACT CLIENT'],
            'date_intervention': ["DATED'INTERVENTION", "DATE D'INTERVENTION"],
            'taches': ['TÂCHES'],
            'pilotes': ['PILOTES', 'PILOTES REGIS'],
            'adresse': ['ADRESSE'],
            'type_techno': ['TECHO'],
            'offre': ['OFFRES', 'OFFRE'],
            'equipe': ['EQUIPE', 'EQUIPES', 'EQUI', 'PILOTE', 'NOM EQUIPE', 'ST']
        }
        
        # Construction du mapping dynamique
        rename_dict = {}
        for standard_col, variants in expected_columns.items():
            for variant in variants:
                if variant in df.columns:
                    rename_dict[variant] = standard_col
                    print(f"Colonne trouvée: {variant} -> {standard_col}")
                    break
            else:
                print(f"Attention: Colonne non trouvée pour {standard_col}")
        
        # Renommer les colonnes selon le mapping
        df = df.rename(columns=rename_dict)
        print("Colonnes du fichier après renommage :", df.columns.tolist())
        
        nb_lignes = 0
        nb_erreurs = 0
        erreurs = []
        
        for index, row in df.iterrows():
            try:
                # Vérifier que les champs obligatoires sont présents
                nd_val = row.get('nd')
                nom_client_val = row.get('nom_client')
                olt_val = row.get('olt')  # Dans la production, on utilise OLT comme zone
                
                if (pd.isna(nd_val) or pd.isna(nom_client_val) or pd.isna(olt_val) or
                    not str(nd_val).strip() or not str(nom_client_val).strip() or 
                    not str(olt_val).strip()):
                    nb_erreurs += 1
                    erreurs.append(f"Ligne {index+2}: ND, nom client ou OLT manquant ou vide")
                    print(f"Erreur ligne {index}: ND, nom client ou OLT manquant ou vide")
                    continue
                
                # Traitement de la date d'intervention
                date_intervention = row.get('date_intervention')
                if pd.isna(date_intervention):
                    date_intervention = datetime.now()
                elif isinstance(date_intervention, str):
                    try:
                        date_intervention = datetime.strptime(date_intervention, '%Y-%m-%d')
                    except:
                        date_intervention = datetime.now()
                
                # Normaliser les valeurs
                def safe_str(val):
                    if pd.isna(val):
                        return ''
                    return str(val).strip()
                
                # Définir le prestataire pour la production
                prestataire = "Production"  # Pour les imports Production
                
                # Déterminer le type de technologie dynamiquement
                type_tech_val = safe_str(row.get('type_techno')).upper()
                if 'FTTH' in type_tech_val:
                    type_techno = 'Fibre'
                elif 'ADSL' in type_tech_val:
                    type_techno = 'Cuivre'
                elif '5G' in type_tech_val:
                    type_techno = '5G'
                else:
                    type_techno = 'Fibre'  # Valeur par défaut pour la production
                
                # Créer la demande d'intervention pour la production
                demande = DemandeIntervention(
                    nd=safe_str(row.get('nd')),
                    demandee=safe_str(row.get('demande') or 'Production'),
                    zone=safe_str(row.get('olt')),  # Utiliser OLT comme zone pour la production
                    type_techno=type_techno,
                    offre=safe_str(row.get('offre')),
                    nom_client=safe_str(row.get('nom_client')),
                    prenom_client='',  # Valeur par défaut vide pour la production
                    contact_client=safe_str(row.get('contact_client')),
                    date_demande_intervention=date_intervention,
                    fichier_importe_id=fichier_import.id,
                    equipe=safe_str(row.get('equipe')),
                    statut='nouveau',
                    libelle_quartier=safe_str(row.get('adresse') or row.get('libelle_quartier', '')),
                    taches=safe_str(row.get('taches')),
                    service=service,  # Utiliser le service passé en paramètre
                    prestataire=prestataire,  # Définir le prestataire
                    commande_client=safe_str(row.get('commande_client')),
                    date_validation=row.get('date_validation'),
                    heure=safe_str(row.get('heure')),
                    rbs=safe_str(row.get('rbs')),
                    pilotes=safe_str(row.get('pilotes')),
                    st=safe_str(row.get('st')),
                    ci_prcl=safe_str(row.get('ci_prcl')),
                    coordonnees_gps=safe_str(row.get('coordonnees_gps')),
                    sr=safe_str(row.get('sr')),
                    adresse=safe_str(row.get('adresse'))
                )
                
                db.session.add(demande)
                nb_lignes += 1
                
            except Exception as e:
                nb_erreurs += 1
                erreur_msg = f"Erreur ligne {index+2}: {str(e)}"
                print(erreur_msg)
                erreurs.append(erreur_msg)
        
        # Mettre à jour l'enregistrement d'import
        fichier_import.nb_lignes = nb_lignes
        fichier_import.nb_erreurs = nb_erreurs
        fichier_import.statut = 'termine'
        
        db.session.commit()
        
        return {
            'success': True,
            'nb_lignes': nb_lignes,
            'nb_erreurs': nb_erreurs,
            'erreurs': erreurs
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }

def is_technicien_compatible(technicien, demande):
    """Vérifie si un technicien est compatible avec une demande (case-insensitive)"""
    # Si la demande ne spécifie pas de technologie, on autorise l'affectation par défaut
    type_techno = str(demande.type_techno).strip().upper() if demande.type_techno else ''
    if not type_techno or type_techno in ['-', '', 'NONE']:
        return True
        
    if not technicien.technologies:
        return False
    
    technologies_technicien = [t.strip().upper() for t in str(technicien.technologies).split(',')]
    return type_techno in technologies_technicien

def find_best_technicien(demande):
    """Trouve le meilleur technicien pour une demande selon les critères"""
    # Critères de recherche
    query = User.query.filter_by(role='technicien', actif=True)
    
    # Filtrer par zone si possible
    if demande.zone:
        query = query.filter_by(zone=demande.zone)
    
    # Filtrer par libelle_commune si possible
    if demande.libelle_commune:
        query = query.filter_by(libelle_commune=demande.libelle_commune)
    
    techniciens = query.all()

    # Filtrer par technologie
    techniciens_compatibles = [t for t in techniciens if is_technicien_compatible(t, demande)]
    
    if not techniciens_compatibles:
        return None
    
    # Trouver celui avec le moins d'interventions actives
    meilleur_technicien = None
    min_interventions = float('inf')
    
    for technicien in techniciens_compatibles:
        nb_interventions = Intervention.query.filter_by(
            technicien_id=technicien.id,
            statut='en_cours'
        ).count()
        
        if nb_interventions < min_interventions:
            min_interventions = nb_interventions
            meilleur_technicien = technicien
    
    return meilleur_technicien

def create_sms_notification(technicien_id, demande_id, type_notification, notify_managers=True):
    """Crée une notification SMS pour le technicien et les responsables"""
    demande = db.session.get(DemandeIntervention, demande_id)
    technicien = db.session.get(User, technicien_id)

    # Message pour le technicien
    if type_notification == 'affectation':
        message = f"Nouvelle intervention affectée: {demande.nd} - {demande.nom_client} {demande.prenom_client} - Zone: {demande.zone}"
    elif type_notification == 'rappel':
        message = f"Rappel: Intervention {demande.nd} en attente de traitement depuis 2h"
    elif type_notification == 'validation':
        message = f"Intervention {demande.nd} validée avec succès"
    elif type_notification == 'rejet':
        message = f"Intervention {demande.nd} rejetée - Veuillez consulter les commentaires"
    elif type_notification == 'urgence':
        message = f"URGENT: Intervention {demande.nd} nécessite une attention immédiate"
    elif type_notification == 'echeance':
        message = f"Échéance proche: Intervention {demande.nd} doit être terminée aujourd'hui"
    else:
        message = f"Notification: {demande.nd} - {demande.nom_client} {demande.prenom_client}"

    # Créer et envoyer la notification au technicien
    notification = NotificationSMS(
        technicien_id=technicien_id,
        demande_id=demande_id,
        message=message,
        type_notification=type_notification
    )
    db.session.add(notification)
    
    # Si notify_managers est True, envoyer aux responsables
    if notify_managers:
        # Message pour les responsables
        manager_message = {
            'affectation': f"Nouvelle affectation - Tech: {technicien.nom} - ND: {demande.nd} - Zone: {demande.zone}",
            'rappel': f"Retard d'intervention - Tech: {technicien.nom} - ND: {demande.nd} - Zone: {demande.zone}",
            'validation': f"Intervention validée - Tech: {technicien.nom} - ND: {demande.nd} - Zone: {demande.zone}",
            'rejet': f"Intervention rejetée - Tech: {technicien.nom} - ND: {demande.nd} - Zone: {demande.zone}",
            'urgence': f"URGENT: Intervention prioritaire - ND: {demande.nd} - Zone: {demande.zone}",
            'echeance': f"Échéance aujourd'hui - Tech: {technicien.nom} - ND: {demande.nd} - Zone: {demande.zone}"
        }.get(type_notification, f"Notification générale - ND: {demande.nd}")

        # Trouver les responsables concernés
        managers = User.query.filter(
            User.role.in_(['admin', 'chef_pilote', 'chef_zone']),
            User.actif == True
        )

        # Filtrer selon la zone et le service
        if demande.zone:
            chef_zone = managers.filter_by(role='chef_zone', zone=demande.zone).all()
            for manager in chef_zone:
                notification = NotificationSMS(
                    technicien_id=manager.id,
                    demande_id=demande_id,
                    message=manager_message,
                    type_notification=f"manager_{type_notification}"
                )
                db.session.add(notification)
                print(f"SMS envoyé au chef de zone {manager.nom}: {manager_message}")

        if demande.service:
            chef_pilote = managers.filter_by(role='chef_pilote', service=demande.service).all()
            for manager in chef_pilote:
                notification = NotificationSMS(
                    technicien_id=manager.id,
                    demande_id=demande_id,
                    message=manager_message,
                    type_notification=f"manager_{type_notification}"
                )
                db.session.add(notification)
                print(f"SMS envoyé au chef pilote {manager.nom}: {manager_message}")

        # Notifier les admins
        admins = managers.filter_by(role='admin').all()
        for admin in admins:
            notification = NotificationSMS(
                technicien_id=admin.id,
                demande_id=demande_id,
                message=manager_message,
                type_notification=f"admin_{type_notification}"
            )
            db.session.add(notification)
            print(f"SMS envoyé à l'admin {admin.nom}: {manager_message}")

    db.session.commit()
    print(f"SMS envoyé au technicien {technicien.telephone}: {message}")


def send_email(subject, recipients, body=None, html=None):
    from app import mail
    msg = MailMessage(subject=subject, recipients=recipients)
    if html:
        msg.html = html
    if body:
        msg.body = body
    mail.send(msg)

def get_chef_pur_stats(zone=None):
    """Statistiques pour le Chef PUR (optionnellement filtrées par zone)"""
    today = datetime.now().date()
    
    # 1. OPTIMISATION: Récupérer tous les techniciens principaux des équipes actives en une seule requête jointe
    principal_techs_query = db.session.query(MembreEquipe, Equipe).join(
        Equipe, MembreEquipe.equipe_id == Equipe.id
    ).filter(
        Equipe.actif == True,
        MembreEquipe.type_membre == 'technicien'
    )
    if zone:
        principal_techs_query = principal_techs_query.filter(Equipe.zone == zone)
    
    principal_techs = principal_techs_query.all()
    tech_ids = [mt.technicien_id for mt, eq in principal_techs if mt.technicien_id]
    
    # 2. OPTIMISATION: Récupérer tous les comptes de statuts pour ces techniciens en une seule requête groupée
    stats_data = {}
    if tech_ids:
        bulk_counts = db.session.query(
            DemandeIntervention.technicien_id,
            DemandeIntervention.statut,
            func.count(DemandeIntervention.id)
        ).filter(
            DemandeIntervention.technicien_id.in_(tech_ids)
        )
        if zone:
            bulk_counts = bulk_counts.filter(DemandeIntervention.zone == zone)
        
        bulk_counts = bulk_counts.group_by(
            DemandeIntervention.technicien_id, 
            DemandeIntervention.statut
        ).all()
        
        # Organiser les données par technicien_id
        for tid, status, count in bulk_counts:
            if tid not in stats_data:
                stats_data[tid] = {}
            stats_data[tid][status] = count

    equipes_stats = []
    for mt, eq in principal_techs:
        tid = mt.technicien_id
        counts = stats_data.get(tid, {})
        
        do = counts.get('affecte', 0)
        da = counts.get('en_cours', 0)
        dr = counts.get('rejete', 0)
        dt = counts.get('termine', 0)
        dv = counts.get('valide', 0)
        
        total = do + da + dr + dt + dv
        prod = round((dv / total * 100) if total > 0 else 0, 1)
        
        equipes_stats.append({
            'nom_equipe': eq.nom_equipe,
            'technicien_principal': f"{mt.nom} {mt.prenom}",
            'demandes_orientees': do,
            'demandes_acceptees': da,
            'demandes_rejetees': dr,
            'demandes_traitees': dt,
            'demandes_validees': dv,
            'productivite': prod,
            'zone': eq.zone,
            'service': eq.service,
            'technologies': eq.technologies
        })
    
    # 3. OPTIMISATION: Statistiques par activité en utilisant group_by
    activites_stats = []
    agg_stats_query = db.session.query(
        User.zone,
        Equipe.technologies,
        DemandeIntervention.service,
        func.count(DemandeIntervention.id)
    ).join(
        DemandeIntervention, DemandeIntervention.technicien_id == User.id
    ).join(
        MembreEquipe, MembreEquipe.technicien_id == User.id
    ).join(
        Equipe, MembreEquipe.equipe_id == Equipe.id
    ).filter(
        Equipe.actif == True,
        User.actif == True
    )

    if zone:
        agg_stats_query = agg_stats_query.filter(User.zone == zone)
    
    agg_stats = agg_stats_query.group_by(
        User.zone,
        Equipe.technologies,
        DemandeIntervention.service
    ).all()

    for zone_val, technologies, service, count in agg_stats:
        activites_stats.append({
            'zone': zone_val,
            'technologie': technologies,
            'activite': service,
            'demandes_total': count
        })
    
    # Statistiques globales
    demandes_query = DemandeIntervention.query
    interventions_query = Intervention.query.join(DemandeIntervention)
    equipes_actives_query = Equipe.query.filter_by(actif=True, publie=True, date_publication=today)
    techniciens_actifs_query = User.query.filter_by(role='technicien', actif=True)
    if zone:
        demandes_query = demandes_query.filter_by(zone=zone)
        interventions_query = interventions_query.join(User, Intervention.technicien_id == User.id).filter(User.zone == zone)
        equipes_actives_query = equipes_actives_query.filter_by(zone=zone)
        techniciens_actifs_query = techniciens_actifs_query.filter_by(zone=zone)
    
    # Détail des demandes du jour (Déjà optimisé avec with_entities)
    demandes_jour_query = demandes_query.filter(
        db.func.date(DemandeIntervention.date_creation) == today
    )
    age_stats = demandes_jour_query.with_entities(DemandeIntervention.age, db.func.count()).group_by(DemandeIntervention.age).all()
    priorite_stats = demandes_jour_query.with_entities(DemandeIntervention.priorite_traitement, db.func.count()).group_by(DemandeIntervention.priorite_traitement).all()
    offre_stats = demandes_jour_query.with_entities(DemandeIntervention.offre, db.func.count()).group_by(DemandeIntervention.offre).all()

    # Demandes du jour par service (Déjà simple)
    demandes_jour_sav = demandes_jour_query.filter(DemandeIntervention.service == 'SAV').count()
    demandes_jour_production = demandes_jour_query.filter(DemandeIntervention.service == 'Production').count()
    
    # Interventions validées par service
    interventions_validees_sav = interventions_query.filter(
        Intervention.statut == 'valide',
        db.func.date(Intervention.date_validation) == today,
        DemandeIntervention.service == 'SAV'
    ).count()
    
    interventions_validees_production = interventions_query.filter(
        Intervention.statut == 'valide',
        db.func.date(Intervention.date_validation) == today,
        DemandeIntervention.service == 'Production'
    ).count()

    return {
        'total_demandes': demandes_query.count(),
        'demandes_jour': demandes_jour_query.count(),
        'demandes_jour_sav': demandes_jour_sav,
        'demandes_jour_production': demandes_jour_production,
        'demandes_jour_details': {
            'age': dict(age_stats),
            'priorite_traitement': dict(priorite_stats),
            'offre': dict(offre_stats)
        },
        'interventions_cours': interventions_query.filter(Intervention.statut == 'en_cours').count(),
        'interventions_terminees': interventions_query.filter(Intervention.statut == 'termine').count(),
        'interventions_validees': interventions_query.filter(Intervention.statut == 'valide').count(),
        'interventions_validees_sav': interventions_validees_sav,
        'interventions_validees_production': interventions_validees_production,
        'equipes_actives': equipes_actives_query.count(),
        'techniciens_actifs': techniciens_actifs_query.count(),
        'attente_validation': interventions_query.filter(Intervention.statut == 'termine').count(),
        'interventions_rejetees': interventions_query.filter(Intervention.statut == 'rejete').count(),
        'equipes_stats': equipes_stats,
        'activites_stats': activites_stats,
    }


def get_chef_pilote_stats(service, current_user=None):
    """Statistiques pour les Chefs Pilotes avec gestion du chef pilote principal"""
    today = datetime.now().date()
    
    # Déterminer le filtre de service selon le profil de l'utilisateur
    if current_user and current_user.role == 'chef_pilote' and current_user.service:
        if current_user.service == 'SAV,Production':
            # Chef pilote principal voit les deux services
            base_query = DemandeIntervention.query.filter(
                DemandeIntervention.service.in_(['SAV', 'Production'])
            )
        else:
            # Chef pilote normal voit seulement son service
            base_query = DemandeIntervention.query.filter_by(service=current_user.service)
    else:
        # Pour les autres cas, utiliser le service passé en paramètre
        base_query = DemandeIntervention.query.filter_by(service=service)
    
    return {
        'total_demandes': base_query.count(),
        'demandes_nouvelles': base_query.filter_by(statut='nouveau').count(),
        'demandes_affectees': base_query.filter_by(statut='affecte').count(),
        'demandes_terminees': base_query.filter_by(statut='termine').count(),
        'demandes_validees': base_query.filter_by(statut='valide').count(),
        'demandes_jour': base_query.filter(
            db.func.date(DemandeIntervention.date_creation) == today
        ).count()
    }

def get_performance_data(zone=None):
    """
    🎯 UNIFIED PERFORMANCE DATA - CONSOLIDATION OF TWO SYSTEMS
    
    Previously delegated to kpi_utils.get_performance_data_with_fallback()
    Now uses the NEW unified function with Redis caching and KPI consolidation.
    
    Returns both old fields (taux_reussite) for backward compatibility
    AND new KPI fields (score_total, resolution_1ere_visite, etc.)
    
    Args:
        zone (str): Optional zone filter
        
    Returns:
        dict: Unified performance data with caching
    """
    from kpi_utils import get_unified_performance_data
    return get_unified_performance_data(zone=zone)

def _get_performance_data_fallback(zone=None):
    """
    Fallback: Simple Intervention-based calculation when KPI system is unavailable.
    Graceful degradation - maintains backward compatibility.
    """
    import logging
    from models import Equipe, User, MembreEquipe, Intervention
    from datetime import date
    
    logger = logging.getLogger(__name__)
    
    try:
        today = date.today()
        
        # ÉQUIPES: Simple calculation from Interventions
        equipes_data = []
        equipes_query = Equipe.query.filter_by(actif=True)
        if zone:
            equipes_query = equipes_query.filter_by(zone=zone)
        
        for equipe in equipes_query.all():
            total = Intervention.query.filter_by(equipe_id=equipe.id).count()
            success = Intervention.query.filter_by(equipe_id=equipe.id, statut='valide').count()
            taux = (success / total * 100) if total > 0 else 0
            
            equipes_data.append({
                'nom_equipe': equipe.nom_equipe,
                'prestataire': equipe.prestataire or '',
                'zone': equipe.zone,
                'technologies': equipe.technologies,
                'interventions_realisees': total,
                'taux_reussite': round(taux, 1)
            })
        
        # TECHNICIENS: Simple calculation
        techniciens_data = []
        techniciens_query = User.query.filter_by(role='technicien', actif=True)
        if zone:
            techniciens_query = techniciens_query.filter_by(zone=zone)
        
        for tech in techniciens_query.all():
            total = Intervention.query.filter_by(technicien_id=tech.id).count()
            success = Intervention.query.filter_by(technicien_id=tech.id, statut='valide').count()
            taux = (success / total * 100) if total > 0 else 0
            
            if total > 0:
                membre = MembreEquipe.query.filter_by(
                    technicien_id=tech.id, 
                    type_membre='technicien'
                ).first()
                equipe = db.session.get(Equipe, membre.equipe_id) if membre else None
                
                techniciens_data.append({
                    'nom': tech.nom,
                    'prenom': tech.prenom,
                    'zone': tech.zone,
                    'technologies': tech.technologies,
                    'interventions_realisees': total,
                    'taux_reussite': round(taux, 1),
                    'equipe_nom': equipe.nom_equipe if equipe else '',
                    'prestataire': equipe.prestataire if equipe and equipe.prestataire else ""
                })
        
        # ZONES & PILOTS: Empty for fallback
        zones_data = []
        pilots_data = []
        
        logger.info(f"✅ Fallback calculation succeeded - {len(equipes_data)} equipes, {len(techniciens_data)} techniciens")
        return {
            'equipes': equipes_data,
            'techniciens': techniciens_data,
            'zones': zones_data,
            'pilots': pilots_data,
            '_fallback_used': True
        }
    
    except Exception as fallback_e:
        logger.error(f"❌ CRITICAL: Both KPI and fallback systems failed: {str(fallback_e)}")
        return {
            'equipes': [],
            'techniciens': [],
            'zones': [],
            'pilots': [],
            '_error': str(fallback_e),
            '_fallback_used': True
        }

def get_chef_zone_stats(zone):
    """Statistiques pour les Chefs de Zone - Filtrées par zone spécifique"""
    today = datetime.now().date()
    
    print(f"DEBUG: get_chef_zone_stats appelé avec zone: {zone}")
    
    # Vérifier si zone est None
    if not zone:
        print("DEBUG: Zone est None, retour des stats vides")
        return {
            'equipes_jour': 0,
            'techniciens_zone': 0,
            'interventions_cours': 0,
            'interventions_terminees_jour': 0
        }
    
    # Équipes actives pour cette zone spécifique (pas seulement celles publiées aujourd'hui)
    equipes_total = Equipe.query.filter_by(zone=zone, actif=True).count()
    
    # Équipes publiées aujourd'hui - essayer avec la zone principale, puis ajouter formats alternatifs
    equipes_jour = Equipe.query.filter_by(zone=zone, publie=True, date_publication=today, actif=True).count()
    
    # Si zone est simple (sans parenthèses), essayer aussi le format "Nom (CODE)"
    if zone and '(' not in zone:
        zone_name = zone.strip()
        from models import Zone
        zone_obj = Zone.query.filter_by(nom=zone_name).first()
        if zone_obj:
            zone_formatted = f"{zone_obj.nom} ({zone_obj.code})"
            equipes_jour_formatted = Equipe.query.filter_by(zone=zone_formatted, publie=True, date_publication=today, actif=True).count()
            if equipes_jour_formatted > 0:
                print(f"DEBUG: Équipes avec format zone '{zone_formatted}': {equipes_jour_formatted}")
                equipes_jour += equipes_jour_formatted
    
    print(f"DEBUG: Équipes totales pour zone '{zone}': {equipes_total}")
    print(f"DEBUG: Équipes publiées aujourd'hui pour zone '{zone}': {equipes_jour}")
    
    # Techniciens de cette zone spécifique (vérifier zone texte et zone_id)
    from models import Zone
    zone_obj = None
    
    # Essayer de trouver la zone objet à partir du nom de zone
    if zone and '(' in zone and ')' in zone:
        # Format "Nom (Code)" - extraire le nom
        zone_name = zone.split('(')[0].strip()
        zone_obj = Zone.query.filter_by(nom=zone_name).first()
    elif zone:
        # Format simple - chercher par nom ou code
        zone_obj = Zone.query.filter((Zone.nom == zone) | (Zone.code == zone)).first()
    
    techniciens_zone = 0
    if zone_obj:
        # Compter les techniciens avec zone_id correspondant
        techniciens_with_id = User.query.filter_by(role='technicien', zone_id=zone_obj.id, actif=True).count()
        print(f"DEBUG: Techniciens avec zone_id {zone_obj.id}: {techniciens_with_id}")
        
        # Ajouter les techniciens avec l'ancien champ zone (compatibilité)
        techniciens_with_text = User.query.filter_by(role='technicien', zone=zone, actif=True).count()
        print(f"DEBUG: Techniciens avec zone texte '{zone}': {techniciens_with_text}")
        
        techniciens_zone = techniciens_with_id + techniciens_with_text
    elif zone:
        # Fallback: utiliser l'ancienne méthode
        techniciens_zone = User.query.filter_by(role='technicien', zone=zone, actif=True).count()
        print(f"DEBUG: Techniciens fallback zone texte: {techniciens_zone}")
    
    print(f"DEBUG: Total techniciens zone '{zone}': {techniciens_zone}")
    
    # Interventions en cours pour cette zone spécifique
    if zone_obj:
        # Avec zone_id
        interventions_cours_id = Intervention.query.join(User, Intervention.technicien_id == User.id).filter(
            User.zone_id == zone_obj.id,
            Intervention.statut == 'en_cours'
        ).count()
        
        # Avec zone texte (compatibilité)
        interventions_cours_text = Intervention.query.join(User, Intervention.technicien_id == User.id).filter(
            User.zone == zone,
            Intervention.statut == 'en_cours'
        ).count()
        
        interventions_cours = interventions_cours_id + interventions_cours_text
    elif zone:
        # Fallback: ancienne méthode
        interventions_cours = Intervention.query.join(User, Intervention.technicien_id == User.id).filter(
            User.zone == zone, 
            Intervention.statut == 'en_cours'
        ).count()
    
    print(f"DEBUG: Interventions en cours pour zone '{zone}': {interventions_cours}")
    
    # Interventions terminées aujourd'hui pour cette zone spécifique
    if zone_obj:
        # Avec zone_id
        interventions_terminees_id = Intervention.query.join(User, Intervention.technicien_id == User.id).filter(
            User.zone_id == zone_obj.id,
            Intervention.statut == 'termine',
            db.func.date(Intervention.date_fin) == today
        ).count()
        
        # Avec zone texte (compatibilité)
        interventions_terminees_text = Intervention.query.join(User, Intervention.technicien_id == User.id).filter(
            User.zone == zone,
            Intervention.statut == 'termine',
            db.func.date(Intervention.date_fin) == today
        ).count()
        
        interventions_terminees_jour = interventions_terminees_id + interventions_terminees_text
    elif zone:
        # Fallback: ancienne méthode
        interventions_terminees_jour = Intervention.query.join(User, Intervention.technicien_id == User.id).filter(
            User.zone == zone, 
            Intervention.statut == 'termine',
            db.func.date(Intervention.date_fin) == today
        ).count()
    
    print(f"DEBUG: Interventions terminées aujourd'hui pour zone '{zone}': {interventions_terminees_jour}")
    
    stats = {
        'equipes_jour': equipes_jour,
        'techniciens_zone': techniciens_zone,
        'interventions_cours': interventions_cours,
        'interventions_terminees_jour': interventions_terminees_jour
    }
    
    print(f"DEBUG: Stats finales pour zone '{zone}': {stats}")
    return stats

def get_technicien_interventions(technicien_id):
    """Récupère les interventions d'un technicien"""
    return Intervention.query.filter_by(technicien_id=technicien_id).join(
        DemandeIntervention
    ).order_by(DemandeIntervention.date_demande_intervention.desc()).all()

import requests
def send_orange_sms(to, message, sender=None):
    client_id = os.getenv("ORANGE_CLIENT_ID")
    client_secret = os.getenv("ORANGE_CLIENT_SECRET")
    # Ajoute le préfixe tel: si absent
    if sender and not sender.startswith("tel:"):
        sender_tel = f"tel:{sender}"
    else:
        sender_tel = sender
    token_url = "https://api.orange.com/oauth/v3/token"
    sms_url = f"https://api.orange.com/smsmessaging/v1/outbound/{sender_tel}/requests"

    auth = (client_id, client_secret)
    data = {'grant_type': 'client_credentials'}
    token_resp = requests.post(token_url, auth=auth, data=data)
    token = token_resp.json().get('access_token')

    if not token:
        print("Erreur d'obtention du token Orange:", token_resp.text, flush=True)
        return False

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "outboundSMSMessageRequest": {
            "address": f"tel:{to}",
            "senderAddress": sender_tel,  # doit être identique à l'URL
            "outboundSMSTextMessage": {
                "message": message
            }
        }
    }
    resp = requests.post(sms_url, headers=headers, json=payload)
    print(f"Orange SMS API status: {resp.status_code}, réponse: {resp.text}", flush=True)
    return resp.status_code == 201



def build_stats_by_zone_tech():
    services = ['SAV', 'Production']
    zones_list = ['MBOUR', 'KAOLACK', 'DAKAR']
    technologies = ['Fibre', 'Cuivre', '5G']

    # OPTIMISATION: Une seule requête agrégée pour toutes les stats
    # On récupère les comptes groupés par service, zone et technologie
    query_results = db.session.query(
        DemandeIntervention.service,
        DemandeIntervention.zone,
        DemandeIntervention.type_techno,
        func.count(DemandeIntervention.id).label('total'),
        func.sum(case((DemandeIntervention.statut == 'affecte', 1), else_=0)).label('ot_oriente'),
        func.sum(case((DemandeIntervention.statut == 'valide', 1), else_=0)).label('ot_cloture'),
        func.sum(case((Intervention.statut == 'en_cours', 1), else_=0)).label('ot_traite'),
        func.sum(case((Intervention.statut == 'termine', 1), else_=0)).label('ot_non_cloture')
    ).outerjoin(
        Intervention, DemandeIntervention.id == Intervention.demande_id
    ).group_by(
        DemandeIntervention.service,
        DemandeIntervention.zone,
        DemandeIntervention.type_techno
    ).all()

    # Transformer les résultats en dictionnaire pour accès rapide
    raw_data = {}
    for r in query_results:
        # Normaliser la zone pour le regroupement DAKAR
        zone_name = r.zone.upper() if r.zone else ""
        raw_data[(r.service, zone_name, r.type_techno.lower())] = r

    stats_by_zone_tech = {}

    for service in services:
        for zone in zones_list:
            for tech in technologies:
                tech_lower = tech.lower()
                tech_db = tech[0].upper() + tech[1:].lower()
                
                key = (service, zone, tech_lower)
                
                # Initialiser les compteurs
                total_demandes = 0
                ot_oriente = 0
                ot_traite = 0
                ot_cloture = 0
                ot_non_cloture = 0

                if zone == 'DAKAR':
                    # Regrouper tout ce qui n'est pas MBOUR ou KAOLACK
                    for (srv, z, t), data in raw_data.items():
                        if srv == service and t == tech_lower and z not in ['MBOUR', 'KAOLACK']:
                            total_demandes += data.total
                            ot_oriente += data.ot_oriente
                            ot_traite += data.ot_traite
                            ot_cloture += data.ot_cloture
                            ot_non_cloture += data.ot_non_cloture
                else:
                    # Données spécifiques à la zone
                    data = raw_data.get((service, zone, tech_lower))
                    if data:
                        total_demandes = data.total
                        ot_oriente = data.ot_oriente
                        ot_traite = data.ot_traite
                        ot_cloture = data.ot_cloture
                        ot_non_cloture = data.ot_non_cloture

                productivite = f"{round((ot_cloture / total_demandes * 100) if total_demandes > 0 else 0, 1)}%"

                stats_by_zone_tech[key] = {
                    'ot_oriente': int(ot_oriente),
                    'ot_traite': int(ot_traite),
                    'ot_cloture': int(ot_cloture),
                    'ot_non_cloture': int(ot_non_cloture),
                    'productivite': productivite
                }
                
    return stats_by_zone_tech


def log_activity(user_id, action, module, entity_id=None, entity_name=None, details=None, ip_address=None):
    """Log une activité utilisateur"""
    if not ip_address:
        ip_address = request.remote_addr if request else None
    
    if details and not isinstance(details, str):
        details = json.dumps(details, default=str)
    
    log = ActivityLog(
        user_id=user_id,
        action=action,
        module=module,
        entity_id=entity_id,
        entity_name=entity_name,
        details=details,
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()