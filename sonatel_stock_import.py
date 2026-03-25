import pandas as pd
import logging
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional, Any
from flask import current_app
from extensions import db
from models import Produit, MouvementStock, EmplacementStock, User, Categorie, Zone
from utils_audit import log_stock_entry

logger = logging.getLogger(__name__)

class SonatelImportProcessor:
    """
    Processor for Sonatel Stock Excel files.
    Columns: Articles, DAKAR, MBOUR, KAOLACK, Total stock, Commentaires
    """
    
    REQUIRED_COLUMNS = ['Articles', 'Total stock']
    def __init__(self, user: User):
        self.user = user
        self.summary = {
            'total_rows': 0,
            'inserted_rows': 0,
            'error_rows': 0,
            'errors': []
        }
        # Dynamically load zones from DB
        try:
            db_zones = db.session.query(Zone).filter_by(actif=True).all()
            self.ZONE_COLUMNS = [z.nom.upper() for z in db_zones]
            logger.info(f"Dynamically loaded zones for import: {self.ZONE_COLUMNS}")
        except Exception as e:
            logger.error(f"Error loading zones for import: {e}")
            self.ZONE_COLUMNS = ['DAKAR', 'MBOUR', 'KAOLACK'] # Fallback

    def process_excel(self, file_content: bytes) -> Dict[str, Any]:
        """Parse Excel and import into Dakar warehouse"""
        try:
            df = pd.read_excel(file_content)
            
            # Filter out empty rows or rows without Articles
            df = df.dropna(subset=['Articles'])
            self.summary['total_rows'] = len(df)
            
            # Check required columns
            missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
            if missing:
                return {
                    'success': False,
                    'error': f"Colonnes manquantes : {', '.join(missing)}"
                }

            # Get Dakar Central Warehouse
            dakar_warehouse = db.session.query(EmplacementStock).filter(
                EmplacementStock.code == 'ENTREPOT'
            ).first()
            
            if not dakar_warehouse:
                # Fallback to creating it if missing (following init_emplacements pattern)
                dakar_warehouse = EmplacementStock(
                    code='ENTREPOT',
                    designation='Entrepôt central',
                    description='Stock principal de l\'entrepôt central',
                    actif=True
                )
                db.session.add(dakar_warehouse)
                db.session.flush()

            for index, row in df.iterrows():
                try:
                    self._process_row(row, dakar_warehouse)
                    self.summary['inserted_rows'] += 1
                except Exception as e:
                    self.summary['error_rows'] += 1
                    self.summary['errors'].append(f"Ligne {index + 2}: {str(e)}")
            
            db.session.commit()
            return {
                'success': True,
                'summary': self.summary
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f"Erreur lors du traitement du fichier : {str(e)}"
            }

    def _process_row(self, row: pd.Series, destination: EmplacementStock):
        """Process a single row from the Excel"""
        article_name = str(row['Articles']).strip()
        total_qty = row['Total stock']
        comment = str(row.get('Commentaires', '')) if pd.notna(row.get('Commentaires')) else ''
        
        if pd.isna(total_qty) or total_qty <= 0:
            return # Skip zero/empty stock
            
        # 1. Find or create Product
        product = db.session.query(Produit).filter(Produit.nom == article_name).first()
        if not product:
            # Create a basic product if not exists
            # We use the name as reference too if it looks unique enough, 
            # or generate a generic reference.
            ref = article_name.upper().replace(' ', '_')[:50]
            # Ensure reference uniqueness
            idx = 1
            original_ref = ref
            while db.session.query(Produit).filter(Produit.reference == ref).first():
                ref = f"{original_ref}_{idx}"
                idx += 1
                
            product = Produit(
                nom=article_name,
                reference=ref,
                actif=True,
                description=f"Importé via Sonatel - {datetime.now().strftime('%Y-%m-%d')}"
            )
            db.session.add(product)
            db.session.flush()

        # 2. Create Movement (Always to Dakar first)
        mouvement = MouvementStock(
            type_mouvement='entree',
            reference=f'SONATEL-{datetime.now(timezone.utc).strftime("%Y%m%d")}',
            date_reference=datetime.now(timezone.utc).date(),
            produit_id=product.id,
            quantite=float(total_qty),
            utilisateur_id=self.user.id,
            emplacement_id=destination.id,
            commentaire=f"Import Sonatel. {comment}".strip(),
            date_mouvement=datetime.now(timezone.utc),
            workflow_state='EN_ATTENTE',
            applique_au_stock=False
        )
        
        # Store planned distribution in comments for the GS to see
        dist_info = []
        for zone in self.ZONE_COLUMNS:
            val = row.get(zone, 0)
            if pd.notna(val) and val > 0:
                dist_info.append(f"{zone}: {val}")
        
        if dist_info:
            mouvement.commentaire += f" | Répartition prévue : {', '.join(dist_info)}"
            
        db.session.add(mouvement)
        
        # 3. Log Audit
        log_stock_entry(
            produit_id=product.id,
            quantity=float(total_qty),
            actor_id=self.user.id,
            supplier="Sonatel",
            invoice_num=mouvement.reference
        )

def process_sonatel_import(file_content: bytes, user: User) -> Dict[str, Any]:
    """Function wrapper for route consumption"""
    processor = SonatelImportProcessor(user)
    return processor.process_excel(file_content)
