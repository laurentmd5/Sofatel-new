from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
    StringField, PasswordField, SelectField, TextAreaField, BooleanField, 
    DateField, HiddenField, IntegerField, TimeField, SubmitField
)
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, ValidationError, NumberRange
from wtforms.widgets import TextArea
from wtforms.fields import DecimalField, FloatField, SelectField
from models import Produit, Intervention
from flask_login import current_user

class ProduitForm(FlaskForm):
    """
    Formulaire pour l'ajout et la modification de produits
    """
    reference = StringField('Référence', validators=[
        DataRequired(),
        Length(max=100, message='La référence ne peut pas dépasser 100 caractères')
    ])
    code_barres = StringField('Code-barres', validators=[
        Optional(),
        Length(max=100, message='Le code-barres ne peut pas dépasser 100 caractères')
    ])
    nom = StringField('Nom', validators=[
        DataRequired(),
        Length(max=200, message='Le nom ne peut pas dépasser 200 caractères')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    
    # Champs de relation
    categorie_id = SelectField('Catégorie', coerce=int, validators=[DataRequired()])
    fournisseur_id = SelectField('Fournisseur', coerce=int, validators=[Optional()])
    emplacement_id = SelectField('Emplacement de stock', coerce=int, validators=[Optional()])
    
    # Champs de prix
    prix_achat = DecimalField('Prix d\'achat', 
        places=2, 
        validators=[
            Optional(),
            NumberRange(min=0, message='Le prix d\'achat ne peut pas être négatif')
        ],
        default=0.0
    )
    prix_vente = DecimalField('Prix de vente', 
        places=2, 
        validators=[
            Optional(),
            NumberRange(min=0, message='Le prix de vente ne peut pas être négatif')
        ],
        default=0.0
    )
    tva = DecimalField('TVA (%)', 
        places=2, 
        validators=[
            Optional(),
            NumberRange(min=0, max=100, message='La TVA doit être entre 0 et 100%')
        ],
        default=0.0
    )
    
    # Gestion des stocks
    quantite = DecimalField('Quantité en stock', 
        places=2, 
        validators=[
            Optional(),
            NumberRange(min=0, message='La quantité ne peut pas être négative')
        ],
        default=0.0
    )
    
    unite_mesure = StringField('Unité de mesure', validators=[
        Optional(),
        Length(max=20, message='L\'unité de mesure ne peut pas dépasser 20 caractères')
    ])
    stock_min = IntegerField('Stock minimum', 
        validators=[
            Optional(),
            NumberRange(min=0, message='Le stock minimum ne peut pas être négatif')
        ],
        default=0
    )
    stock_max = IntegerField('Stock maximum', 
        validators=[
            Optional(),
            NumberRange(min=0, message='Le stock maximum ne peut pas être négatif')
        ],
        default=0
    )
    
    # Statut
    actif = BooleanField('Produit actif', default=True)
    
    def __init__(self, *args, **kwargs):
        from models import Categorie, Fournisseur, EmplacementStock
        from sqlalchemy import text
        super(ProduitForm, self).__init__(*args, **kwargs)
        
        # Remplir les choix des catégories
        self.categorie_id.choices = [(c.id, c.nom) for c in Categorie.query.order_by(text('nom')).all()]
        
        # Remplir les choix des fournisseurs
        self.fournisseur_id.choices = [(0, 'Aucun')] + [
            (f.id, f.raison_sociale) 
            for f in Fournisseur.query.filter_by(actif=True).order_by(text('raison_sociale')).all()
        ]
        
        # Remplir les choix des emplacements de stock actifs
        self.emplacement_id.choices = [(0, 'Non spécifié')] + [
            (e.id, e.designation)
            for e in EmplacementStock.query.filter_by(actif=True).order_by(text('designation')).all()
        ]
        
        # Remplir les choix des fournisseurs (en utilisant raison_sociale au lieu de nom)
        self.fournisseur_id.choices = [(0, 'Aucun')] + [(f.id, f.raison_sociale) for f in Fournisseur.query.order_by(text('raison_sociale')).all()]


class FournisseurForm(FlaskForm):
    """
    Formulaire pour l'ajout et la modification de fournisseurs
    """
    code = StringField('Code fournisseur', validators=[
        DataRequired(),
        Length(max=20, message='Le code ne peut pas dépasser 20 caractères')
    ])
    raison_sociale = StringField('Nom', validators=[
        DataRequired(),
        Length(max=200, message='Le nom ne peut pas dépasser 200 caractères')
    ])
    contact = StringField('Contact', validators=[
        Length(max=100, message='Le contact ne peut pas dépasser 100 caractères')
    ])
    telephone = StringField('Téléphone', validators=[
        Length(max=20, message='Le numéro de téléphone ne peut pas dépasser 20 caractères')
    ])
    email = StringField('Email', validators=[
        Email(),
        Length(max=100, message='L\'email ne peut pas dépasser 100 caractères')
    ])
    adresse = TextAreaField('Adresse')
    actif = BooleanField('Fournisseur actif', default=True)


class FicheTechniqueForm(FlaskForm):
    # Informations générales
    nom_raison_sociale = StringField('Nom/Raison sociale', validators=[DataRequired()])
    contact = StringField('Contact', validators=[DataRequired()])
    represente_par = StringField('Représenté par', validators=[DataRequired()])
    date_installation = DateField('Date d\'installation', validators=[DataRequired()])
    tel1 = StringField('Téléphone 1', validators=[DataRequired()])
    tel2 = StringField('Téléphone 2', validators=[Optional()])
    adresse_demandee = StringField('Adresse', validators=[DataRequired()])
    etage = StringField('Étage', validators=[DataRequired()])
    gps_lat = StringField('Latitude GPS', validators=[DataRequired()])
    gps_long = StringField('Longitude GPS', validators=[DataRequired()])
    type_logement_avec_bpi = TextAreaField('Type logement avec BPI', validators=[DataRequired()])
    type_logement_sans_bpi = TextAreaField('Type logement sans BPI', validators=[DataRequired()])
    h_arrivee = TimeField('Heure d\'arrivée', validators=[DataRequired()])
    h_depart = TimeField('Heure de départ', validators=[DataRequired()])
    
    # Informations techniques
    n_ligne = StringField('N° Ligne', validators=[DataRequired()])
    n_demande = StringField('N° Demande', validators=[DataRequired()])
    technicien_structure = StringField('Technicien structure', validators=[DataRequired()])
    pilote_structure = StringField('Pilote structure', validators=[DataRequired()])
    offre = StringField('Offre', validators=[DataRequired()])
    debit = StringField('Débit', validators=[DataRequired()])
    type_mc = BooleanField('MC')
    type_na = BooleanField('NA')
    type_transfert = BooleanField('Transfert')
    type_autre = BooleanField('Autre')
    backoffice_structure = StringField('Backoffice structure', validators=[DataRequired()])
    
    # Matériels
    type_ont = StringField('Type ONT', validators=[DataRequired()])
    nature_ont = StringField('Nature ONT', validators=[DataRequired()])
    numero_serie_ont = StringField('N° série ONT', validators=[DataRequired()])
    type_decodeur = StringField('Type décodeur', validators=[DataRequired()])
    nature_decodeur = StringField('Nature décodeur', validators=[DataRequired()])
    numero_serie_decodeur = StringField('N° série décodeur', validators=[DataRequired()])
    disque_dur = BooleanField('Disque dur')
    telephone = BooleanField('Téléphone')
    recepteur_wifi = BooleanField('Récepteur WiFi')
    cpl = BooleanField('CPL')
    carte_vaccess = BooleanField('Carte V-Access')
    
    # Accessoires
    type_cable_lc = StringField('Type câble LC', validators=[DataRequired()])
    type_cable_bti = StringField('Type câble BTI', validators=[DataRequired()])
    type_cable_pto_one = StringField('Type câble PTO ONE', validators=[DataRequired()])
    kit_pto = BooleanField('Kit PTO')
    piton = BooleanField('Piton')
    arobase = BooleanField('Arobase')
    malico = BooleanField('Malico')
    ds6 = BooleanField('DS6')
    autre_accessoire = StringField('Autre accessoire', validators=[DataRequired()])
    
    # Tests de services
    appel_sortant_ok = BooleanField('Appel sortant OK')
    appel_sortant_nok = BooleanField('Appel sortant NOK')
    appel_entrant_ok = BooleanField('Appel entrant OK')
    appel_entrant_nok = BooleanField('Appel entrant NOK')
    tvo_mono_ok = BooleanField('TVO mono OK')
    tvo_mono_nok = BooleanField('TVO mono NOK')
    tvo_multi_ok = BooleanField('TVO multi OK')
    tvo_multi_nok = BooleanField('TVO multi NOK')
    enregistreur_dd_ok = BooleanField('Enregistreur DD OK')
    enregistreur_dd_nok = BooleanField('Enregistreur DD NOK')
    
    # Tests de débits
    par_cable_salon = StringField('Débit câble - Salon', validators=[DataRequired()])
    par_cable_chambres = StringField('Débit câble - Chambres', validators=[DataRequired()])
    par_cable_bureau = StringField('Débit câble - Bureau', validators=[DataRequired()])
    par_cable_autres = StringField('Débit câble - Autres', validators=[DataRequired()])
    par_cable_vitesse_wifi = StringField('Vitesse WiFi câble', validators=[DataRequired()])
    par_cable_mesure_mbps = IntegerField('Mesure Mbps câble', validators=[DataRequired()])
    par_wifi_salon = StringField('Débit WiFi - Salon', validators=[DataRequired()])
    par_wifi_chambres = StringField('Débit WiFi - Chambres', validators=[DataRequired()])
    par_wifi_bureau = StringField('Débit WiFi - Bureau', validators=[DataRequired()])
    par_wifi_autres = StringField('Débit WiFi - Autres', validators=[DataRequired()])
    par_wifi_vitesse_wifi = StringField('Vitesse WiFi', validators=[DataRequired()])
    par_wifi_mesure_mbps = IntegerField('Mesure Mbps WiFi', validators=[DataRequired()])
    
    # Etiquetages et Nettoyage
    etiquetage_colliers_serres = BooleanField('Étiquetage colliers serrés')
    etiquetage_pbo_normalise = BooleanField('Étiquetage PBO normalisé')
    nettoyage_depose = BooleanField('Nettoyage dépose')
    nettoyage_tutorat = BooleanField('Nettoyage tutorat')
    
    # Rattachement
    rattachement_nro = StringField('NRO', validators=[DataRequired()])
    rattachement_type = StringField('Type', validators=[DataRequired()])
    rattachement_num_carte = StringField('N° Carte', validators=[DataRequired()])
    rattachement_num_port = StringField('N° Port', validators=[DataRequired()])
    rattachement_plaque = StringField('Plaque', validators=[DataRequired()])
    rattachement_bpi_pbo = StringField('BPI/PBO', validators=[DataRequired()])
    rattachement_coupleur = StringField('Coupleur', validators=[DataRequired()])
    rattachement_fibre = StringField('Fibre', validators=[DataRequired()])
    rattachement_ref_dbm = StringField('Référence dBm', validators=[DataRequired()])
    rattachement_mesure_dbm = StringField('Mesure dBm', validators=[DataRequired()])
    
    # Commentaires
    commentaires = TextAreaField('Commentaires', validators=[DataRequired()])
    photos = FileField('Photos', validators=[DataRequired()])
    # Signatures et satisfaction client
    signature_equipe = HiddenField('Signature équipe')
    signature_client = HiddenField('Signature client')
    client_tres_satisfait = BooleanField('Très satisfait')
    client_satisfait = BooleanField('Satisfait')
    client_pas_satisfait = BooleanField('Pas satisfait')

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Mot de passe', validators=[DataRequired()])


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Envoyer le lien')      


from datetime import date

class TeamForm(FlaskForm):
    nom_equipe = StringField("Nom d'équipe", validators=[DataRequired(), Length(max=100)], render_kw={"id": "nom_equipe"})
    date_creation = DateField('Date de création', validators=[Optional()], default=date.today, render_kw={"id": "date_creation"})
    technologies = SelectField('Technologies', choices=[
        ('', 'Sélectionner les technologies'),
        ('Fibre', 'Fibre'),
        ('Cuivre', 'Cuivre'),
        ('5G', '5G'),
        ('Fibre,Cuivre', 'Fibre + Cuivre'),
        ('Fibre,5G', 'Fibre + 5G'),
        ('Fibre,Cuivre,5G', 'Toutes technologies')
    ], validators=[Optional()], render_kw={"id": "technologies"})
    
    # Définir le champ zone avec coerce=int pour accepter des IDs
    zone = SelectField('Zone', coerce=int, validators=[DataRequired(message="La zone est obligatoire")], render_kw={"id": "zone"})
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Charger dynamiquement les zones depuis la base de données
        from models import Zone
        toutes_zones = Zone.query.order_by(Zone.nom).all()
        zones = [z for z in toutes_zones if getattr(z, 'actif', True)]
        
        # Créer les choix pour le SelectField
        zone_choices = [(0, 'Sélectionner une zone')]
        for zone in zones:
            zone_choices.append((zone.id, f"{zone.nom} ({zone.code})"))
        
        # Mettre à jour les choix du champ zone
        self.zone.choices = zone_choices
        
        print(f"DEBUG: Zones chargées pour TeamForm: {len(zone_choices)} zones")
        for zone_id, zone_text in zone_choices:
            print(f"  - {zone_id}: {zone_text}")
    
    service = SelectField('Service', choices=[
        ('', 'Sélectionner un service'),
        ('SAV', 'SAV'), 
        ('Production', 'Production'),
        ('SAV,Production', 'SAV + Production')
    ], validators=[Optional()], render_kw={"id": "service"})
    prestataire = SelectField('Prestataire', choices=[
        ('', 'Aucun'),
        ('Netsysteme', 'Netsysteme'),
        ('Autres', 'Autres')
    ], validators=[Optional()], render_kw={"id": "prestataire-select"})


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nouveau mot de passe', validators=[DataRequired()])
    submit = SubmitField('Réinitialiser')

class ImportDemandesForm(FlaskForm):
    fichier_excel = FileField('Fichier Excel', validators=[
        FileRequired(),
        FileAllowed(['xlsx', 'xls'], 'Seuls les fichiers Excel sont autorisés!')
    ])
    service = SelectField('Service', choices=[], validators=[DataRequired()])

    def __init__(self, service_choices=None, default_service=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Définir les choix de service
        if service_choices:
            self.service.choices = service_choices
        else:
            self.service.choices = [('SAV', 'SAV'), ('Production', 'Production')]
        
        # Définir la valeur par défaut si fournie
        if default_service:
            self.service.data = default_service
            
class DispatchingForm(FlaskForm):
    demande_id = HiddenField('ID Demande', validators=[DataRequired()])
    technicien_id = SelectField('Technicien', coerce=int, validators=[DataRequired()])
    equipe_id = SelectField('Équipe', coerce=int, validators=[Optional()])
    commentaire = TextAreaField('Commentaire', validators=[Optional()])

class CreateEquipeForm(FlaskForm):
    nom_equipe = StringField('Nom de l\'équipe', validators=[DataRequired(), Length(max=100)])
    zone = SelectField('Zone', choices=[
        ('Dakar', 'Dakar'),
        ('Mbour', 'Mbour'),
        ('Kaolack', 'Kaolack'),
        ('Autres', 'Autres')
    ], validators=[DataRequired()])
    prestataire = SelectField('Prestataire', choices=[
        ('', 'Aucun'),
        ('Netsysteme', 'Netsysteme'),
        ('Autres', 'Autres')
    ], validators=[Optional()])
    technologies = SelectField('Technologies', choices=[
        ('Fibre', 'Fibre'),
        ('Cuivre', 'Cuivre'),
        ('5G', '5G'),
        ('Fibre,Cuivre', 'Fibre + Cuivre'),
        ('Fibre,5G', 'Fibre + 5G'),
        ('Cuivre,5G', 'Cuivre + 5G'),
        ('Fibre,Cuivre,5G', 'Toutes technologies')
    ], validators=[DataRequired()])
    service = SelectField('Service', choices=[
        ('SAV', 'SAV'), 
        ('Production', 'Production'),
        ('SAV,Production', 'SAV + Production')
    ], validators=[DataRequired()])
    date_creation = DateField('Date', validators=[DataRequired()])

class EditEquipeForm(FlaskForm):
    zone = SelectField('Zone', choices=[
        ('Dakar', 'Dakar'),
        ('Mbour', 'Mbour'),
        ('Kaolack', 'Kaolack'),
        ('Autres', 'Autres')
    ], validators=[DataRequired()])
    prestataire = SelectField('Prestataire', choices=[
        ('', 'Aucun'),
        ('Netsysteme', 'Netsysteme'),
        ('Autres', 'Autres')
    ], validators=[Optional()])
    technologies = SelectField('Technologies', choices=[
        ('Fibre', 'Fibre'),
        ('Cuivre', 'Cuivre'),
        ('5G', '5G'),
        ('Fibre,Cuivre', 'Fibre + Cuivre'),
        ('Fibre,5G', 'Fibre + 5G'),
        ('Cuivre,5G', 'Cuivre + 5G'),
        ('Fibre,Cuivre,5G', 'Toutes technologies')
    ], validators=[DataRequired()])
    service = SelectField('Service', choices=[
        ('SAV', 'SAV'), 
        ('Production', 'Production'),
        ('SAV,Production', 'SAV + Production')
    ], validators=[DataRequired()])

class EntreeStockForm(FlaskForm):
    """
    Formulaire pour gérer les entrées en stock
    """
    quantite = FloatField('Quantité', validators=[
        DataRequired(message='La quantité est requise'),
        NumberRange(min=0.01, message='La quantité doit être supérieure à zéro')
    ])
    prix_unitaire = FloatField('Prix unitaire', validators=[
        Optional(),
        NumberRange(min=0, message='Le prix unitaire ne peut pas être négatif')
    ])
    emplacement_id = SelectField('Emplacement de stockage', coerce=int, validators=[
        DataRequired(message='Veuillez sélectionner un emplacement de stockage')
    ])
    commentaire = TextAreaField('Commentaire', validators=[Optional()])

class SortieStockForm(FlaskForm):
    """
    Formulaire pour gérer les sorties de stock
    """
    quantite = FloatField('Quantité', validators=[
        DataRequired(message='La quantité est requise'),
        NumberRange(min=0.01, message='La quantité doit être supérieure à zéro')
    ])
    prix_vente = FloatField('Prix de vente', validators=[
        Optional(),
        NumberRange(min=0, message='Le prix de vente ne peut pas être négatif')
    ])
    emplacement_id = SelectField('Emplacement de stockage', coerce=int, validators=[
        DataRequired(message='Veuillez sélectionner un emplacement de stockage')
    ])
    motif = SelectField('Motif de sortie', validators=[
        DataRequired(message='Le motif de sortie est obligatoire')
    ], choices=[
        ('', '-- Sélectionner un motif --'),
        ('vente_client', 'Vente client'),
        ('sav_retour', 'SAV/Retour'),
        ('perte_casse', 'Perte/Casse'),
        ('autre_zone', 'Destination autre zone'),
        ('ecart_inventaire', 'Écart inventaire'),
        ('autre', 'Autre')
    ])
    commentaire = TextAreaField('Commentaire/Détails', validators=[Optional()])

class ReservationPieceForm(FlaskForm):
    """
    Formulaire pour la réservation de pièces pour une intervention
    """
    produit_id = SelectField('Pièce à réserver', coerce=int, validators=[DataRequired()])
    quantite = FloatField('Quantité', validators=[
        DataRequired(message='La quantité est requise'),
        NumberRange(min=0.01, message='La quantité doit être supérieure à zéro')
    ])
    commentaire = TextAreaField('Commentaire', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(ReservationPieceForm, self).__init__(*args, **kwargs)
        # Remplir la liste déroulante des produits disponibles
        self.produit_id.choices = [(p.id, f"{p.reference} - {p.nom} (Stock: {p.quantite})") 
                                 for p in Produit.query.filter(Produit.quantite > 0).order_by(Produit.nom).all()]
    
    def validate_quantite(self, field):
        produit = db.session.get(Produit, self.produit_id.data)
        if produit and field.data > produit.quantite:
            raise ValidationError(f'Quantité indisponible. Stock actuel: {produit.quantite}')


class MembreEquipeForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    prenom = StringField('Prénom', validators=[DataRequired(), Length(max=100)])
    telephone = StringField('Téléphone', validators=[DataRequired(), Length(max=20)])
    type_membre = SelectField('Type', choices=[('technicien', 'Technicien'), ('accompagnant', 'Accompagnant')], validators=[DataRequired()])
    technicien_id = SelectField('Technicien (si applicable)', coerce=int, validators=[Optional()])

""" class InterventionForm(FlaskForm):
    # Champs techniques
    numero = StringField('Numéro', validators=[Optional(), Length(max=50)])
    constitutions = StringField('Constitutions', validators=[Optional(), Length(max=100)])
    valeur_pB0 = StringField('Valeur pB0', validators=[Optional(), Length(max=50)])
    nature_signalisation = StringField('Nature signalisation', validators=[Optional(), Length(max=100)])
    diagnostic_technicien = TextAreaField('Diagnostic technicien', validators=[Optional()])
    cause_derangement = TextAreaField('Cause dérangement', validators=[Optional()])
    action_releve = TextAreaField('Action relevé', validators=[Optional()])
    
    # Matériel
    materiel_recup = StringField('Matériel livré', validators=[Optional(), Length(max=100)])
    numero_serie_livre = StringField('N° série livré', validators=[Optional(), Length(max=100)])
    materiel_recupere = StringField('Matériel récupéré', validators=[Optional(), Length(max=100)])
    numero_serie_recup = StringField('N° série récupéré', validators=[Optional(), Length(max=100)])
    
    # Tests
    appel_sortant = BooleanField('Appel sortant')
    envoi_numero = StringField('Envoi numéro', validators=[Optional(), Length(max=20)])
    appel_entrant = BooleanField('Appel entrant')
    affichage_numero = StringField('Affichage numéro', validators=[Optional(), Length(max=20)])
    tvo_mono_ok = BooleanField('TVO mono OK')
    
    # Installation
    pieces = TextAreaField('Pièces', validators=[Optional()])
    communes = StringField('Communes', validators=[Optional(), Length(max=100)])
    chambres = StringField('Chambres', validators=[Optional(), Length(max=100)])
    bureau = StringField('Bureau', validators=[Optional(), Length(max=100)])
    wifi_extender = BooleanField('WiFi extender')
    
    # Satisfaction
    satisfaction = SelectField('Satisfaction client', choices=[
        ('', 'Non renseigné'),
        ('excellent', 'Excellent'),
        ('bon', 'Bon'),
        ('moyen', 'Moyen'),
        ('mauvais', 'Mauvais')
    ], validators=[Optional()])
    
    # Signatures (seront gérées en JavaScript)
    signature_equipe = HiddenField('Signature équipe')
    signature_client = HiddenField('Signature client')
 """

class SurveyForm(FlaskForm):
    # Informations générales
    date_survey = DateField('Date du Survey*', validators=[DataRequired()])
    nom_raison_sociale = StringField('Nom/Raison sociale*', validators=[DataRequired()])
    contact = StringField('Contact*', validators=[DataRequired()])
    represente_par = StringField('Représenté par*', validators=[DataRequired()])
    tel1 = StringField('Téléphone 1*', validators=[DataRequired()])
    tel2 = StringField('Téléphone 2', validators=[Optional()])
    adresse_demande = StringField('Adresse*', validators=[DataRequired()])
    etage = StringField('Étage*', validators=[DataRequired()])
    gps_lat = StringField('Latitude GPS*', validators=[DataRequired()])
    gps_long = StringField('Longitude GPS*', validators=[DataRequired()])
    h_debut = StringField('Heure début*', validators=[DataRequired()])
    h_fin = StringField('Heure fin*', validators=[DataRequired()])

    # Champs techniques
    n_ligne = StringField('N° Ligne*', validators=[DataRequired()])
    n_demande = StringField('N° Demande*', validators=[DataRequired()])
    service_demande = SelectField('Service demandé*', choices=[
        ('', 'Sélectionner...'),
        ('Internet Fibre', 'Internet Fibre'),
        ('Internet Cuivre', 'Internet Cuivre'),
        ('Analogique', 'Analogique'),
        ('RNIS', 'RNIS'),
        ('Leased Line', 'Leased Line')
    ], validators=[DataRequired()])
    
    # État du client
    etat_client = SelectField('État du client*', choices=[
        ('', 'Sélectionner...'),
        ('Nouveau', 'Nouveau'),
        ('Migration', 'Migration'),
        ('En service', 'En service')
    ], validators=[DataRequired()])

    # Localisation
    nature_local = SelectField('Nature du local*', choices=[
        ('', 'Sélectionner...'),
        ('Appartement', 'Appartement'),
        ('Villa', 'Villa'),
        ('Bureau', 'Bureau'),
        ('Commerce', 'Commerce'),
        ('Autre', 'Autre')
    ], validators=[DataRequired()])
    type_logement = SelectField('Type de logement*', choices=[
        ('', 'Sélectionner...'),
        ('Résidentiel', 'Résidentiel'),
        ('Professionnel', 'Professionnel')
    ], validators=[DataRequired()])
    
    # Disponibilité réseaux
    fibre_dispo = BooleanField('Fibre disponible')
    cuivre_dispo = BooleanField('Cuivre disponible')
    gpon_olt = StringField('GPON/OLT*', validators=[DataRequired()])
    splitter = StringField('Splitter*', validators=[DataRequired()])
    distance_fibre = IntegerField('Distance fibre (m)*', validators=[DataRequired()])
    etat_fibre = SelectField('État de la fibre*', choices=[
        ('', 'Sélectionner...'),
        ('Bon', 'Bon'),
        ('Mauvais', 'Mauvais')
    ], validators=[DataRequired()])
    sr = StringField('SR*', validators=[DataRequired()])
    pc = StringField('PC*', validators=[DataRequired()])
    distance_cuivre = IntegerField('Distance cuivre (m)*', validators=[DataRequired()])
    etat_cuivre = SelectField('État du cuivre*', choices=[
        ('', 'Sélectionner...'),
        ('Bon', 'Bon'),
        ('Mauvais', 'Mauvais')
    ], validators=[DataRequired()])

    # Matériel requis
    modem = BooleanField('Modem')
    ont = BooleanField('ONT')
    nb_prises = IntegerField('Nombre de prises*', validators=[DataRequired()])
    quantite_cable = IntegerField('Quantité de câble (m)*', validators=[DataRequired()])
    
    # Observations
    observation_tech = TextAreaField('Observations techniques*', validators=[DataRequired()])
    observation_client = TextAreaField('Observations client*', validators=[DataRequired()])
    conclusion = SelectField('Conclusion*', choices=[
        ('', 'Sélectionner...'),
        ('Réalisable', 'Réalisable'),
        ('Non réalisable', 'Non réalisable'),
        ('En attente', 'En attente')
    ], validators=[DataRequired()])
    
    # Images
    photo_batiment = FileField('Photo du bâtiment*', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images uniquement!')
    ])
    photo_environ = FileField('Photo de l\'environnement*', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images uniquement!')
    ])
    technicien_structure = StringField('Technicien structure*', validators=[DataRequired()])
    backoffice_structure = StringField('Backoffice structure*', validators=[DataRequired()])
    offre = StringField('Offre*', validators=[DataRequired()])
    debit = StringField('Débit*', validators=[DataRequired()])
    type_mi = BooleanField('MI')
    type_na = BooleanField('NA')
    type_transfer = BooleanField('Transfer')
    type_autre = BooleanField('Autre')

    # Données réseaux
    nro = StringField('NRO', validators=[DataRequired()])
    type_reseau = StringField('Type réseau', validators=[DataRequired()])
    plaque = StringField('Plaque', validators=[DataRequired()])
    bpi = StringField('BPI', validators=[DataRequired()])
    pbo = StringField('PBO', validators=[DataRequired()])
    coupleur = StringField('Coupleur', validators=[DataRequired()])
    fibre = StringField('Fibre', validators=[DataRequired()])
    nb_clients = IntegerField('Nombre clients', validators=[DataRequired()])
    valeur_pbo_dbm = StringField('Valeur PBO (dBm)', validators=[DataRequired()])
    bpi_b1 = StringField('BPI B1', validators=[DataRequired()])
    pbo_b1 = StringField('PBO B1', validators=[DataRequired()])
    coupleur_b1 = StringField('Coupleur B1', validators=[DataRequired()])
    nb_clients_b1 = IntegerField('Nombre clients B1', validators=[DataRequired()])
    valeur_pbo_dbm_b1 = StringField('Valeur PBO B1 (dBm)', validators=[DataRequired()])

    # Données client
    description_logement_avec_bpi = TextAreaField('Description logement avec BPI', validators=[DataRequired()])
    description_logement_sans_bpi = TextAreaField('Description logement sans BPI', validators=[DataRequired()])
    emplacement_pto = StringField('Emplacement PTO', validators=[DataRequired()])
    passage_cable = TextAreaField('Passage câble', validators=[DataRequired()])
    longueur_tirage_pbo_bti = StringField('Longueur tirage PBO-BTI', validators=[DataRequired()])
    longueur_tirage_bti_pto = StringField('Longueur tirage BTI-PTO', validators=[DataRequired()])
    materiel_existant_decodeur_carte = BooleanField('Décodeur/Carte')
    materiel_existant_wifi_extender = BooleanField('WiFi Extender')
    materiel_existant_fax = BooleanField('Fax')
    materiel_existant_videosurveillance = BooleanField('Vidéosurveillance')
    qualite_ligne_adsl_defaut_couverture = BooleanField('Défaut couverture')
    qualite_ligne_adsl_lenteurs = BooleanField('Lenteurs')
    qualite_ligne_adsl_deconnexions = BooleanField('Déconnexions')
    qualite_ligne_adsl_ras = BooleanField('RAS')

    # Pièces et mesures
    niveau_wifi_salon = StringField('Niveau WiFi salon', validators=[DataRequired()])
    niveau_wifi_chambre1 = StringField('Niveau WiFi chambre 1', validators=[DataRequired()])
    niveau_wifi_bureau1 = StringField('Niveau WiFi bureau 1', validators=[DataRequired()])
    niveau_wifi_autres_pieces = StringField('Niveau WiFi autres pièces', validators=[DataRequired()])
    choix_bf_hall = BooleanField('BF Hall')
    choix_bf_chambre2 = BooleanField('BF Chambre 2')
    choix_bf_bureau2 = BooleanField('BF Bureau 2')
    choix_bf_mesure_dbm = StringField('BF Mesure dBm', validators=[DataRequired()])
    cuisine_chambre3 = BooleanField('Cuisine/Chambre 3')
    cuisine_bureau3 = BooleanField('Cuisine/Bureau 3')
    cuisine_mesure_dbm = StringField('Cuisine Mesure dBm', validators=[DataRequired()])

    # Accessoires recommandés
    repeteur_wifi_oui = BooleanField('Répéteur WiFi - Oui')
    repeteur_wifi_non = BooleanField('Répéteur WiFi - Non')
    repeteur_wifi_quantite = IntegerField('Quantité répéteur', validators=[DataRequired()])
    repeteur_wifi_emplacement = StringField('Emplacement répéteur', validators=[DataRequired()])
    cpl_oui = BooleanField('CPL - Oui')
    cpl_non = BooleanField('CPL - Non')
    cpl_quantite = IntegerField('Quantité CPL', validators=[DataRequired()])
    cpl_emplacement = StringField('Emplacement CPL', validators=[DataRequired()])
    cable_local_type = StringField('Type câble local', validators=[DataRequired()])
    cable_local_longueur = StringField('Longueur câble', validators=[DataRequired()])
    cable_local_connecteurs = StringField('Connecteurs', validators=[DataRequired()])
    goulottes_oui = BooleanField('Goulottes - Oui')
    goulottes_non = BooleanField('Goulottes - Non')
    goulottes_quantite = IntegerField('Quantité goulottes', validators=[DataRequired()])
    goulottes_nombre_x2m = IntegerField('Nombre x 2m', validators=[DataRequired()])

    # Survey OK/NOK et motifs
    survey_ok = BooleanField('Survey OK')
    survey_nok = BooleanField('Survey NOK')
    motif = SelectField(
        'Motif*',
        choices=[
            ('CONTRAINTE RACCORDEMENT SONATEL-GC', 'CONTRAINTE RACCORDEMENT SONATEL-GC'),
            ('CONTRAINTE RACCORDEMENT CLIENT-GC', 'CONTRAINTE RACCORDEMENT CLIENT-GC'),
            ('CONTRAINTE RACCORDEMENT SONATEL-EL', 'CONTRAINTE RACCORDEMENT SONATEL-EL'),
            ('CONTRAINTE RACCORDEMENT SONATEL-PCH', 'CONTRAINTE RACCORDEMENT SONATEL-PCH'),
            ('CONTRAINTE RACCORDEMENT SONATEL-PP', 'CONTRAINTE RACCORDEMENT SONATEL-PP'),
            ('SURVEY OK-INSTALLATION REALISABLE', 'SURVEY OK-INSTALLATION REALISABLE'),
            ('PROBLEME TECHNIQUE SONATEL-ABS-CI', 'PROBLEME TECHNIQUE SONATEL-ABS-CI'),
            ('PROBLEME TECHNIQUE SONATEL-ABS-VS', 'PROBLEME TECHNIQUE SONATEL-ABS-VS'),
            ('PROBLEME TECHNIQUE SONATEL-ABS-JA', 'PROBLEME TECHNIQUE SONATEL-ABS-JA')
        ],
        validators=[DataRequired()]
    )
    commentaires = TextAreaField('Commentaires', validators=[DataRequired()])

    # Signatures et satisfaction client
    signature_equipe = HiddenField('Signature équipe')
    signature_client = HiddenField('Signature client')
    client_tres_satisfait = BooleanField('Très satisfait')
    client_satisfait = BooleanField('Satisfait')
    client_pas_satisfait = BooleanField('Pas satisfait')




class InterventionForm(FlaskForm):
    # Champs techniques
    numero = StringField('N°', validators=[Optional(), Length(max=50)])
    constitutions = StringField('CONSTITUTIONS', validators=[Optional(), Length(max=100)])
    valeur_pB0 = StringField('VALEUR AU PB0-dBm', validators=[Optional(), Length(max=50)])
    nature_signalisation = StringField('Nature signalisation', validators=[Optional(), Length(max=100)])
    diagnostic_technicien = TextAreaField('Diagnostic technicien', validators=[Optional()])
    cause_derangement = TextAreaField('Cause dérangement', validators=[Optional()])
    action_releve = TextAreaField('Action de relève', validators=[Optional()])
    gps_lat = StringField('Latitude GPS*', validators=[DataRequired()])
    gps_long = StringField('Longitude GPS*', validators=[DataRequired()])
    # Matériel
    materiel_livre = SelectField(
        'MATÉRIELS LIVRÉS',
        choices=[
            ('', 'Sélectionner un matériel'),
            ('Type ONT', 'Type ONT'),
            ('Décodeur', 'Décodeur'),
            ('Disque dur', 'Disque dur'),
            ('Téléphone', 'Téléphone'),
            ('Répétiteur Wifi', 'Répétiteur Wifi'),
            ('CPL', 'CPL'),
            ('Carte VIACCESS', 'Carte VIACCESS')
        ],
        validators=[Optional()]
    )
    materiel_recup = StringField('MATÉRIELS RECUPÉRÉS', validators=[Optional(), Length(max=100)])
    numero_serie_livre = StringField('N° SÉRIE LIVRÉ', validators=[Optional(), Length(max=100)])
    numero_serie_recup = StringField('N° SÉRIE RÉCUPÉRÉ', validators=[Optional(), Length(max=100)])
    
    # Tests services
    appel_sortant = BooleanField('Appel sortant')
    envoi_numero = StringField('Envoi numéro', validators=[Optional(), Length(max=20)])
    appel_entrant = BooleanField('Appel entrant')
    affichage_numero = StringField('Affichage numéro', validators=[Optional(), Length(max=20)])
    tvo_mono_ok = BooleanField('TVO mono OK')
    
    # Installation
    
    pieces = SelectField('Pièces',
                         choices=[
        ('', 'Sélectionner'),
        ('Bureau Wifi < -70dBm', 'Bureau Wifi < -70dBm'),
        ('Choix Bf: 20/40 MHz', 'Choix Bf: 20/40 MHz')
    ],
      validators=[Optional()]
    )
    communes = StringField('Communes', validators=[Optional(), Length(max=100)])
    chambres = IntegerField('Chambres', validators=[Optional()])
    bureau = IntegerField('Bureau', validators=[Optional()])
    wifi_extender = BooleanField('Autres pièces')
    mesure_dbm = StringField(
        'Mesure en dBm',
        validators=[
            Optional(),
            Length(max=10),
            Regexp(r'^-?\d+$', message="Doit être une valeur numérique (ex: -70)")
        ]
    )
    # Tests débits
    debit_cable_montant = StringField('Débit câble montant', validators=[Optional(), Length(max=50)])
    debit_mbs_descendant = StringField('Débit Mbs descendant', validators=[Optional(), Length(max=50)])
    debit_mbs_ping = StringField('Débit Mbs ping', validators=[Optional(), Length(max=50)])
    debit_ms = StringField('Débit ms', validators=[Optional(), Length(max=50)])
    
    # Satisfaction
    satisfaction = SelectField('Satisfaction client', choices=[
        ('', 'Non renseigné'),
        ('1', 'Satisfait'),
        ('2', 'Peu satisfait'),
        ('3', 'Très satisfait'),
        ('0', 'Pas satisfait')
    ], validators=[Optional()])
    
    # Signatures
    signature_equipe = HiddenField('Signature équipe')
    signature_client = HiddenField('Signature client')

    # Photos
    photos = FileField('Photos', validators=[DataRequired()])
    # Champs pour la section ACCESSOIRES
    jarretiere = StringField('Jarretière', validators=[Optional(), Length(max=50)])
    nombre_type_bpe = StringField('Nombre et type BPE', validators=[Optional(), Length(max=50)])
    coupleur_c1 = StringField('Coupleur C1', validators=[Optional(), Length(max=50)])
    coupleur_c2 = StringField('Coupleur C2', validators=[Optional(), Length(max=50)])
    arobase = StringField('Arobase', validators=[Optional(), Length(max=50)])
    malico = StringField('Malico', validators=[Optional(), Length(max=50)])
    type_cable = StringField('Type de cable', validators=[Optional(), Length(max=50)])
    lc_metre = StringField('LC en mètre', validators=[Optional(), Length(max=50)])
    bti_metre = StringField('BTI en mètre', validators=[Optional(), Length(max=50)])
    pto_one = StringField('PTO ONE', validators=[Optional(), Length(max=50)])
    kitpto_metre = StringField('KITPTO en mètre', validators=[Optional(), Length(max=50)])
    piton = StringField('Piton', validators=[Optional(), Length(max=50)])
    ds6 = StringField('DS6', validators=[Optional(), Length(max=50)])
    autres_accessoires = StringField('Autres', validators=[Optional(), Length(max=100)])
    
    # Type Installation
    type_mi = BooleanField('Type MI (Mise en place)')
    type_na = BooleanField('Type NA (Nouveau client)')
    type_ma = BooleanField('Type MA (Modification)')
    
    # Confirmation
    confirm_data = BooleanField('Confirmation données*', validators=[DataRequired()])
    confirm_signature = BooleanField('Confirmation signature*', validators=[DataRequired()])
    
    # Template-specific fields (for validation compatibility)
    adresse_demande = StringField('Adresse*', validators=[Optional()])
    etage = StringField('Étage*', validators=[Optional()])
    h_debut = StringField('Heure début*', validators=[Optional()])
    h_fin = StringField('Heure fin*', validators=[Optional()])
    date_intervention = StringField('Date*', validators=[Optional()])
    nom_raison_sociale = StringField('Nom*', validators=[Optional()])
    contact = StringField('Contact*', validators=[Optional()])
    tel1 = StringField('Port1*', validators=[Optional()])
    tel2 = StringField('Port2*', validators=[Optional()])
    n_ligne = StringField('N Ligne*', validators=[Optional()])
    n_demande = StringField('N Demande*', validators=[Optional()])
    service_demande = StringField('Service*', validators=[Optional()])
    technicien_structure = StringField('Tech Structure*', validators=[Optional()])
    backoffice_structure = StringField('BO Structure*', validators=[Optional()])
    offre = StringField('Offre*', validators=[Optional()])
    debit = StringField('Débit*', validators=[Optional()])
    technicien_responsable = StringField('Tech Responsable*', validators=[Optional()])
    statut = StringField('Statut*', validators=[Optional()])
    observations = TextAreaField('Observations*', validators=[Optional()])

    def validate_confirm_password(self, field):
        if field.data != self.password.data:
            raise ValidationError('Les mots de passe ne correspondent pas.')

class CreateUserForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired()])
    role = SelectField('Rôle', choices=[
        ('chef_pur', 'Chef PUR'),
        ('chef_pilote', 'Chef Pilote'),
        ('chef_zone', 'Chef Zone'),
        ('technicien', 'Technicien'),
        ('magasinier', 'Magasinier'),
        ('gestionnaire_stock', 'Gestionnaire de Stock'),
        ('controle_operations_terrains', 'Contrôle des opérations terrains'),
        ('comptabilite_finance', 'Comptabilité et services financiers'),
        ('rh', 'Gestionnaire RH')
    ], validators=[DataRequired()])
    nom = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    prenom = StringField('Prénom', validators=[DataRequired(), Length(max=100)])
    telephone = StringField('Téléphone', validators=[
        DataRequired(),
        Length(max=20),
        Regexp(r'^(\+221)?7[0-9]{8}$', message="Format: 77xxxxxxx ou +22177xxxxxxx")
    ])
    
    # Champs spécifiques selon le rôle
    # NOTE: Zone validation is done in validate_zone() method below
    zone = SelectField('Zone', coerce=int, validators=[Optional()])
    commune = StringField('Commune', validators=[Optional(), Length(max=100)])
    quartier = StringField('Quartier', validators=[Optional(), Length(max=100)])
    service = SelectField('Service', choices=[
        ('', 'Sélectionner un service'),
        ('SAV', 'SAV'),
        ('Production', 'Production'),
        ('SAV,Production', 'SAV + Production')
    ], validators=[Optional()])
    technologies = SelectField('Technologies', choices=[
        ('', 'Sélectionner les technologies'),
        ('Fibre', 'Fibre'),
        ('Cuivre', 'Cuivre'),
        ('5G', '5G'),
        ('Fibre,Cuivre', 'Fibre + Cuivre'),
        ('Fibre,5G', 'Fibre + 5G'),
        ('Cuivre,5G', 'Cuivre + 5G'),
        ('Fibre,Cuivre,5G', 'Toutes technologies')
    ], validators=[Optional()])
    actif = BooleanField('Utilisateur actif', default=True)

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        # Charger les zones depuis la BD dynamiquement
        from models import Zone
        toutes_zones = Zone.query.order_by(Zone.nom).all()
        zones = [z for z in toutes_zones if getattr(z, 'actif', True)]
        print(f"DEBUG: Zones trouvées: {len(zones)}")  # Debug
        for zone in zones:
            print(f"DEBUG: Zone - ID: {zone.id}, Nom: {zone.nom}, Code: {zone.code}")  # Debug
        
        self.zone.choices = [(0, 'Sélectionner une zone')] + [
            (zone.id, f"{zone.nom} ({zone.code})") 
            for zone in zones
        ]
        print(f"DEBUG: Choices zone: {len(self.zone.choices)}")  # Debug

    def validate_zone(self, field):
        """Validation du champ zone selon le rôle"""
        if self.role.data in ['chef_zone', 'magasinier', 'technicien']:
            # Pour chef_zone, magasinier et technicien, la zone est obligatoire
            if not field.data or field.data == 0 or str(field.data) == '0' or field.data is None:
                role_display = {'chef_zone': 'Chef de zone', 'magasinier': 'Magasinier', 'technicien': 'Technicien'}.get(self.role.data, self.role.data)
                raise ValidationError(f'La zone est obligatoire pour un {role_display}.')

    def validate_confirm_password(self, field):
        if field.data != self.password.data:
            raise ValidationError('Les mots de passe ne correspondent pas.')

class EditUserForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    role = SelectField('Rôle', choices=[
        ('chef_pur', 'Chef PUR'),
        ('chef_pilote', 'Chef Pilote'),
        ('chef_zone', 'Chef Zone'),
        ('technicien', 'Technicien'),
        ('magasinier', 'Magasinier'),
        ('gestionnaire_stock', 'Gestionnaire de Stock'),
        ('controle_operations_terrains', 'Contrôle des opérations terrains'),
        ('comptabilite_finance', 'Comptabilité et services financiers'),
        ('rh', 'Gestionnaire RH')
    ], validators=[DataRequired()])
    nom = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    prenom = StringField('Prénom', validators=[DataRequired(), Length(max=100)])
    telephone = StringField('Téléphone', validators=[DataRequired(), Length(max=20)])
    
    # Champs spécifiques selon le rôle
    zone = SelectField('Zone', coerce=int, validators=[Optional()])
    commune = StringField('Commune', validators=[Optional(), Length(max=100)])
    quartier = StringField('Quartier', validators=[Optional(), Length(max=100)])
    service = SelectField('Service', choices=[
        ('', 'Sélectionner un service'),
        ('SAV', 'SAV'),
        ('Production', 'Production'),
        ('SAV,Production', 'SAV + Production')
    ], validators=[Optional()])
    technologies = SelectField('Technologies', choices=[
        ('', 'Sélectionner les technologies'),
        ('Fibre', 'Fibre'),
        ('Cuivre', 'Cuivre'),
        ('5G', '5G'),
        ('Fibre,Cuivre', 'Fibre + Cuivre'),
        ('Fibre,5G', 'Fibre + 5G'),
        ('Cuivre,5G', 'Cuivre + 5G'),
        ('Fibre,Cuivre,5G', 'Toutes technologies')
    ], validators=[Optional()])
    actif = BooleanField('Utilisateur actif')
    
    # Champ optionnel pour changer le mot de passe
    new_password = PasswordField('Nouveau mot de passe (optionnel)', validators=[Optional(), Length(min=6)])
    confirm_new_password = PasswordField('Confirmer le nouveau mot de passe', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        # Charger les zones depuis la BD dynamiquement
        from models import Zone
        toutes_zones = Zone.query.order_by(Zone.nom).all()
        self.zone.choices = [(0, 'Sélectionner une zone')] + [
            (zone.id, f"{zone.nom} ({zone.code})")
            for zone in toutes_zones if getattr(zone, 'actif', True)
        ]

    def validate_confirm_new_password(self, field):
        if self.new_password.data and field.data != self.new_password.data:
            raise ValidationError('Les mots de passe ne correspondent pas.')

    def validate_zone(self, field):
        """Validation du champ zone selon le rôle"""
        if self.role.data in ['chef_zone', 'magasinier', 'technicien']:
            # Pour chef_zone, magasinier et technicien, la zone est obligatoire
            if not field.data or field.data == 0 or str(field.data) == '0' or field.data is None:
                role_display = {'chef_zone': 'Chef de zone', 'magasinier': 'Magasinier', 'technicien': 'Technicien'}.get(self.role.data, self.role.data)
                raise ValidationError(f'La zone est obligatoire pour un {role_display}.')
        
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Envoyer le lien')      

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nouveau mot de passe', validators=[DataRequired()])
    submit = SubmitField('Réinitialiser')


# ============================================================================
# 🔴 PHASE 2 FIX: Formulaires spécialisés pour le rôle Magasinier
# ============================================================================

class CreateUserMagasinierForm(FlaskForm):
    """Form spécialisée pour créer un utilisateur magasinier avec zone obligatoire"""
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired()])
    nom = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    prenom = StringField('Prénom', validators=[DataRequired(), Length(max=100)])
    telephone = StringField('Téléphone', validators=[
        DataRequired(),
        Length(max=20),
        Regexp(r'^(\+221)?7[0-9]{8}$', message="Format: 77xxxxxxx ou +22177xxxxxxx")
    ])
    
    # MAGASINIER: Zone est OBLIGATOIRE
    zone = SelectField('Zone (obligatoire)', coerce=int, validators=[DataRequired()])
    actif = BooleanField('Utilisateur actif', default=True)

    def __init__(self, *args, **kwargs):
        super(CreateUserMagasinierForm, self).__init__(*args, **kwargs)
        # Charger les zones depuis la BD dynamiquement (sans option vide pour magasinier)
        from models import Zone
        self.zone.choices = [
            (zone.id, f"{zone.nom} ({zone.code})") 
            for zone in Zone.query.filter_by(actif=True).order_by(Zone.nom).all()
        ]

    def validate_confirm_password(self, field):
        if field.data != self.password.data:
            raise ValidationError('Les mots de passe ne correspondent pas.')

    def validate_zone(self, field):
        """Valider que la zone est bien sélectionnée pour un magasinier"""
        if not field.data or field.data == 0:
            raise ValidationError('Vous devez sélectionner une zone pour ce magasinier.')


class EntreeStockFormMagasinier(FlaskForm):
    """Form spécialisée pour l'entrée de stock par un magasinier"""
    
    fournisseur = SelectField('Fournisseur', coerce=int, validators=[DataRequired()])
    emplacement = SelectField('Emplacement (zone du magasinier)', coerce=int, validators=[DataRequired()])
    produit = SelectField('Produit', coerce=int, validators=[DataRequired()])
    quantite = IntegerField('Quantité', validators=[DataRequired(), NumberRange(min=1)])
    prix_unitaire = DecimalField('Prix unitaire (CFA)', validators=[Optional()], places=2)
    numero_facture = StringField('Numéro de facture', validators=[Optional(), Length(max=100)])
    numero_bon_livraison = StringField('Numéro de bon de livraison', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Enregistrer l\'entrée')

    def __init__(self, magasinier_zone_id=None, *args, **kwargs):
        super(EntreeStockFormMagasinier, self).__init__(*args, **kwargs)
        self.magasinier_zone_id = magasinier_zone_id
        
        # Charger fournisseurs
        from models import Fournisseur
        self.fournisseur.choices = [(0, 'Sélectionner un fournisseur')] + [
            (fournisseur.id, fournisseur.nom_fournisseur)
            for fournisseur in Fournisseur.query.filter_by(actif=True).order_by(Fournisseur.nom_fournisseur).all()
        ]
        
        # Charger emplacements filtrés par zone du magasinier
        from models import EmplacementStock
        if magasinier_zone_id:
            self.emplacement.choices = [(0, 'Sélectionner un emplacement')] + [
                (emplacement.id, f"{emplacement.code} ({emplacement.etage})")
                for emplacement in EmplacementStock.query.filter_by(
                    zone_id=magasinier_zone_id, 
                    actif=True
                ).order_by(EmplacementStock.code).all()
            ]
        
        # Charger produits
        from models import Produit
        self.produit.choices = [(0, 'Sélectionner un produit')] + [
            (produit.id, f"{produit.designation}")
            for produit in Produit.query.filter_by(actif=True).order_by(Produit.designation).all()
        ]

    def validate_emplacement(self, field):
        """Valider que l'emplacement appartient à la zone du magasinier"""
        if self.magasinier_zone_id:
            from models import EmplacementStock
            emplacement = EmplacementStock.query.get(field.data)
            if not emplacement or emplacement.zone_id != self.magasinier_zone_id:
                raise ValidationError('L\'emplacement sélectionné n\'appartient pas à votre zone.')


class SortieStockFormMagasinier(FlaskForm):
    """Form spécialisée pour la sortie de stock par un magasinier"""
    
    emplacement = SelectField('Emplacement (zone du magasinier)', coerce=int, validators=[DataRequired()])
    produit = SelectField('Produit', coerce=int, validators=[DataRequired()])
    quantite = IntegerField('Quantité', validators=[DataRequired(), NumberRange(min=1)])
    motif = SelectField('Motif de sortie', choices=[
        ('', 'Sélectionner un motif'),
        ('vente', 'Vente'),
        ('test', 'Test'),
        ('rebut', 'Rebut'),
        ('transfert', 'Transfert inter-zone'),
        ('consommation', 'Consommation interne'),
        ('autre', 'Autre')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Enregistrer la sortie')

    def __init__(self, magasinier_zone_id=None, *args, **kwargs):
        super(SortieStockFormMagasinier, self).__init__(*args, **kwargs)
        self.magasinier_zone_id = magasinier_zone_id
        
        # Charger emplacements filtrés par zone du magasinier
        from models import EmplacementStock
        if magasinier_zone_id:
            self.emplacement.choices = [(0, 'Sélectionner un emplacement')] + [
                (emplacement.id, f"{emplacement.code} ({emplacement.etage})")
                for emplacement in EmplacementStock.query.filter_by(
                    zone_id=magasinier_zone_id, 
                    actif=True
                ).order_by(EmplacementStock.code).all()
            ]
        
        # Charger produits
        from models import Produit
        self.produit.choices = [(0, 'Sélectionner un produit')] + [
            (produit.id, f"{produit.designation}")
            for produit in Produit.query.filter_by(actif=True).order_by(Produit.designation).all()
        ]

    def validate_emplacement(self, field):
        """Valider que l'emplacement appartient à la zone du magasinier"""
        if self.magasinier_zone_id:
            from models import EmplacementStock
            emplacement = EmplacementStock.query.get(field.data)
            if not emplacement or emplacement.zone_id != self.magasinier_zone_id:
                raise ValidationError('L\'emplacement sélectionné n\'appartient pas à votre zone.')
