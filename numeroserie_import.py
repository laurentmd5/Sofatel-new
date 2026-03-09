"""
numeroserie_import.py - Import Massif Numéros de Série Sonatel

Gère l'import de fichiers Excel/CSV contenant listes de numéros de série Sonatel
avec validation, détection doublons, audit trail complet
"""

import csv
import re
from io import StringIO, BytesIO
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Optional
import openpyxl
from models import (
    NumeroSerie, NumeroSerieStatut, ImportHistoriqueNumeroSerie,
    Produit, User, EmplacementStock, db
)


def utcnow():
    """Return timezone-aware UTC datetime"""
    return datetime.now(timezone.utc)


class NumeroSerieImportValidator:
    """Validateur pour import numéros de série"""
    
    # Format strict: SN-YYYY-NNNNNNN
    REGEX_NUMERO = r'^SN-\d{4}-\d{7}$'
    
    def __init__(self):
        self.erreurs: List[Dict] = []
        self.avertissements: List[Dict] = []
        self.doublons_fichier: List[str] = []
        self.doublons_systeme: List[str] = []
    
    def valider_numero(self, numero: str, ligne: int) -> bool:
        """Valide format du numéro de série"""
        if not numero or not isinstance(numero, str):
            self.erreurs.append({
                'ligne': ligne,
                'numero': numero,
                'erreur': 'Numéro vide ou invalide'
            })
            return False
        
        numero = numero.strip()
        
        if not re.match(self.REGEX_NUMERO, numero):
            self.erreurs.append({
                'ligne': ligne,
                'numero': numero,
                'erreur': f'Format invalide. Attendu: SN-YYYY-NNNNNNN (ex: SN-2024-0001234)'
            })
            return False
        
        return True
    
    def valider_fichier(self, contenu: str, format_type: str = 'csv') -> Tuple[List[Dict], bool]:
        """
        Parse et valide fichier CSV/Excel
        
        Args:
            contenu: Contenu fichier
            format_type: 'csv' ou 'excel'
        
        Returns:
            (List[lignes validées], succès)
        """
        self.erreurs = []
        self.avertissements = []
        self.doublons_fichier = []
        self.doublons_systeme = []
        
        lignes = []
        
        try:
            if format_type == 'csv':
                lignes = self._parse_csv(contenu)
            elif format_type == 'excel':
                lignes = self._parse_excel(contenu)
            else:
                self.erreurs.append({
                    'ligne': 0,
                    'erreur': f'Format non supporté: {format_type}'
                })
                return [], False
            
            if not lignes:
                self.erreurs.append({
                    'ligne': 0,
                    'erreur': 'Fichier vide ou aucune donnée valide'
                })
                return [], False
            
            # Valider chaque ligne
            lignes_valides = []
            numeros_vus = set()
            
            for ligne_num, ligne in enumerate(lignes, start=2):  # Commencer à ligne 2 (après header)
                numero = ligne.get('numero', '').strip()
                
                if not numero:
                    continue
                
                # Valider format
                if not self.valider_numero(numero, ligne_num):
                    continue
                
                # Détecter doublon dans fichier
                if numero in numeros_vus:
                    self.doublons_fichier.append(numero)
                    self.erreurs.append({
                        'ligne': ligne_num,
                        'numero': numero,
                        'erreur': 'Doublon dans fichier (numéro apparaît plusieurs fois)'
                    })
                    continue
                
                # Détecter doublon en système
                if NumeroSerie.query.filter_by(numero=numero).first():
                    self.doublons_systeme.append(numero)
                    self.erreurs.append({
                        'ligne': ligne_num,
                        'numero': numero,
                        'erreur': 'Doublon en système (numéro déjà importé)'
                    })
                    continue
                
                numeros_vus.add(numero)
                lignes_valides.append({
                    'numero': numero,
                    'ligne': ligne_num,
                    'details': ligne  # Champs additionnels si présents
                })
            
            succes = len(self.erreurs) == 0
            return lignes_valides, succes
            
        except Exception as e:
            self.erreurs.append({
                'ligne': 0,
                'erreur': f'Erreur parsing fichier: {str(e)}'
            })
            return [], False
    
    def _parse_csv(self, contenu: str) -> List[Dict]:
        """Parse fichier CSV"""
        lignes = []
        try:
            lecteur = csv.DictReader(StringIO(contenu))
            
            # Valider en-têtes obligatoires
            if not lecteur.fieldnames or 'numero' not in lecteur.fieldnames:
                raise ValueError('En-tête CSV doit contenir colonne "numero"')
            
            for ligne in lecteur:
                lignes.append(ligne)
            
            return lignes
        except Exception as e:
            raise ValueError(f'Erreur parsing CSV: {str(e)}')
    
    def _parse_excel(self, contenu: bytes) -> List[Dict]:
        """Parse fichier Excel"""
        lignes = []
        try:
            workbook = openpyxl.load_workbook(BytesIO(contenu))
            worksheet = workbook.active
            
            # Lire header
            header = []
            for cell in worksheet[1]:
                header.append(cell.value)
            
            if 'numero' not in header:
                raise ValueError('En-tête Excel doit contenir colonne "numero"')
            
            numero_index = header.index('numero')
            
            # Lire données
            for row_num, row in enumerate(worksheet.iter_rows(min_row=2, values_only=False), start=2):
                numero_cell = row[numero_index]
                numero = numero_cell.value if numero_cell else None
                
                ligne = {}
                for col_index, cell in enumerate(row):
                    col_name = header[col_index] if col_index < len(header) else f'col_{col_index}'
                    ligne[col_name] = cell.value
                
                lignes.append(ligne)
            
            return lignes
        except Exception as e:
            raise ValueError(f'Erreur parsing Excel: {str(e)}')


class NumeroSerieImporter:
    """Importe numéros de série validés en base de données"""
    
    def __init__(self, utilisateur_id: int, produit_id: int, bon_livraison_ref: str):
        self.utilisateur_id = utilisateur_id
        self.produit_id = produit_id
        self.bon_livraison_ref = bon_livraison_ref
        self.emplacement_magasin = None
    
    def get_emplacement_magasin(self) -> Optional[EmplacementStock]:
        """Récupère emplacement magasin central"""
        if self.emplacement_magasin:
            return self.emplacement_magasin
        
        emplacement = EmplacementStock.query.filter_by(
            type_emplacement='magasin_central'
        ).first()
        
        if not emplacement:
            raise ValueError('Emplacement magasin central non trouvé')
        
        self.emplacement_magasin = emplacement
        return emplacement
    
    def importer(self, lignes_valides: List[Dict]) -> Tuple[int, int, List[Dict]]:
        """
        Importe lignes valides en base de données
        
        Returns:
            (nb_importe, nb_erreurs, rapport_erreurs)
        """
        nb_importe = 0
        nb_erreurs = 0
        erreurs = []
        
        try:
            produit = Produit.query.get(self.produit_id)
            if not produit:
                raise ValueError(f'Produit {self.produit_id} introuvable')
            
            utilisateur = db.session.query(User).get(self.utilisateur_id)
            if not utilisateur:
                raise ValueError(f'Utilisateur {self.utilisateur_id} introuvable')
            
            emplacement = self.get_emplacement_magasin()
            
            for ligne in lignes_valides:
                try:
                    numero = NumeroSerie(
                        numero=ligne['numero'],
                        produit_id=self.produit_id,
                        statut=NumeroSerieStatut.EN_MAGASIN,
                        emplacement_id=emplacement.id,
                        cree_par_id=self.utilisateur_id,
                        date_entree=utcnow()
                    )
                    
                    db.session.add(numero)
                    nb_importe += 1
                    
                except Exception as e:
                    nb_erreurs += 1
                    erreurs.append({
                        'numero': ligne['numero'],
                        'ligne': ligne.get('ligne', '?'),
                        'erreur': str(e)
                    })
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            nb_erreurs += 1
            erreurs.append({
                'numero': 'GLOBAL',
                'erreur': str(e)
            })
        
        return nb_importe, nb_erreurs, erreurs
    
    def enregistrer_historique(self, nom_fichier: str, nb_lignes: int, nb_importe: int,
                               nb_erreurs: int, nb_doublons: int, rapport: Dict,
                               contenu_fichier: Optional[bytes] = None) -> ImportHistoriqueNumeroSerie:
        """Enregistre historique import"""
        
        historique = ImportHistoriqueNumeroSerie(
            nom_fichier=nom_fichier,
            bon_livraison_ref=self.bon_livraison_ref,
            produit_id=self.produit_id,
            nb_lignes_fichier=nb_lignes,
            nb_importe=nb_importe,
            nb_erreurs=nb_erreurs,
            nb_doublons=nb_doublons,
            rapport=rapport,
            date_import=utcnow(),
            utilisateur_id=self.utilisateur_id,
            contenu_fichier=contenu_fichier,
            statut='termine' if nb_erreurs == 0 else 'partiel'
        )
        
        db.session.add(historique)
        db.session.commit()
        
        return historique


def importer_numeros_sonatel(
    contenu: bytes,
    nom_fichier: str,
    format_type: str,
    produit_id: int,
    bon_livraison_ref: str,
    utilisateur_id: int,
    dry_run: bool = True
) -> Dict:
    """
    Importe numéros de série Sonatel complet
    
    Args:
        contenu: Contenu fichier (bytes)
        nom_fichier: Nom du fichier
        format_type: 'csv' ou 'excel'
        produit_id: ID produit
        bon_livraison_ref: Référence bon livraison Sonatel
        utilisateur_id: ID utilisateur effectuant import
        dry_run: Si True, valide sans commit (prévérification)
    
    Returns:
        {
            'succes': bool,
            'nb_lignes': int,
            'nb_importe': int,
            'nb_erreurs': int,
            'nb_doublons': int,
            'erreurs': List[Dict],
            'avertissements': List[Dict],
            'rapport': Dict
        }
    """
    
    try:
        # Décoder contenu
        if isinstance(contenu, bytes):
            if format_type == 'csv':
                contenu_str = contenu.decode('utf-8')
            else:
                contenu_str = contenu  # Garder bytes pour Excel
        else:
            contenu_str = contenu
        
        # Valider
        validateur = NumeroSerieImportValidator()
        
        if format_type == 'csv':
            lignes_valides, succes_validation = validateur.valider_fichier(
                contenu_str, 'csv'
            )
        else:
            lignes_valides, succes_validation = validateur.valider_fichier(
                contenu_str, 'excel'
            )
        
        # Si dry_run, retourner résultats validation uniquement
        if dry_run or not succes_validation:
            return {
                'succes': succes_validation,
                'mode': 'dry_run',
                'nb_lignes': len(lignes_valides),
                'nb_valides': len(lignes_valides),
                'nb_erreurs': len(validateur.erreurs),
                'nb_doublons_fichier': len(validateur.doublons_fichier),
                'nb_doublons_systeme': len(validateur.doublons_systeme),
                'erreurs': validateur.erreurs,
                'avertissements': validateur.avertissements,
                'message': f'Mode dry-run: {len(lignes_valides)} numéros valides, {len(validateur.erreurs)} erreurs'
            }
        
        # Importer (commit réel)
        importer = NumeroSerieImporter(utilisateur_id, produit_id, bon_livraison_ref)
        nb_importe, nb_erreurs_import, erreurs_import = importer.importer(lignes_valides)
        
        # Enregistrer historique
        rapport = {
            'validateur_erreurs': validateur.erreurs,
            'importer_erreurs': erreurs_import,
            'doublons_fichier': validateur.doublons_fichier,
            'doublons_systeme': validateur.doublons_systeme
        }
        
        historique = importer.enregistrer_historique(
            nom_fichier=nom_fichier,
            nb_lignes=len(lignes_valides),
            nb_importe=nb_importe,
            nb_erreurs=nb_erreurs_import,
            nb_doublons=len(validateur.doublons_systeme),
            rapport=rapport,
            contenu_fichier=contenu if isinstance(contenu, bytes) else contenu.encode('utf-8')
        )
        
        return {
            'succes': True,
            'mode': 'commit',
            'import_id': historique.id,
            'nb_lignes': len(lignes_valides),
            'nb_importe': nb_importe,
            'nb_erreurs': nb_erreurs_import,
            'nb_doublons': len(validateur.doublons_systeme),
            'erreurs': validateur.erreurs + erreurs_import,
            'avertissements': validateur.avertissements,
            'message': f'Import complété: {nb_importe} numéros importés, {nb_erreurs_import} erreurs'
        }
    
    except Exception as e:
        return {
            'succes': False,
            'erreur': str(e),
            'erreurs': [{'erreur': str(e)}]
        }
