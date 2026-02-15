"""
PO Database Service
Manages purchase order database operations
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class POService:
    
    def __init__(self, po_database_path: str):
        self.po_database_path = Path(po_database_path)
        self.po_database_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if it doesn't exist
        if not self.po_database_path.exists():
            self._save_database([])
    
    def load_database(self) -> List[Dict]:
        """Load PO database from JSON file"""
        try:
            with open(self.po_database_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} POs from database")
            return data
        except Exception as e:
            logger.error(f"Failed to load PO database: {e}")
            return []
    
    def _save_database(self, pos: List[Dict]):
        """Save PO database to JSON file"""
        try:
            with open(self.po_database_path, 'w') as f:
                json.dump(pos, f, indent=2)
            logger.info(f"Saved {len(pos)} POs to database")
        except Exception as e:
            logger.error(f"Failed to save PO database: {e}")
            raise
    
    def add_po(self, po_data: Dict) -> bool:
        """Add new PO to database"""
        try:
            # Load current database
            pos = self.load_database()
            
            # Check if PO already exists
            po_number = po_data.get('po_number')
            if po_number:
                existing = [p for p in pos if p.get('po_number') == po_number]
                if existing:
                    logger.warning(f"PO {po_number} already exists, updating...")
                    # Remove old version
                    pos = [p for p in pos if p.get('po_number') != po_number]
            
            # Add new PO
            pos.append(po_data)
            
            # Save database
            self._save_database(pos)
            
            logger.info(f"Added PO {po_number} to database")
            return True
        
        except Exception as e:
            logger.error(f"Failed to add PO: {e}")
            return False
    
    def get_po(self, po_number: str) -> Optional[Dict]:
        """Get specific PO by number"""
        pos = self.load_database()
        for po in pos:
            if po.get('po_number') == po_number:
                return po
        return None
    
    def get_all_pos(self) -> List[Dict]:
        """Get all POs"""
        return self.load_database()
    
    def get_po_summary_list(self) -> List[Dict]:
        """Get list of PO summaries (for frontend display)"""
        pos = self.load_database()
        
        # Get 5 most recent scans (assuming newer are at the end)
        recent_pos = list(reversed(pos))[:5]
        
        summaries = []
        for po in recent_pos:
            summaries.append({
                "po_number": po.get('po_number'),
                "vendor": po.get('vendor'),
                "order_date": po.get('order_date'),
                "status": po.get('status', 'approved'),
                "item_count": len(po.get('line_items', []))
            })
        return summaries


# Singleton instance
_po_service_instance = None

def get_po_service() -> POService:
    """Get or create PO service singleton"""
    global _po_service_instance
    if _po_service_instance is None:
        from app.core.config import settings
        _po_service_instance = POService(settings.PO_DATABASE_PATH)
    return _po_service_instance
