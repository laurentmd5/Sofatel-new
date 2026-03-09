# Remplacer "from app import db" par :
from extensions import db
from flask import current_app
from flask_login import UserMixin
from datetime import datetime, timezone
from sqlalchemy import func, Enum
import enum


def utcnow():
    """Return timezone-aware UTC datetime for use in defaults."""
    return datetime.now(timezone.utc)


# ============================================================================
# CONSTANTES DE RÔLES - GESTION DE STOCK
# ============================================================================

class RoleEnum(enum.Enum):
    """Énumération des rôles utilisateurs"""
    CHEF_PUR = 'chef_pur'  # Responsable principal stock
    GESTIONNAIRE_STOCK = 'gestionnaire_stock'  # Gestion centrale
    MAGASINIER = 'magasinier'  # Magasinier local (zone)
    TECHNICIEN = 'technicien'  # Technicien terrain
    DIRECTION = 'direction'  # Direction (DG/DT)
    ADMIN = 'admin'  # Administrateur système
    CHEF_PILOTE = 'chef_pilote'  # Chef de pilote (ancien)
    CHEF_ZONE = 'chef_zone'  # Chef de zone (ancien)
    CONTROLE_OPERATIONS = 'controle_operations_terrains'  # Contrôle opérations
    COMPTABILITE = 'comptabilite_finance'  # Comptabilité
    RH = 'rh'  # Gestionnaire RH


ROLE_CHOICES = [
    ('chef_pur', 'Responsable Principal Stock'),
    ('gestionnaire_stock', 'Gestionnaire de Stock'),
    ('magasinier', 'Magasinier Local'),
    ('technicien', 'Technicien'),
    ('direction', 'Direction'),
    ('admin', 'Administrateur'),
    ('chef_pilote', 'Chef Pilote'),
    ('chef_zone', 'Chef Zone'),
    ('controle_operations_terrains', 'Contrôle Opérations'),
    ('rh', 'Gestionnaire RH'),
    ('comptabilite_finance', 'Comptabilité Finance'),
]

# Rôles autorisés pour le module stock
STOCK_ROLES = ['chef_pur', 'gestionnaire_stock', 'magasinier', 'technicien', 'direction', 'admin']

# Rôles avec accès au stock (tous les rôles valides)
ALL_ROLES = [choice[0] for choice in ROLE_CHOICES]

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_survey = db.Column(db.Date, nullable=False)
    nom_raison_sociale = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    represente_par = db.Column(db.String(100))
    tel1 = db.Column(db.String(20), nullable=False)
    tel2 = db.Column(db.String(20))
    adresse_demande = db.Column(db.String(255), nullable=False)
    etage = db.Column(db.String(20))
    gps_lat = db.Column(db.String(50))
    gps_long = db.Column(db.String(50))
    h_debut = db.Column(db.String(20))
    h_fin = db.Column(db.String(20))
    n_ligne = db.Column(db.String(50))
    n_demande = db.Column(db.String(50), nullable=False)
    service_demande = db.Column(db.String(50), nullable=False)
    etat_client = db.Column(db.String(50))
    nature_local = db.Column(db.String(50))
    type_logement = db.Column(db.String(50))
    fibre_dispo = db.Column(db.Boolean)
    cuivre_dispo = db.Column(db.Boolean)
    gpon_olt = db.Column(db.String(50))
    splitter = db.Column(db.String(50))
    distance_fibre = db.Column(db.Integer)
    etat_fibre = db.Column(db.String(20))
    sr = db.Column(db.String(50))
    pc = db.Column(db.String(50))
    distance_cuivre = db.Column(db.Integer)
    etat_cuivre = db.Column(db.String(20))
    modem = db.Column(db.Boolean)
    ont = db.Column(db.Boolean)
    nb_prises = db.Column(db.Integer)
    quantite_cable = db.Column(db.Integer)
    observation_tech = db.Column(db.Text)
    observation_client = db.Column(db.Text)
    conclusion = db.Column(db.String(50), nullable=False)
    photos = db.Column(db.Text)
    """ photo_batiment = db.Column(db.String(255))
    photo_environ = db.Column(db.String(255)) """
    technicien_structure = db.Column(db.String(100))
    backoffice_structure = db.Column(db.String(100))
    offre = db.Column(db.String(100))
    debit = db.Column(db.String(50))
    type_mi = db.Column(db.Boolean)
    type_na = db.Column(db.Boolean)
    type_transfer = db.Column(db.Boolean)
    type_autre = db.Column(db.Boolean)
    nro = db.Column(db.String(50))
    type_reseau = db.Column(db.String(50))
    plaque = db.Column(db.String(50))
    bpi = db.Column(db.String(50))
    pbo = db.Column(db.String(50))
    coupleur = db.Column(db.String(50))
    fibre = db.Column(db.String(50))
    nb_clients = db.Column(db.Integer)
    valeur_pbo_dbm = db.Column(db.String(20))
    bpi_b1 = db.Column(db.String(50))
    pbo_b1 = db.Column(db.String(50))
    coupleur_b1 = db.Column(db.String(50))
    nb_clients_b1 = db.Column(db.Integer)
    valeur_pbo_dbm_b1 = db.Column(db.String(20))
    description_logement_avec_bpi = db.Column(db.Text)
    description_logement_sans_bpi = db.Column(db.Text)
    emplacement_pto = db.Column(db.String(100))
    passage_cable = db.Column(db.Text)
    longueur_tirage_pbo_bti = db.Column(db.String(50))
    longueur_tirage_bti_pto = db.Column(db.String(50))
    materiel_existant_decodeur_carte = db.Column(db.Boolean)
    materiel_existant_wifi_extender = db.Column(db.Boolean)
    materiel_existant_fax = db.Column(db.Boolean)
    materiel_existant_videosurveillance = db.Column(db.Boolean)
    qualite_ligne_adsl_defaut_couverture = db.Column(db.Boolean)
    qualite_ligne_adsl_lenteurs = db.Column(db.Boolean)
    qualite_ligne_adsl_deconnexions = db.Column(db.Boolean)
    qualite_ligne_adsl_ras = db.Column(db.Boolean)
    niveau_wifi_salon = db.Column(db.String(20))
    niveau_wifi_chambre1 = db.Column(db.String(20))
    niveau_wifi_bureau1 = db.Column(db.String(20))
    niveau_wifi_autres_pieces = db.Column(db.String(20))
    choix_bf_hall = db.Column(db.Boolean)
    choix_bf_chambre2 = db.Column(db.Boolean)
    choix_bf_bureau2 = db.Column(db.Boolean)
    choix_bf_mesure_dbm = db.Column(db.String(20))
    cuisine_chambre3 = db.Column(db.Boolean)
    cuisine_bureau3 = db.Column(db.Boolean)
    cuisine_mesure_dbm = db.Column(db.String(20))
    repeteur_wifi_oui = db.Column(db.Boolean)
    repeteur_wifi_non = db.Column(db.Boolean)
    repeteur_wifi_quantite = db.Column(db.Integer)
    repeteur_wifi_emplacement = db.Column(db.String(100))
    cpl_oui = db.Column(db.Boolean)
    cpl_non = db.Column(db.Boolean)
    cpl_quantite = db.Column(db.Integer)
    cpl_emplacement = db.Column(db.String(100))
    cable_local_type = db.Column(db.String(50))
    cable_local_longueur = db.Column(db.String(20))
    cable_local_connecteurs = db.Column(db.String(50))
    goulottes_oui = db.Column(db.Boolean)
    goulottes_non = db.Column(db.Boolean)
    goulottes_quantite = db.Column(db.Integer)
    goulottes_nombre_x2m = db.Column(db.Integer)
    survey_ok = db.Column(db.Boolean)
    survey_nok = db.Column(db.Boolean)
    motif = db.Column(db.Text)
    commentaires = db.Column(db.Text)
    signature_equipe = db.Column(db.Text)
    signature_client = db.Column(db.Text)
    client_tres_satisfait = db.Column(db.Boolean)
    client_satisfait = db.Column(db.Boolean)
    client_pas_satisfait = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    
    # Relation avec l'intervention
    intervention_id = db.Column(db.Integer, db.ForeignKey('intervention.id'))
    intervention = db.relationship('Intervention', backref=db.backref('surveys', lazy=True))
    
    def __repr__(self):
        return f'<Survey {self.n_demande}>'


class FicheTechnique(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    
    # Informations générales
    nom_raison_sociale = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(255), nullable=False)
    represente_par = db.Column(db.String(255))
    date_installation = db.Column(db.Date, nullable=False)
    tel1 = db.Column(db.String(20), nullable=False)
    tel2 = db.Column(db.String(20))
    adresse_demandee = db.Column(db.String(255), nullable=False)
    etage = db.Column(db.String(50))
    gps_lat = db.Column(db.String(50))
    gps_long = db.Column(db.String(50))
    type_logement_avec_bpi = db.Column(db.Text)
    type_logement_sans_bpi = db.Column(db.Text)
    h_arrivee = db.Column(db.Time)
    h_depart = db.Column(db.Time)
    
    # Informations techniques
    n_ligne = db.Column(db.String(50))
    n_demande = db.Column(db.String(50))
    technicien_structure = db.Column(db.String(100))
    pilote_structure = db.Column(db.String(100))
    offre = db.Column(db.String(100))
    debit = db.Column(db.String(50))
    type_mc = db.Column(db.Boolean, default=False)
    type_na = db.Column(db.Boolean, default=False)
    type_transfert = db.Column(db.Boolean, default=False)
    type_autre = db.Column(db.Boolean, default=False)
    backoffice_structure = db.Column(db.String(100))
    
    # Matériels
    type_ont = db.Column(db.String(100))
    nature_ont = db.Column(db.String(100))
    numero_serie_ont = db.Column(db.String(100))
    type_decodeur = db.Column(db.String(100))
    nature_decodeur = db.Column(db.String(100))
    numero_serie_decodeur = db.Column(db.String(100))
    disque_dur = db.Column(db.Boolean, default=False)
    telephone = db.Column(db.Boolean, default=False)
    recepteur_wifi = db.Column(db.Boolean, default=False)
    cpl = db.Column(db.Boolean, default=False)
    carte_vaccess = db.Column(db.Boolean, default=False)
    
    # Accessoires
    type_cable_lc = db.Column(db.String(100))
    type_cable_bti = db.Column(db.String(100))
    type_cable_pto_one = db.Column(db.String(100))
    kit_pto = db.Column(db.Boolean, default=False)
    piton = db.Column(db.Boolean, default=False)
    arobase = db.Column(db.Boolean, default=False)
    malico = db.Column(db.Boolean, default=False)
    ds6 = db.Column(db.Boolean, default=False)
    autre_accessoire = db.Column(db.String(255))
    
    # Tests de services
    appel_sortant_ok = db.Column(db.Boolean, default=False)
    appel_sortant_nok = db.Column(db.Boolean, default=False)
    appel_entrant_ok = db.Column(db.Boolean, default=False)
    appel_entrant_nok = db.Column(db.Boolean, default=False)
    tvo_mono_ok = db.Column(db.Boolean, default=False)
    tvo_mono_nok = db.Column(db.Boolean, default=False)
    tvo_multi_ok = db.Column(db.Boolean, default=False)
    tvo_multi_nok = db.Column(db.Boolean, default=False)
    enregistreur_dd_ok = db.Column(db.Boolean, default=False)
    enregistreur_dd_nok = db.Column(db.Boolean, default=False)
    
    # Tests de débits
    par_cable_salon = db.Column(db.String(50))
    par_cable_chambres = db.Column(db.String(50))
    par_cable_bureau = db.Column(db.String(50))
    par_cable_autres = db.Column(db.String(50))
    par_cable_vitesse_wifi = db.Column(db.String(50))
    par_cable_mesure_mbps = db.Column(db.Integer)
    par_wifi_salon = db.Column(db.String(50))
    par_wifi_chambres = db.Column(db.String(50))
    par_wifi_bureau = db.Column(db.String(50))
    par_wifi_autres = db.Column(db.String(50))
    par_wifi_vitesse_wifi = db.Column(db.String(50))
    par_wifi_mesure_mbps = db.Column(db.Integer)
    
    # Etiquetages et Nettoyage
    etiquetage_colliers_serres = db.Column(db.Boolean, default=False)
    etiquetage_pbo_normalise = db.Column(db.Boolean, default=False)
    nettoyage_depose = db.Column(db.Boolean, default=False)
    nettoyage_tutorat = db.Column(db.Boolean, default=False)
    
    # Rattachement
    rattachement_nro = db.Column(db.String(100))
    rattachement_type = db.Column(db.String(100))
    rattachement_num_carte = db.Column(db.String(100))
    rattachement_num_port = db.Column(db.String(100))
    rattachement_plaque = db.Column(db.String(100))
    rattachement_bpi_pbo = db.Column(db.String(100))
    rattachement_coupleur = db.Column(db.String(100))
    rattachement_fibre = db.Column(db.String(100))
    rattachement_ref_dbm = db.Column(db.String(50))
    rattachement_mesure_dbm = db.Column(db.String(50))
    
    # Commentaires
    commentaires = db.Column(db.Text)
    photos = db.Column(db.Text)
    # Signatures et satisfaction client
    signature_equipe = db.Column(db.Text)  # Stockage base64 ou chemin fichier
    signature_client = db.Column(db.Text)  # Stockage base64 ou chemin fichier
    client_tres_satisfait = db.Column(db.Boolean, default=False)
    client_satisfait = db.Column(db.Boolean, default=False)
    client_pas_satisfait = db.Column(db.Boolean, default=False)
    
    # Métadonnées
    date_creation = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    
    # Relations
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    technicien = db.relationship('User', backref=db.backref('surveys', lazy=True))
    intervention_id = db.Column(db.Integer, db.ForeignKey('intervention.id'))
    intervention = db.relationship('Intervention', backref='fiche_technique_data', uselist=False)
    
    def __repr__(self):
        return f'<FicheTechnique {self.id} - {self.nom_raison_sociale}>'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # chef_pur, chef_pilote, chef_zone, technicien
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    zone = db.Column(db.String(50))  # Pour chef_zone et technicien (legacy)
    commune = db.Column(db.String(50))  # Commune pour technicien
    quartier = db.Column(db.String(50))  # Quartier pour technicien
    service = db.Column(db.String(20))  # SAV ou Production pour chef_pilote
    technologies = db.Column(db.String(100))  # Technologies maîtrisées par le technicien
    
    # ========== STOCK MODULE ZONE FK ==========
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=True)
    zone_relation = db.relationship('Zone', foreign_keys=[zone_id], backref=db.backref('utilisateurs', lazy='dynamic'))
    
    actif = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    interventions = db.relationship('Intervention', foreign_keys='Intervention.technicien_id', backref='technicien_user', lazy='dynamic', overlaps='interventions_realisees,technicien')
    equipes_creees = db.relationship('Equipe', foreign_keys='Equipe.chef_zone_id', backref='chef_zone', lazy='dynamic')

    def get_role_display(self):
        if self.role == 'chef_pur':
            return 'Chef PUR'
        elif self.role == 'chef_pilote':
            if self.service == 'SAV,Production':
                return 'Chef Pilote Principal'
            else:
                return 'Pilote'
        elif self.role == 'chef_zone':
            return 'Chef Zone'
        elif self.role == 'technicien':
            return 'Technicien'
        elif self.role == 'gestionnaire_stock':
            return 'Gestionnaire de Stock'
        elif self.role == 'controle_operations_terrains':
            return 'Contrôle des opérations terrains'
        elif self.role == 'comptabilite_finance':
            return 'Comptabilité et services financiers'
        elif self.role == 'rh':
            return 'Gestionnaire RH'
        else:
            return self.role.replace('_', ' ').title()

    # ========================================================================
    # MÉTHODES DE VÉRIFICATION DE PERMISSIONS STOCK
    # ========================================================================
    
    def has_stock_permission(self, permission_key):
        """
        Vérifie si utilisateur a une permission stock spécifique
        
        Args:
            permission_key: Clé permission (ex: 'can_receive_stock')
            
        Returns:
            bool: True si utilisateur a permission
        """
        from rbac_stock import STOCK_PERMISSIONS
        
        if not self.role:
            return False
        
        role = self.role.lower()
        perms = STOCK_PERMISSIONS.get(role, {})
        return perms.get(permission_key, False)
    
    def is_stock_manager(self):
        """Vérifie si utilisateur est gestionnaire stock"""
        return self.role.lower() in ['chef_pur', 'gestionnaire_stock', 'admin']
    
    def is_stock_warehouse(self):
        """Vérifie si utilisateur est magasinier"""
        return self.role.lower() in ['magasinier', 'chef_pur', 'gestionnaire_stock', 'admin']
    
    def is_stock_viewer(self):
        """Vérifie si utilisateur peut visualiser le stock"""
        return self.role.lower() in ['chef_pur', 'gestionnaire_stock', 'magasinier', 'direction', 'admin']
    
    def is_director(self):
        """Vérifie si utilisateur est direction"""
        return self.role.lower() in ['direction', 'admin']
    
    def is_chef_pur(self):
        """Vérifie si utilisateur est chef pur"""
        return self.role.lower() == 'chef_pur'
    
    def is_admin(self):
        """Vérifie si utilisateur est administrateur"""
        return self.role.lower() == 'admin'
    
    def can_edit_globally(self):
        """Vérifie si utilisateur peut éditer partout (sans restriction de zone)"""
        return self.role.lower() in ['chef_pur', 'gestionnaire_stock', 'admin']
    
    def can_access_zone(self, zone):
        """
        Vérifie si utilisateur peut accéder une zone
        
        Args:
            zone: Code zone
            
        Returns:
            bool: True si accès autorisé
        """
        if self.can_edit_globally():
            return True
        
        # Pour les rôles zonés: vérifier sa zone
        if self.role.lower() in ['magasinier', 'technicien', 'chef_zone']:
            return self.zone == zone
        
        return False

class DemandeIntervention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nd = db.Column(db.String(50), nullable=False)
    demandee = db.Column(db.String(50))
    zone = db.Column(db.String(50), nullable=False)
    priorite_traitement = db.Column(db.String(50))
    # SLA override field (hours) - optional per demande
    sla_hours_override = db.Column(db.Integer, nullable=True)  # if set, overrides SLA hours mapping
    
    origine = db.Column(db.String(100))
    offre = db.Column(db.String(100))
    type_techno = db.Column(db.String(50), nullable=False)  # Fibre, Cuivre, 5G
    produit = db.Column(db.String(100))
    age = db.Column(db.String(10))
    nom_client = db.Column(db.String(100), nullable=False)
    prenom_client = db.Column(db.String(100), nullable=True)  # Rendre nullable
    rep_srp = db.Column(db.String(100))
    constitution = db.Column(db.String(100))
    specialite = db.Column(db.String(100))
    resultat_essai = db.Column(db.String(100))
    commentaire_essai = db.Column(db.Text)
    agent_essai = db.Column(db.String(100))
    date_demande_intervention = db.Column(db.DateTime, nullable=False)
    commentaire_interv = db.Column(db.Text)
    id_ot = db.Column(db.String(50))
    fichier_importe_id = db.Column(db.Integer, db.ForeignKey('fichier_import.id'))
    equipe = db.Column(db.String(100))
    section_id = db.Column(db.String(50))
    statut = db.Column(db.String(50), default='nouveau')  # nouveau, affecte, en_cours, termine, valide
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    libelle_commune = db.Column(db.String(100))
    libelle_quartier = db.Column(db.String(255))
    prestataire = db.Column(db.String(50))
    taches = db.Column(db.String(100))
    service = db.Column(db.String(50), nullable=False)  # SAV ou Production
    date_creation = db.Column(db.DateTime, default=utcnow)
    date_affectation = db.Column(db.DateTime)
    date_completion = db.Column(db.DateTime)
    date_echeance = db.Column(db.Date)

    contact_client = db.Column(db.String(100))
    commentaire_contact = db.Column(db.Text)
    zone_rs = db.Column(db.String(100))
    id_drgt = db.Column(db.String(50))
    libel_sig = db.Column(db.String(100))
    date_sig = db.Column(db.DateTime)
    compteur = db.Column(db.String(50))
    
    # Champs pour l'importation Production
    commande_client = db.Column(db.String(100))
    date_validation = db.Column(db.DateTime)
    heure = db.Column(db.String(50))
    rbs = db.Column(db.String(100))
    pilotes = db.Column(db.String(100))
    st = db.Column(db.String(100))
    ci_prcl = db.Column(db.String(100))
    coordonnees_gps = db.Column(db.String(100))
    sr = db.Column(db.String(100))
    adresse = db.Column(db.Text)
    
    # Relations
    fichier_import = db.relationship('FichierImport', backref='demandes')
    intervention = db.relationship('Intervention', uselist=False, backref='demande')

class FichierImport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_fichier = db.Column(db.String(255), nullable=False)
    date_import = db.Column(db.DateTime, default=utcnow)
    importe_par = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nb_lignes = db.Column(db.Integer, default=0)
    nb_erreurs = db.Column(db.Integer, default=0)
    statut = db.Column(db.String(20), default='en_cours')  # en_cours, termine, erreur
    service = db.Column(db.String(20), nullable=True)  # SAV ou Production
    
    # ✅ SOFT DELETE - Solution 3
    actif = db.Column(db.Boolean, default=True, index=True)
    date_suppression = db.Column(db.DateTime, nullable=True)
    
    # Relations
    importeur = db.relationship('User', backref='imports')


class LeaveRequest(db.Model):
    """
    Leave/Absence request with complete workflow.
    
    Statuses: pending -> approved/rejected
    Tracks: requester, approver, dates, reason, timestamps
    Validates: no overlapping leave, business hours calculation
    """
    __tablename__ = 'leave_request'
    id = db.Column(db.Integer, primary_key=True)
    
    # Requester info
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    technicien = db.relationship('User', foreign_keys=[technicien_id], backref='leave_requests_as_requester')
    
    # Leave details
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # conge_paye, conge_sans_solde, absence, maladie, etc.
    reason = db.Column(db.Text, nullable=True)  # Raison de la demande
    
    # Workflow tracking
    statut = db.Column(db.String(20), default='pending')  # pending, approved, rejected, cancelled
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Who approved/rejected
    manager = db.relationship('User', foreign_keys=[manager_id], backref='leave_requests_as_manager')
    manager_comment = db.Column(db.Text, nullable=True)  # Manager's comment on approval/rejection
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)  # When approved/rejected
    
    # Business hours calculation
    business_days_count = db.Column(db.Float, default=0)  # Calculated at creation
    
    def __repr__(self):
        return f'<LeaveRequest {self.id}: {self.technicien.username} {self.date_debut}-{self.date_fin}>'
    
    def is_approved(self):
        return self.statut == 'approved'
    
    def is_pending(self):
        return self.statut == 'pending'
    
    def overlaps_with(self, other_leave):
        """Check if this leave overlaps with another approved leave"""
        if self.id == other_leave.id:
            return False
        if other_leave.statut != 'approved':
            return False
        # No overlap if either ends before the other starts
        if self.date_fin < other_leave.date_debut or self.date_debut > other_leave.date_fin:
            return False
        return True


class NoteRH(db.Model):
    """
    RH Service Notes - Internal communications for team awareness
    
    Features:
    - Title and content for internal communications
    - Author tracking (RH manager who created)
    - Publication date management
    - Target audience (all techs, by zone, by service)
    - Soft delete via actif flag
    """
    __tablename__ = 'note_rh'
    
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)  # Title (max 200 chars)
    contenu = db.Column(db.Text, nullable=False)  # Content (unlimited)
    
    # Author tracking
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', foreign_keys=[author_id], backref='notes_rh_created')
    
    # Timestamps
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_publication = db.Column(db.DateTime, nullable=True)  # Null = draft, set = published
    
    # Distribution settings
    destinataires = db.Column(db.String(50), default='tous')  # 'tous', 'zone', 'service'
    zone_cible = db.Column(db.String(100), nullable=True)  # If destinataires='zone'
    service_cible = db.Column(db.String(50), nullable=True)  # If destinataires='service'
    
    # Soft delete
    actif = db.Column(db.Boolean, default=True, index=True)
    date_archivage = db.Column(db.DateTime, nullable=True)
    
    # Updated tracking
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NoteRH {self.id}: {self.titre}>'
    
    def is_published(self):
        """Check if note is published (date_publication is set)"""
        return self.date_publication is not None and self.date_publication <= datetime.utcnow()
    
    def publish(self):
        """Publish the note (set publication date to now)"""
        self.date_publication = datetime.utcnow()
    
    def archive(self):
        """Soft delete the note"""
        self.actif = False
        self.date_archivage = datetime.utcnow()


class Equipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_equipe = db.Column(db.String(100), nullable=False)
    date_creation = db.Column(db.Date, nullable=False)
    chef_zone_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    zone = db.Column(db.String(50), nullable=False)
    prestataire = db.Column(db.String(50))  # Prestataire (ex: Netsysteme, etc.)
    technologies = db.Column(db.String(100), nullable=False)  # Technologies couvertes
    service = db.Column(db.String(50), nullable=False)  # SAV ou Production
    actif = db.Column(db.Boolean, default=True)
    publie = db.Column(db.Boolean, default=False)  # Nouveau champ pour indiquer si l'équipe est publiée
    date_publication = db.Column(db.Date)  # Date de la dernière publication
    # Relations
    membres = db.relationship('MembreEquipe', backref='equipe', cascade='all, delete-orphan')

class MembreEquipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipe.id'), nullable=False)
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    type_membre = db.Column(db.String(20), nullable=False)  # technicien, accompagnant
    
    # Relations
    technicien = db.relationship('User', backref='participations_equipe')

""" class Intervention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    demande_id = db.Column(db.Integer, db.ForeignKey('demande_intervention.id'), nullable=False)
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipe.id'))
    motif_rejet = db.Column(db.String(512))
    # Champs du rapport d'intervention
    numero = db.Column(db.String(50))
    constitutions = db.Column(db.String(100))
    valeur_pB0 = db.Column(db.String(50))
    nature_signalisation = db.Column(db.String(100))
    diagnostic_technicien = db.Column(db.Text)
    cause_derangement = db.Column(db.Text)
    action_releve = db.Column(db.Text)
    materiel_recup = db.Column(db.String(100))
    numero_serie_livre = db.Column(db.String(100))
    materiel_recupere = db.Column(db.String(100))
    numero_serie_recup = db.Column(db.String(100))
    appel_sortant = db.Column(db.Boolean, default=False)
    envoi_numero = db.Column(db.String(20))
    appel_entrant = db.Column(db.Boolean, default=False)
    affichage_numero = db.Column(db.String(20))
    tvo_mono_ok = db.Column(db.Boolean, default=False)
    pieces = db.Column(db.Text)
    communes = db.Column(db.String(100))
    chambres = db.Column(db.String(100))
    bureau = db.Column(db.String(100))
    statut = db.Column(db.String(20), default='nouveau')  # nouveau, en_cours, termine, valide
    date_debut = db.Column(db.DateTime)
    date_fin = db.Column(db.DateTime)
    
    # Champs supplémentaires pour interventions
    wifi_extender = db.Column(db.Boolean, default=False)
    satisfaction = db.Column(db.String(20))
    signature_equipe = db.Column(db.Text)  # Base64 ou chemin fichier
    signature_client = db.Column(db.Text)  # Base64 ou chemin fichier
    
    # Métadonnées
    date_validation = db.Column(db.DateTime)
    valide_par = db.Column(db.Integer, db.ForeignKey('user.id'))
    commentaire_validation = db.Column(db.Text)
    technicien = db.relationship('User', foreign_keys=[technicien_id], backref='interventions_realisees')
    valideur = db.relationship('User', foreign_keys=[valide_par], backref='interventions_validees')
    
    # Pour le service Production
    survey_ok = db.Column(db.Boolean)
    survey_date = db.Column(db.DateTime)
    fichier_technique_accessible = db.Column(db.Boolean, default=False)
 """


class InvalidStateTransition(Exception):
    """Raised when attempting an invalid state transition."""


class ImmutableStateError(Exception):
    """Raised when an action attempts to modify an immutable state (e.g. VALIDATED or CLOSED)."""


class PermissionError(Exception):
    """Raised when the acting user does not have permission to perform the transition."""


class Intervention(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    # Relations
    demande_id = db.Column(db.Integer, db.ForeignKey('demande_intervention.id'), nullable=False)
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipe.id'))
    motif_rejet = db.Column(db.String(512))
    accuse_reception = db.Column(db.Boolean, default=False)
    # Champs techniques

    # --- State machine configuration ---
    # Canonical states (used in code) mapped to DB 'statut' values for compatibility
    STATE_CREATED = 'CREATED'
    STATE_ASSIGNED = 'ASSIGNED'
    STATE_IN_PROGRESS = 'IN_PROGRESS'
    STATE_COMPLETED = 'COMPLETED'
    STATE_VALIDATED = 'VALIDATED'
    STATE_CLOSED = 'CLOSED'

    _STATE_TO_DB = {
        STATE_CREATED: 'nouveau',
        STATE_ASSIGNED: 'affecte',
        STATE_IN_PROGRESS: 'en_cours',
        STATE_COMPLETED: 'termine',
        STATE_VALIDATED: 'valide',
        STATE_CLOSED: 'cloture'
    }
    _DB_TO_STATE = {v: k for k, v in _STATE_TO_DB.items()}

    # Allowed transitions
    _ALLOWED_TRANSITIONS = {
        STATE_CREATED: {STATE_ASSIGNED},
        STATE_ASSIGNED: {STATE_IN_PROGRESS},
        STATE_IN_PROGRESS: {STATE_COMPLETED},
        STATE_COMPLETED: {STATE_VALIDATED},
        STATE_VALIDATED: {STATE_CLOSED},
        STATE_CLOSED: set()
    }

    # Roles mapping
    _MANAGER_ROLES = {'chef_pur', 'chef_pilote', 'manager'}  # 'manager' alias

    def _get_state(self):
        # Return canonical state name from DB 'statut' value.
        db_val = (self.statut or '').lower()
        return self._DB_TO_STATE.get(db_val, None)

    def _set_state(self, canonical_state):
        # Store canonical state into DB 'statut' using mapping. Creates the db value if unknown.
        db_val = self._STATE_TO_DB.get(canonical_state)
        if db_val is None:
            raise ValueError(f'Unknown state: {canonical_state}')
        self.statut = db_val

    # Expose state property
    state = property(_get_state, _set_state)

    def add_history(self, action, user=None, details=None):
        # Append a history entry (InterventionHistory model)
        try:
            ih = InterventionHistory(intervention_id=self.id, action=action, user_id=(user.id if user else None), details=details)
            db.session.add(ih)
            # Note: caller manages commit
        except Exception:
            current_app.logger.exception('Failed to add intervention history')

    def can_transition(self, target_state, user=None):
        """Return (True, None) if allowed; else (False, reason_string).

        Permissions rules (summary):
        - ASSIGNED: only manager/chef_zone can assign
        - IN_PROGRESS: technician owning the intervention can start; managers can also start on behalf
        - COMPLETED: technician can complete; manager may mark as completed
        - VALIDATED: only managers/chef_zone can validate
        - CLOSED: only managers
        """
        current = self.state
        # Only CLOSED is fully immutable (terminal); VALIDATED may still transition to CLOSED
        if current == self.STATE_CLOSED:
            return False, 'Intervention is immutable in its current state'
        if target_state not in self._ALLOWED_TRANSITIONS.get(current, set()):
            return False, f'Invalid transition from {current} to {target_state}'

        role = getattr(user, 'role', None) if user else None
        uid = getattr(user, 'id', None) if user else None

        # Role-based checks
        if target_state == self.STATE_ASSIGNED:
            if role not in self._MANAGER_ROLES and role != 'chef_zone':
                return False, 'Only managers or chefs de zone can assign interventions'
        elif target_state == self.STATE_IN_PROGRESS:
            if role == 'technicien':
                if self.technicien_id and uid != self.technicien_id:
                    return False, 'Technician can only start their own interventions'
            elif role not in self._MANAGER_ROLES and role != 'chef_zone':
                return False, 'Only technician or manager/chef_zone can mark intervention in progress'
        elif target_state == self.STATE_COMPLETED:
            if role == 'technicien':
                if self.technicien_id and uid != self.technicien_id:
                    return False, 'Technician can only complete their own interventions'
            elif role not in self._MANAGER_ROLES and role != 'chef_zone':
                return False, 'Only technician or manager/chef_zone can mark intervention completed'
        elif target_state == self.STATE_VALIDATED:
            # Ensure completeness is 100% before allowing validation
            score = getattr(self, 'completeness_score', None)
            if score is None:
                score = self.compute_completeness()
                self.completeness_score = score
            if score < 100:
                return False, f'Completeness check failed ({score}%) - required fields missing'
            if role not in self._MANAGER_ROLES and role != 'chef_zone':
                return False, 'Only managers or chefs de zone can validate interventions'
        elif target_state == self.STATE_CLOSED:
            if role not in self._MANAGER_ROLES:
                return False, 'Only managers can close interventions'

        return True, None

    def transition_state(self, target_state, user=None, details=None):
        """Perform a state transition with validation and history entry.

        Raises:
            InvalidStateTransition, ImmutableStateError, PermissionError
        """
        target_state = target_state if isinstance(target_state, str) else str(target_state)
        current = self.state
        # Normalize target
        if target_state not in self._STATE_TO_DB:
            raise InvalidStateTransition(f'Unknown target state: {target_state}')

        # Disallow modifications if already closed; allow VALIDATED->CLOSED
        if current == self.STATE_CLOSED:
            raise ImmutableStateError('Cannot modify a CLOSED intervention (terminal state)')
        if current == self.STATE_VALIDATED and target_state != self.STATE_CLOSED:
            raise ImmutableStateError('Cannot modify an intervention that is VALIDATED except to close it')

        allowed, reason = self.can_transition(target_state, user=user)
        if not allowed:
            # If reason includes permission, raise PermissionError else InvalidStateTransition
            if reason and ('Only' in reason or 'Technician' in reason):
                raise PermissionError(reason)
            raise InvalidStateTransition(reason or f'Transition {current}->{target_state} not allowed')

        # Apply transition
        old_state = current
        self._set_state(target_state)
        # Append history
        self.add_history(action=f'state:{old_state}->{target_state}', user=user, details=details)
        
        # Publish event for real-time updates
        try:
            from event_bus import publish_event, EventType
            # Map canonical state to event type
            state_to_event = {
                self.STATE_CREATED: EventType.INTERVENTION_CREATED,
                self.STATE_ASSIGNED: EventType.INTERVENTION_ASSIGNED,
                self.STATE_IN_PROGRESS: EventType.INTERVENTION_STARTED,
                self.STATE_COMPLETED: EventType.INTERVENTION_COMPLETED,
                self.STATE_VALIDATED: EventType.INTERVENTION_VALIDATED,
                self.STATE_CLOSED: EventType.INTERVENTION_CLOSED,
            }
            event_type = state_to_event.get(target_state, EventType.INTERVENTION_STATE_CHANGED)
            publish_event(
                event_type=event_type,
                entity_id=self.id,
                entity_type='intervention',
                user_id=user.id if user else None,
                zone_id=self.equipe_id,
                data={
                    'old_state': old_state,
                    'new_state': target_state,
                    'technicien_id': self.technicien_id,
                    'details': details,
                }
            )
        except Exception as e:
            current_app.logger.warning(f"Failed to publish state change event: {e}")
        
        # Caller must commit session

    numero = db.Column(db.String(50))
    constitutions = db.Column(db.String(100))
    valeur_pB0 = db.Column(db.String(50))
    nature_signalisation = db.Column(db.String(100))
    diagnostic_technicien = db.Column(db.Text)
    cause_derangement = db.Column(db.Text)
    action_releve = db.Column(db.Text)
    gps_lat = db.Column(db.String(50))
    gps_long = db.Column(db.String(50))
    
    # Matériel
    materiel_livre = db.Column(db.String(100))  # Ajouté pour correspondre au template
    materiel_recup = db.Column(db.String(100))
    numero_serie_livre = db.Column(db.String(100))
    numero_serie_recup = db.Column(db.String(100))

    # Champs ACCESSOIRES
    jarretiere = db.Column(db.String(50))
    nombre_type_bpe = db.Column(db.String(50))
    coupleur_c1 = db.Column(db.String(50))
    coupleur_c2 = db.Column(db.String(50))
    arobase = db.Column(db.String(50))
    malico = db.Column(db.String(50))
    type_cable = db.Column(db.String(50))
    lc_metre = db.Column(db.String(50))
    bti_metre = db.Column(db.String(50))
    pto_one = db.Column(db.String(50))
    kitpto_metre = db.Column(db.String(50))
    piton = db.Column(db.String(50))
    ds6 = db.Column(db.String(50))
    autres_accessoires = db.Column(db.String(100))
    
    # Tests services
    appel_sortant = db.Column(db.Boolean, default=False)
    envoi_numero = db.Column(db.String(20))
    appel_entrant = db.Column(db.Boolean, default=False)
    affichage_numero = db.Column(db.String(20))
    tvo_mono_ok = db.Column(db.Boolean, default=False)
    
    # Installation
    pieces = db.Column(db.Text)
    communes = db.Column(db.String(100))
    chambres = db.Column(db.Integer)  # Modifié pour correspondre au template
    bureau = db.Column(db.Integer)    # Modifié pour correspondre au template
    wifi_extender = db.Column(db.Boolean, default=False)
    
    # Tests débits (ajoutés pour correspondre au template)
    debit_cable_montant = db.Column(db.String(50))
    debit_mbs_descendant = db.Column(db.String(50))
    debit_mbs_ping = db.Column(db.String(50))
    debit_ms = db.Column(db.String(50))
    
    # Statut
    statut = db.Column(db.String(20), default='nouveau')  # nouveau, en_cours, termine, valide

    # Score de complétude (% entier 0-100)
    completeness_score = db.Column(db.Integer, default=0, nullable=False)

    # Required fields by demand type (used for completeness checks)
    _REQUIRED_FIELDS_BY_TYPE = {
        'Fibre': ['numero', 'diagnostic_technicien', 'pieces', 'debit_cable_montant'],
        'Cuivre': ['numero', 'diagnostic_technicien', 'pieces'],
        '5G': ['numero', 'diagnostic_technicien']
    }

    def required_fields(self):
        """Return list of required field names for this intervention based on demande.type_techno."""
        try:
            t = (self.demande.type_techno or '').strip()
        except Exception:
            t = None
        return self._REQUIRED_FIELDS_BY_TYPE.get(t, [])

    def compute_completeness(self):
        """Compute completeness score (0-100) based on required fields presence/values."""
        fields = self.required_fields()
        if not fields:
            return 100
        total = len(fields)
        present = 0
        for f in fields:
            val = getattr(self, f, None)
            if val is None:
                continue
            if isinstance(val, str) and val.strip() == '':
                continue
            present += 1
        score = int(round((present / total) * 100))
        return score

    def update_completeness(self):
        """Compute and persist completeness_score on the instance (caller commits)."""
        try:
            self.completeness_score = self.compute_completeness()
            db.session.add(self)
        except Exception:
            current_app.logger.exception('Failed to update completeness score')
    
    # Dates
    date_debut = db.Column(db.DateTime)
    date_fin = db.Column(db.DateTime)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_validation = db.Column(db.DateTime)
    
    # SLA fields
    sla_escalation_level = db.Column(db.Integer, default=0)
    sla_last_alerted_at = db.Column(db.DateTime)
    sla_acknowledged_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    sla_acknowledged_at = db.Column(db.DateTime)
    
    # Satisfaction
    satisfaction = db.Column(db.String(20))  # 1, 2, 3, 0 comme dans le template
    
    # Signatures
    signature_equipe = db.Column(db.Text)  # Stockage base64
    signature_client = db.Column(db.Text)  # Stockage base64
    
    # Validation
    valide_par = db.Column(db.Integer, db.ForeignKey('user.id'))
    commentaire_validation = db.Column(db.Text)

    photos = db.Column(db.Text)  # JSON ou chemins séparés par des virgules
    
    # Pour le service Production
    survey_ok = db.Column(db.Boolean)
    survey_date = db.Column(db.DateTime)
    fichier_technique_accessible = db.Column(db.Boolean, default=False)
    
    # Relations
    technicien = db.relationship('User', foreign_keys=[technicien_id], backref=db.backref('interventions_realisees', overlaps='interventions,technicien_user'), overlaps='interventions,technicien_user')
    valideur = db.relationship('User', foreign_keys=[valide_par], backref='interventions_validees')
    mesure_dbm = db.Column(db.String(10))
    histories = db.relationship('InterventionHistory', backref='intervention', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Intervention {self.id}>'


class InterventionHistory(db.Model):
    __tablename__ = 'intervention_history'

    id = db.Column(db.Integer, primary_key=True)
    intervention_id = db.Column(db.Integer, db.ForeignKey('intervention.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref='intervention_histories')


class NotificationSMS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    demande_id = db.Column(db.Integer, db.ForeignKey('demande_intervention.id', ondelete='CASCADE'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    type_notification = db.Column(db.String(20), nullable=False)  # affectation, rappel
    envoye = db.Column(db.Boolean, default=False)
    date_creation = db.Column(db.DateTime, default=utcnow)
    date_envoi = db.Column(db.DateTime)
    
    # Relations
    technicien = db.relationship('User', backref='notifications_sms')
    demande = db.relationship('DemandeIntervention', backref='notifications')

class UserConnectionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # 'login' ou 'logout'
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow)
    ip_address = db.Column(db.String(45))

    user = db.relationship('User', backref=db.backref('connection_logs', lazy=True))    

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # create, update, delete, login, logout, etc.
    module = db.Column(db.String(50), nullable=False)  # users, demandes, teams, interventions, etc.
    entity_id = db.Column(db.Integer)  # ID de l'entité concernée (optionnel)
    entity_name = db.Column(db.String(255))  # Nom descriptif de l'entité
    details = db.Column(db.Text)  # Détails supplémentaires en JSON
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))


class AuditLog(db.Model):
    """
    🔐 AUDIT TRAIL - Complete immutable record of all critical actions.
    
    Captures: intervention status changes, stock adjustments, SLA escalations
    Tracks: actor, action, timestamp, old/new values
    Guarantees: immutable, chronological, comprehensive
    
    Used for: compliance, debugging, audit, business intelligence
    """
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Action tracking
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Who did it
    action = db.Column(db.String(100), nullable=False)  # intervention_status_changed, stock_adjusted, sla_escalated, etc.
    entity_type = db.Column(db.String(50), nullable=False)  # intervention, stock, sla, leave_request, etc.
    entity_id = db.Column(db.Integer, nullable=False)  # ID of affected entity
    
    # Before/After state
    old_value = db.Column(db.Text, nullable=True)  # JSON: previous state
    new_value = db.Column(db.Text, nullable=True)  # JSON: new state
    
    # Context
    details = db.Column(db.Text, nullable=True)  # JSON: additional context
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Timestamps (immutable)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    actor = db.relationship('User', backref=db.backref('audit_logs', lazy=True))
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action} on {self.entity_type}/{self.entity_id}>'


class Categorie(db.Model):
    """
    Catégorie de produits (ex: Matériel réseau, Câbles, Accessoires, etc.)
    """
    __tablename__ = 'categorie'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_maj = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Categorie {self.nom}>'


class EmplacementStock(db.Model):
    """
    Emplacement physique dans l'entrepôt (ex: Rayon A, Étagère 1, etc.)
    Lié à une zone géographique pour l'isolation des données par zone
    """
    __tablename__ = 'emplacement_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Zone de l'emplacement (pour filtrage magasinier par zone)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=True)
    zone = db.relationship('Zone', foreign_keys=[zone_id], backref=db.backref('emplacements_stock', lazy='dynamic'))
    
    actif = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_maj = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Emplacement {self.code} - {self.designation}>'


class Fournisseur(db.Model):
    """
    Fournisseur de produits
    """
    __tablename__ = 'fournisseur'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    raison_sociale = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    adresse = db.Column(db.Text)
    actif = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_maj = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Fournisseur {self.code} - {self.raison_sociale}>'


class Produit(db.Model):
    """
    Produit en stock
    """
    __tablename__ = 'produits'  # Nom de la table dans la base de données
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(100), unique=True, nullable=False)
    code_barres = db.Column(db.String(100), unique=True, nullable=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Relations
    categorie_id = db.Column(db.Integer, db.ForeignKey('categorie.id'), nullable=True)
    categorie = db.relationship('Categorie', backref='produits')
    emplacement_id = db.Column(db.Integer, db.ForeignKey('emplacement_stock.id'), nullable=True)
    emplacement = db.relationship('EmplacementStock', backref='produits')
    
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseur.id'), nullable=True)
    fournisseur = db.relationship('Fournisseur', backref='produits')
    
    # Relation avec les mouvements de stock
    mouvements = db.relationship('MouvementStock', back_populates='produit_relation')
    
    # Prix
    prix_achat = db.Column(db.Numeric(10, 2), nullable=True)
    prix_vente = db.Column(db.Numeric(10, 2), nullable=True)
    tva = db.Column(db.Numeric(5, 2), nullable=True)
    
    # Gestion des stocks
    unite_mesure = db.Column(db.String(20), nullable=True)
    stock_min = db.Column(db.Integer, nullable=True)
    stock_max = db.Column(db.Integer, nullable=True)
    actif = db.Column(db.Boolean, default=True, nullable=False)
    
    # Suivi
    # Ces champs sont commentés car ils ne sont pas présents dans la base de données
    # cree_par = db.Column(db.Integer, db.ForeignKey('user.id'))
    # modifie_par = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<Produit {self.reference} - {self.nom}>'
    
    @property
    def prix_achat_formate(self):
        return f"{self.prix_achat or 0:,.2f} FCFA" if self.prix_achat else "N/A"
    
    @property
    def prix_vente_formate(self):
        return f"{self.prix_vente or 0:,.2f} FCFA" if self.prix_vente else "N/A"
    
    def quantite_par_emplacement(self, emplacement_id=None):
        """
        Calcule la quantité disponible pour un produit, éventuellement filtrée par emplacement
        
        Args:
            emplacement_id (int, optional): ID de l'emplacement pour filtrer. Si None, retourne le stock total.
                
        Returns:
            float: Quantité disponible pour le produit (et l'emplacement si spécifié)
        """
        from sqlalchemy import case, func, select, and_
        from models import MouvementStock

        # Construction de la requête de base
        query = select(
            func.sum(
                case(
                    (MouvementStock.type_mouvement == 'entree', MouvementStock.quantite),
                    (MouvementStock.type_mouvement == 'sortie', -MouvementStock.quantite),
                    else_=0
                )
            )
        ).where(
            MouvementStock.produit_id == self.id
        )
        
        # Filtrage par emplacement si spécifié
        if emplacement_id:
            query = query.where(MouvementStock.emplacement_id == emplacement_id)
        
        try:
            result = db.session.scalar(query)
            return float(result) if result is not None else 0.0
        except Exception as e:
            current_app.logger.error(f"Erreur dans la propriété quantite_par_emplacement: {str(e)}")
            return 0.0
    
    @property
    def quantite(self):
        """
        Propriété pour la rétrocompatibilité - retourne le stock total sans filtre d'emplacement
        """
        return self.quantite_par_emplacement()
    
    @property
    def seuil_alerte(self):
        # Retourne le stock minimum défini pour le produit ou 0 par défaut
        return self.stock_min if self.stock_min is not None else 0
    
    @property
    def statut_stock(self):
        quantite = self.quantite
        seuil = self.seuil_alerte
        
        if quantite <= 0:
            return 'danger'  # Rouge - Rupture de stock
        elif quantite <= seuil:
            return 'warning'  # Orange - Stock faible
        else:
            return 'success'  # Vert - Stock suffisant


class MouvementStock(db.Model):
    """
    Mouvement d'entrée ou de sortie de stock
    """
    __tablename__ = 'mouvement_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Type de mouvement (entrée, sortie, inventaire, etc.)
    type_mouvement = db.Column(db.Enum('entree', 'sortie', 'inventaire', 'ajustement', 'retour'), nullable=False)
    
    # Référence du document (bon de livraison, facture, etc.)
    reference = db.Column(db.String(100))
    date_reference = db.Column(db.Date)
    
    # Lien avec le produit
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    produit_relation = db.relationship('Produit', back_populates='mouvements')
    
    # Quantité et prix
    quantite = db.Column(db.Float, nullable=False)
    prix_unitaire = db.Column(db.Float)
    montant_total = db.Column(db.Float)
    
    # Lien avec l'utilisateur ayant effectué le mouvement
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    utilisateur = db.relationship('User', foreign_keys=[utilisateur_id], backref='mouvements_stock')
    
    # Lien avec le fournisseur (pour les entrées)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseur.id'))
    fournisseur = db.relationship('Fournisseur', backref='mouvements')
    
    # Lien avec l'emplacement de stock
    emplacement_id = db.Column(db.Integer, db.ForeignKey('emplacement_stock.id'), nullable=True)
    emplacement = db.relationship('EmplacementStock', backref='mouvements')
    
    # Informations complémentaires
    commentaire = db.Column(db.Text)
    date_mouvement = db.Column(db.DateTime, default=utcnow, nullable=False)
    
    # Pour les inventaires
    quantite_reelle = db.Column(db.Float)
    ecart = db.Column(db.Float)
    
    # ========== WORKFLOW STATE - NOUVEAU ==========
    workflow_state = db.Column(
        db.String(20),
        nullable=False,
        default='EN_ATTENTE',
        index=True
    )
    
    # Timestamps du workflow
    date_approbation = db.Column(db.DateTime)
    date_execution = db.Column(db.DateTime)
    date_validation = db.Column(db.DateTime)
    
    # Utilisateur qui a approuvé/rejeté
    approuve_par_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approuve_par = db.relationship('User', foreign_keys=[approuve_par_id], backref='mouvements_approuves')
    
    # Raison du rejet si applicable
    motif_rejet = db.Column(db.Text)
    
    # Anomalies détectées
    anomalies = db.Column(db.JSON)  # Liste des anomalies détectées lors du workflow
    
    # Flag: a été appliqué au stock?
    applique_au_stock = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        emplacement = f' - {self.emplacement.designation}' if self.emplacement else ''
        return f'<Mouvement {self.type_mouvement} - {self.produit_relation.nom} x{self.quantite}{emplacement}>'
    
    # ========== MÉTHODES WORKFLOW ==========
    
    def get_workflow_state(self):
        """Retourne l'état du workflow courant"""
        from workflow_stock import WorkflowState
        return WorkflowState(self.workflow_state)
    
    def change_state(self, new_state, user=None, reason=''):
        """Change l'état du workflow avec validation"""
        from workflow_stock import WorkflowValidator, WorkflowState, log_workflow_action
        
        current_state = WorkflowState(self.workflow_state)
        target_state = new_state if isinstance(new_state, WorkflowState) else WorkflowState(new_state)
        
        # Valider la transition
        is_valid, error_msg = WorkflowValidator.validate_state_transition(self, target_state, user)
        if not is_valid:
            raise ValueError(f"Transition invalide: {error_msg}")
        
        # Mettre à jour l'état
        old_state = self.workflow_state
        self.workflow_state = target_state.value
        
        # Enregistrer les timestamps selon le nouvel état
        now = datetime.utcnow()
        if target_state == WorkflowState.APPROUVE:
            self.date_approbation = now
            self.approuve_par_id = user.id if user else None
        elif target_state == WorkflowState.EXECUTE:
            self.date_execution = now
        elif target_state == WorkflowState.VALIDE:
            self.date_validation = now
        elif target_state == WorkflowState.REJETE:
            self.motif_rejet = reason
        
        # Logger l'action
        if user:
            log_workflow_action(self.id, 'state_change', user.id, reason, target_state)
        
        return old_state, target_state
    
    def check_anomalies(self):
        """Vérifie et enregistre les anomalies du mouvement"""
        from workflow_stock import WorkflowValidator
        
        anomalies = WorkflowValidator.check_for_anomalies(self)
        self.anomalies = anomalies if anomalies else None
        return anomalies
    
    def get_pending_approvals_count(self):
        """Retourne le nombre d'approbations requises"""
        from workflow_stock import WorkflowValidator
        return WorkflowValidator.get_required_approvals(self)
    
    def can_execute(self):
        """Vérifie si le mouvement peut être exécuté"""
        from workflow_stock import WorkflowState
        return self.workflow_state == WorkflowState.APPROUVE.value
    
    def is_final_state(self):
        """Vérifie si l'état est final (ne peut pas évoluer)"""
        from workflow_stock import WorkflowState
        return self.workflow_state in [
            WorkflowState.VALIDE.value,
            WorkflowState.ANNULE.value
        ]


class LigneMouvementStock(db.Model):
    """
    Ligne de mouvement de stock (pour les mouvements avec plusieurs produits)
    """
    __tablename__ = 'ligne_mouvement_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Lien avec le mouvement principal
    mouvement_id = db.Column(db.Integer, db.ForeignKey('mouvement_stock.id'), nullable=False)
    mouvement = db.relationship('MouvementStock', backref='lignes')
    
    # Lien avec le produit
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    produit = db.relationship('Produit', backref='lignes_mouvements')
    
    # Quantité et prix
    quantite = db.Column(db.Float, nullable=False)
    prix_unitaire = db.Column(db.Float)
    montant_total = db.Column(db.Float)
    
    # Numéro de série / lot (si applicable)
    numero_serie = db.Column(db.String(100))
    numero_lot = db.Column(db.String(100))
    date_peremption = db.Column(db.Date)
    
    # Pour les inventaires
    quantite_reelle = db.Column(db.Float)
    ecart = db.Column(db.Float)
    
    def __repr__(self):
        return f'<LigneMouvement {self.produit.nom} x{self.quantite}>'


class ReservationPiece(db.Model):
    """
    Réservation de pièces pour une intervention
    Permet de réserver des pièces en stock pour une intervention spécifique
    """
    __tablename__ = 'reservation_piece'
        
    # Statuts possibles d'une réservation
    STATUT_EN_ATTENTE = 'en_attente'
    STATUT_VALIDEE = 'validee'
    STATUT_ANNULEE = 'annulee'
    STATUT_UTILISEE = 'utilisee'
        
    # Statuts pour le technicien
    STATUT_TECH_EN_ATTENTE = 'en_attente'
    STATUT_TECH_VALIDE = 'valide'
    STATUT_TECH_REJETE = 'rejete'
    STATUT_TECH_UTILISE = 'utilise'
        
    id = db.Column(db.Integer, primary_key=True)
        
    # Référence à l'intervention
    intervention_id = db.Column(db.Integer, db.ForeignKey('intervention.id'), nullable=False)
    intervention = db.relationship('Intervention', backref=db.backref('reservations_pieces', lazy=True))
        
    # Référence au produit
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    produit = db.relationship('Produit', backref=db.backref('reservations', lazy=True))
        
    # Détails de la réservation
    quantite = db.Column(db.Float, nullable=False, default=1.0)
    statut = db.Column(db.String(20), nullable=False, default=STATUT_EN_ATTENTE)
    statut_technicien = db.Column(db.String(20), nullable=False, default=STATUT_TECH_EN_ATTENTE)
    commentaire = db.Column(db.Text)
        
    # Utilisateur ayant effectué la réservation
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    utilisateur = db.relationship('User', backref=db.backref('reservations_pieces', lazy=True))
        
    # Dates
    date_creation = db.Column(db.DateTime, default=utcnow, nullable=False)
    date_maj = db.Column(db.DateTime, onupdate=datetime.utcnow)
    date_validation = db.Column(db.DateTime)
    date_annulation = db.Column(db.DateTime)
        
    def __repr__(self):
        return f'<ReservationPiece {self.id} - {self.produit.nom} x{self.quantite} ({self.statut})>'
        
    @property
    def statut_libelle(self):
        """Retourne le libellé du statut"""
        statuts = {
            self.STATUT_EN_ATTENTE: 'En attente',
            self.STATUT_VALIDEE: 'Validée',
            self.STATUT_ANNULEE: 'Annulée',
            self.STATUT_UTILISEE: 'Utilisée'
        }
        return statuts.get(self.statut, 'Inconnu')
        
    def statut_technicien_libelle(self):
        """Retourne le libellé du statut technicien"""
        statuts = {
            self.STATUT_TECH_EN_ATTENTE: 'En attente',
            self.STATUT_TECH_VALIDE: 'Validé',
            self.STATUT_TECH_REJETE: 'Rejeté',
            self.STATUT_TECH_UTILISE: 'Utilisé'
        }
        return statuts.get(self.statut_technicien, 'Inconnu')
        
    def verifier_disponibilite(self):
        """
        Vérifie si la quantité demandée est disponible en stock
        Retourne un booléen indiquant la disponibilité
        """
        from sqlalchemy import func
        
        # Somme des quantités réservées pour ce produit, hors la réservation courante
        query = db.session.query(
            func.sum(ReservationPiece.quantite)
        ).filter(
            ReservationPiece.produit_id == self.produit_id,
            ReservationPiece.id != self.id,  # Exclure la réservation courante
            ReservationPiece.statut.in_([self.STATUT_EN_ATTENTE, self.STATUT_VALIDEE])
        ).scalar() or 0.0
        
        # Vérifier la quantité disponible en stock
        quantite_disponible = self.produit.quantite - float(query)
        return quantite_disponible >= self.quantite
        
    def valider(self, utilisateur_id):
        """
        Valide la réservation
        """
        if self.statut != self.STATUT_EN_ATTENTE:
            return False, "Seules les réservations en attente peuvent être validées"
            
        if not self.verifier_disponibilite():
            return False, "Quantité insuffisante en stock pour valider cette réservation"
            
        self.statut = self.STATUT_VALIDEE
        self.statut_technicien = self.STATUT_TECH_VALIDE
        self.date_validation = datetime.now(timezone.utc)
        self.utilisateur_id = utilisateur_id
        
        # Mettre à jour le commentaire pour inclure la date de validation
        self.commentaire = f"{self.commentaire or ''}\n\nValidé le {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} par l'utilisateur ID: {utilisateur_id}"
        
        try:
            db.session.commit()
            return True, "Réservation validée avec succès"
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de la validation de la réservation: {str(e)}"
            
    def annuler(self, motif=None, rejeter=False):
        """
        Annule la réservation
            
        Args:
            motif (str, optional): Motif de l'annulation
            rejeter (bool, optional): Si True, marque comme rejeté pour le technicien. Defaults to False.
                
        Returns:
            tuple: (succes, message)
        """
        if self.statut in [self.STATUT_ANNULEE, self.STATUT_UTILISEE]:
            return False, "Impossible d'annuler une réservation déjà annulée ou utilisée"
                
        self.statut = self.STATUT_ANNULEE
        self.statut_technicien = self.STATUT_TECH_REJETE if rejeter else self.STATUT_TECH_EN_ATTENTE
        self.date_annulation = datetime.now(timezone.utc)
            
        action = "Rejetée" if rejeter else "Annulée"
        self.commentaire = f"{self.commentaire or ''}\n\n{action} le {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}"
            
        if motif:
            self.commentaire += f"\nMotif: {motif}"
            
        try:
            db.session.commit()
            return True, f"Réservation {action.lower()} avec succès"
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de l'annulation de la réservation: {str(e)}"
            
    def marquer_comme_utilisee(self):
        """
        Marque la réservation comme utilisée (après sortie de stock)
        """
        if self.statut != self.STATUT_VALIDEE:
            return False, "Seules les réservations validées peuvent être marquées comme utilisées"
        
        # Vérifier que la quantité est disponible
        if not self.verifier_disponibilite():
            return False, "Quantité insuffisante en stock pour marquer cette réservation comme utilisée"
                
        # Créer un mouvement de sortie de stock
        try:
            # Construire la référence de l'intervention de manière plus robuste
            reference_intervention = 'Sans référence'
            if self.intervention:
                try:
                    # Essayer d'accéder à la référence via demande si elle existe
                    if hasattr(self.intervention, 'demande') and self.intervention.demande:
                        reference_intervention = getattr(self.intervention.demande, 'reference', f'Intervention #{self.intervention_id}')
                    else:
                        reference_intervention = f'Intervention #{self.intervention_id}'
                except Exception:
                    reference_intervention = f'Intervention #{self.intervention_id}'
            
            mouvement = MouvementStock(
                type_mouvement='sortie',
                reference=f'RES-{self.id}',
                date_reference=datetime.now(timezone.utc).date(),
                produit_id=self.produit_id,
                quantite=self.quantite,
                utilisateur_id=self.utilisateur_id,
                emplacement_id=self.produit.emplacement_id if self.produit and hasattr(self.produit, 'emplacement_id') else None,
                commentaire=f"Sortie pour {reference_intervention}",
                date_mouvement=datetime.now(timezone.utc)
            )
            db.session.add(mouvement)
            
            # Mettre à jour le statut de la réservation
            self.statut = self.STATUT_UTILISEE
            self.statut_technicien = self.STATUT_TECH_UTILISE
            
            # Mettre à jour le commentaire pour inclure la date d'utilisation
            self.commentaire = f"{self.commentaire or ''}\n\nMarquée comme utilisée le {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}"
            
            db.session.commit()
            return True, "Réservation marquée comme utilisée avec succès et stock mis à jour"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors du marquage de la réservation comme utilisée: {str(e)}"


# ============================================================================
# CLIENT - CLIENTS FINAUX
# ============================================================================

class Client(db.Model):
    """
    Représente un client FINAL installé avec du matériel sérialisé
    Lié à DemandeIntervention et NumeroSerie
    """
    __tablename__ = 'client'
    
    # Identifiant
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations personnelles
    nom = db.Column(db.String(100), nullable=False, index=True)
    prenom = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    telephone = db.Column(db.String(20), nullable=True)
    
    # Adresse
    adresse = db.Column(db.String(255), nullable=False)
    quartier = db.Column(db.String(100), nullable=True)
    commune = db.Column(db.String(100), nullable=True)
    
    # Informations Sonatel
    numero_ligne_sonatel = db.Column(db.String(50), nullable=True, unique=True, index=True)  # Identifiant Sonatel
    numero_demande = db.Column(db.String(50), nullable=True)  # Numéro de demande d'intervention
    offre = db.Column(db.String(100), nullable=True)  # Type d'offre souscrite
    
    # Statut contrat
    statut_contrat = db.Column(db.String(50), default='actif')  # actif, suspendu, resilie
    date_souscription = db.Column(db.DateTime, nullable=True)
    date_resilition = db.Column(db.DateTime, nullable=True)
    
    # Audit
    date_creation = db.Column(db.DateTime, default=utcnow, nullable=False)
    date_modification = db.Column(db.DateTime, onupdate=utcnow)
    
    def __repr__(self):
        return f'<Client {self.nom} {self.prenom} ({self.numero_ligne_sonatel})>'
    
    def get_nom_complet(self):
        """Retourne le nom complet du client"""
        if self.prenom:
            return f"{self.prenom} {self.nom}"
        return self.nom


# ============================================================================
# ZONE - ZONES GÉOGRAPHIQUES/ORGANISATIONNELLES
# ============================================================================

class Zone(db.Model):
    """
    Représente une zone géographique ou organisationnelle
    Les magasins, zones sont organisés par zone
    """
    __tablename__ = 'zone'
    
    # Identifiant
    id = db.Column(db.Integer, primary_key=True)
    
    # Zone info
    nom = db.Column(db.String(100), nullable=False, unique=True, index=True)  # Dakar, Pikine, Rufisque, etc.
    code = db.Column(db.String(20), nullable=False, unique=True)  # Zone code
    description = db.Column(db.Text, nullable=True)
    
    # Chef de zone
    chef_zone_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    chef_zone = db.relationship('User', foreign_keys=[chef_zone_id], backref=db.backref('zones_responsable'))
    
    # Localisation
    region = db.Column(db.String(100), nullable=True)
    
    # Statut
    actif = db.Column(db.Boolean, default=True)
    
    # Audit
    date_creation = db.Column(db.DateTime, default=utcnow, nullable=False)
    date_modification = db.Column(db.DateTime, onupdate=utcnow)
    
    def __repr__(self):
        return f'<Zone {self.nom} ({self.code})>'


# ============================================================================
# PHASE 3: NUMEROSERIE - TRAÇABILITÉ ARTICLES SÉRIALISÉS
# ============================================================================

class NumeroSerieStatut(enum.Enum):
    """États du numéro de série dans son cycle de vie"""
    EN_MAGASIN = 'EN_MAGASIN'              # Reçu, rangé magasin central
    ALLOUE_ZONE = 'ALLOUE_ZONE'            # Envoyé zone, reçu chef zone
    ALLOUE_TECHNICIEN = 'ALLOUE_TECHNICIEN'  # Affecté technicien pour intervention
    INSTALLEE = 'INSTALLEE'                # Installé chez client, en service
    RETOURNEE = 'RETOURNEE'                # Retour client (défaut, fin contrat)
    REBUT = 'REBUT'                        # État terminal - destruction


class NumeroSerieTypeTransition(enum.Enum):
    """Types de mouvements de numéro de série"""
    AFFECTATION_ZONE = 'affectation_zone'
    AFFECTATION_TECH = 'affectation_tech'
    INSTALLATION = 'installation'
    RETOUR = 'retour'
    REBUT_DESTRUCTION = 'rebut_destruction'


class NumeroSerie(db.Model):
    """
    Représente un exemplaire UNIQUE d'article sérialisé
    Suivi complet du cycle: réception → zone → technicien → installation client → retour
    """
    __tablename__ = 'numero_serie'
    
    # Identifiant
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(100), unique=True, nullable=False, index=True)  # SN-2024-0001234
    
    # Type article
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False, index=True)
    produit = db.relationship('Produit', backref=db.backref('numeros_serie', cascade='all, delete-orphan'))
    
    # Progression États
    statut = db.Column(db.Enum(NumeroSerieStatut), default=NumeroSerieStatut.EN_MAGASIN, nullable=False, index=True)
    date_entree = db.Column(db.DateTime, default=utcnow, nullable=False)
    
    # Localisation
    emplacement_id = db.Column(db.Integer, db.ForeignKey('emplacement_stock.id'), nullable=True)
    emplacement = db.relationship('EmplacementStock', backref=db.backref('numeros_serie'))
    
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=True)
    zone = db.relationship('Zone', backref=db.backref('numeros_serie_alloues'))
    
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    technicien = db.relationship('User', foreign_keys=[technicien_id], backref=db.backref('numeros_serie_alloues'))
    date_affectation_tech = db.Column(db.DateTime, nullable=True)
    
    # Installation
    date_installation = db.Column(db.DateTime, nullable=True)
    adresse_client = db.Column(db.String(255), nullable=True)
    numero_ligne_sonatel = db.Column(db.String(50), nullable=True)  # Ligne client Sonatel
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    client = db.relationship('Client', backref=db.backref('numeros_serie_installes'))
    
    # Retour
    date_retour = db.Column(db.DateTime, nullable=True)
    motif_retour = db.Column(db.String(255), nullable=True)  # défectueux, changement, fin contrat
    dossier_sav_id = db.Column(db.Integer, db.ForeignKey('dossier_sav.id'), nullable=True)
    dossier_sav = db.relationship('DossierSAV', foreign_keys='DossierSAV.numero_serie_id', backref=db.backref('numeros_serie_retournes'))
    
    # Destruction
    date_destruction = db.Column(db.DateTime, nullable=True)
    motif_destruction = db.Column(db.String(255), nullable=True)
    
    # Audit complet
    cree_par_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cree_par = db.relationship('User', foreign_keys=[cree_par_id], backref=db.backref('numeros_serie_crees'))
    date_creation = db.Column(db.DateTime, default=utcnow, nullable=False)
    
    modifie_par_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    modifie_par = db.relationship('User', foreign_keys=[modifie_par_id], backref=db.backref('numeros_serie_modifies'))
    date_modification = db.Column(db.DateTime, onupdate=utcnow)
    
    # Relations
    mouvements = db.relationship('MouvementNumeroSerie', backref=db.backref('numero_serie'), cascade='all, delete-orphan')
    historique_etats = db.relationship('HistoriqueEtatNumeroSerie', backref=db.backref('numero_serie'), cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<NumeroSerie {self.numero} - {self.statut.value}>'
    
    def get_statut_display(self):
        """Retourne le libellé du statut"""
        statut_display = {
            NumeroSerieStatut.EN_MAGASIN: 'En magasin',
            NumeroSerieStatut.ALLOUE_ZONE: 'Alloué zone',
            NumeroSerieStatut.ALLOUE_TECHNICIEN: 'Alloué technicien',
            NumeroSerieStatut.INSTALLEE: 'Installée',
            NumeroSerieStatut.RETOURNEE: 'Retournée',
            NumeroSerieStatut.REBUT: 'Rebut',
        }
        return statut_display.get(self.statut, self.statut.value)
    
    def get_statut_color(self):
        """Retourne couleur UI pour affichage"""
        color_map = {
            NumeroSerieStatut.EN_MAGASIN: 'primary',      # Bleu
            NumeroSerieStatut.ALLOUE_ZONE: 'info',        # Cyan
            NumeroSerieStatut.ALLOUE_TECHNICIEN: 'warning', # Orange
            NumeroSerieStatut.INSTALLEE: 'success',       # Vert
            NumeroSerieStatut.RETOURNEE: 'danger',        # Rouge
            NumeroSerieStatut.REBUT: 'dark',              # Gris
        }
        return color_map.get(self.statut, 'secondary')
    
    def peut_transitionner_vers(self, nouveau_statut):
        """Valide si transition est autorisée selon la règle métier"""
        transitions_valides = {
            NumeroSerieStatut.EN_MAGASIN: [NumeroSerieStatut.ALLOUE_ZONE],
            NumeroSerieStatut.ALLOUE_ZONE: [NumeroSerieStatut.ALLOUE_TECHNICIEN],
            NumeroSerieStatut.ALLOUE_TECHNICIEN: [NumeroSerieStatut.INSTALLEE, NumeroSerieStatut.RETOURNEE],
            NumeroSerieStatut.INSTALLEE: [NumeroSerieStatut.RETOURNEE],
            NumeroSerieStatut.RETOURNEE: [NumeroSerieStatut.REBUT, NumeroSerieStatut.EN_MAGASIN],  # Réparation possible
            NumeroSerieStatut.REBUT: [],  # Terminal
        }
        
        return nouveau_statut in transitions_valides.get(self.statut, [])
    
    def transition_vers(self, nouveau_statut, utilisateur_id, raison=None):
        """Effectue la transition d'état avec traçabilité complète"""
        if not self.peut_transitionner_vers(nouveau_statut):
            raise ValueError(f"Transition {self.statut.value} → {nouveau_statut.value} non autorisée")
        
        ancien_statut = self.statut
        self.statut = nouveau_statut
        self.modifie_par_id = utilisateur_id
        self.date_modification = utcnow()
        
        # Enregistrer dans historique
        historique = HistoriqueEtatNumeroSerie(
            numero_serie_id=self.id,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            date_transition=utcnow(),
            utilisateur_id=utilisateur_id,
            raison=raison
        )
        db.session.add(historique)
        
        return self
    
    def get_historique_timeline(self):
        """Retourne timeline complète des transitions"""
        timeline = []
        
        # Événement création
        timeline.append({
            'date': self.date_creation,
            'type': 'creation',
            'titre': 'Numéro de série créé',
            'utilisateur': self.cree_par.nom if self.cree_par else 'Système',
            'details': f'Article: {self.produit.nom if self.produit else "N/A"}'
        })
        
        # Transitions d'état
        for historique in sorted(self.historique_etats, key=lambda h: h.date_transition):
            timeline.append({
                'date': historique.date_transition,
                'type': 'transition_etat',
                'titre': f'{historique.ancien_statut.value} → {historique.nouveau_statut.value}',
                'utilisateur': historique.utilisateur.nom if historique.utilisateur else 'Système',
                'details': historique.raison or 'Transition standard'
            })
        
        # Mouvements
        for mouvement in sorted(self.mouvements, key=lambda m: m.date_mouvement):
            timeline.append({
                'date': mouvement.date_mouvement,
                'type': 'mouvement',
                'titre': f'Mouvement: {mouvement.type_transition.value}',
                'utilisateur': mouvement.utilisateur.nom if mouvement.utilisateur else 'Système',
                'details': mouvement.commentaire or ''
            })
        
        return sorted(timeline, key=lambda x: x['date'])


class HistoriqueEtatNumeroSerie(db.Model):
    """Enregistrement IMMUABLE de chaque changement d'état"""
    __tablename__ = 'historique_etat_numero_serie'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_serie_id = db.Column(db.Integer, db.ForeignKey('numero_serie.id'), nullable=False, index=True)
    
    ancien_statut = db.Column(db.Enum(NumeroSerieStatut), nullable=False)
    nouveau_statut = db.Column(db.Enum(NumeroSerieStatut), nullable=False)
    date_transition = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    utilisateur = db.relationship('User', backref=db.backref('transitions_numero_serie'))
    
    raison = db.Column(db.String(255), nullable=True)
    
    # Audit
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    
    def __repr__(self):
        return f'<HistoriqueEtat {self.ancien_statut.value} → {self.nouveau_statut.value} at {self.date_transition}>'


class MouvementNumeroSerie(db.Model):
    """Enregistrement des mouvements physiques de numéros de série"""
    __tablename__ = 'mouvement_numero_serie'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_serie_id = db.Column(db.Integer, db.ForeignKey('numero_serie.id'), nullable=False, index=True)
    
    type_transition = db.Column(db.Enum(NumeroSerieTypeTransition), nullable=False)
    
    # Localisation source → destination
    ancien_emplacement_id = db.Column(db.Integer, db.ForeignKey('emplacement_stock.id'), nullable=True)
    ancien_emplacement = db.relationship('EmplacementStock', foreign_keys=[ancien_emplacement_id])
    
    nouvel_emplacement_id = db.Column(db.Integer, db.ForeignKey('emplacement_stock.id'), nullable=True)
    nouvel_emplacement = db.relationship('EmplacementStock', foreign_keys=[nouvel_emplacement_id])
    
    # Personnel impliqué
    ancien_technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ancien_technicien = db.relationship('User', foreign_keys=[ancien_technicien_id])
    
    nouveau_technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    nouveau_technicien = db.relationship('User', foreign_keys=[nouveau_technicien_id])
    
    # Dates
    date_mouvement = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    utilisateur = db.relationship('User', foreign_keys=[utilisateur_id], backref=db.backref('mouvements_numero_serie'))
    
    # Détails
    commentaire = db.Column(db.Text, nullable=True)
    reference = db.Column(db.String(100), nullable=True)  # Bon mouvement, demande, etc.
    
    def __repr__(self):
        return f'<MouvementNumeroSerie {self.type_transition.value} at {self.date_mouvement}>'


class ImportHistoriqueNumeroSerie(db.Model):
    """Historique des imports de numéros de série Sonatel"""
    __tablename__ = 'import_historique_numero_serie'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Fichier source
    nom_fichier = db.Column(db.String(255), nullable=False)
    bon_livraison_ref = db.Column(db.String(100), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    produit = db.relationship('Produit', backref=db.backref('imports_numero_serie'))
    
    # Résultats
    nb_lignes_fichier = db.Column(db.Integer, nullable=False)
    nb_importe = db.Column(db.Integer, nullable=False)
    nb_erreurs = db.Column(db.Integer, nullable=False)
    nb_doublons = db.Column(db.Integer, nullable=False)
    
    # Rapport
    rapport = db.Column(db.JSON, nullable=True)  # Détails erreurs
    
    # Audit
    date_import = db.Column(db.DateTime, default=utcnow, nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    utilisateur = db.relationship('User', backref=db.backref('imports_numero_serie'))
    
    # Fichier source archivé
    contenu_fichier = db.Column(db.LargeBinary, nullable=True)  # Backup fichier source
    
    statut = db.Column(db.String(50), default='termine')  # en_cours, termine, erreur
    
    def __repr__(self):
        return f'<ImportHistoriqueNumeroSerie {self.bon_livraison_ref} - {self.nb_importe} importés>'


class DossierSAV(db.Model):
    """Dossiers Support After-Sales pour articles retournés"""
    __tablename__ = 'dossier_sav'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_dossier = db.Column(db.String(50), unique=True, nullable=False)  # SAV-2024-XXXXX
    
    # Numéro de série retourné
    numero_serie_id = db.Column(db.Integer, db.ForeignKey('numero_serie.id'), nullable=False)
    
    # Client
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    client = db.relationship('Client', backref=db.backref('dossiers_sav'))
    
    # Intervention d'origine
    intervention_id = db.Column(db.Integer, db.ForeignKey('intervention.id'), nullable=True)
    intervention = db.relationship('Intervention', backref=db.backref('dossiers_sav'))
    
    # Motif retour
    motif_retour = db.Column(db.String(255), nullable=False)  # défectueux, changement, etc.
    description_probleme = db.Column(db.Text, nullable=True)
    date_ouverture = db.Column(db.DateTime, default=utcnow, nullable=False)
    
    # Résolution
    statut = db.Column(db.String(50), default='ouvert')  # ouvert, en_cours, resolu, rejete
    date_resolution = db.Column(db.DateTime, nullable=True)
    resolution = db.Column(db.Text, nullable=True)
    
    # Remplacement
    numero_serie_remplacement_id = db.Column(db.Integer, db.ForeignKey('numero_serie.id'), nullable=True)
    numero_serie_remplacement = db.relationship('NumeroSerie', foreign_keys=[numero_serie_remplacement_id])
    
    # Audit
    cree_par_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cree_par = db.relationship('User', foreign_keys=[cree_par_id], backref=db.backref('dossiers_sav_crees'))
    date_creation = db.Column(db.DateTime, default=utcnow, nullable=False)
    
    def __repr__(self):
        return f'<DossierSAV {self.numero_dossier}>'


class TokenBlacklist(db.Model):
    """Tokens JWT révoqués/blacklistés pour le logout sécurisé"""
    __tablename__ = 'token_blacklist'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)  # JWT ID
    token_type = db.Column(db.String(10))  # 'access' ou 'refresh'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    blacklisted_on = db.Column(db.DateTime, default=utcnow, nullable=False)
    revoke_reason = db.Column(db.String(255))  # Motif de révocation
    
    def __repr__(self):
        return f'<TokenBlacklist {self.jti[:8]}... user_id={self.user_id} reason={self.revoke_reason}>'