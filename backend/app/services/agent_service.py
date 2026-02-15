"""
Service layer for agent integration
"""

import sys
import os
from typing import Dict, Any, Optional
import logging

# Add parent directory to path for imports
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.join(root_dir, 'invoice-reconciliation-system'))

from core.utils import load_config, load_purchase_orders
from core.state import create_initial_state
from core.graph import InvoiceReconciliationGraph
from agents.document_intelligence import DocumentIntelligenceAgent
from agents.matching_agent import MatchingAgent
from agents.discrepancy_detection import DiscrepancyDetectionAgent
from agents.resolution_agent import ResolutionRecommendationAgent

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing the multi-agent system"""
    
    def __init__(self, config_path: str = "config.yaml", po_path: str = "data/purchase_orders.json"):
        """Initialize the agent service"""
        self.config_path = config_path
        self.po_path = po_path
        self.config = load_config(config_path)
        self.po_database = load_purchase_orders(po_path)
        self.llm = self._initialize_llm()
        self.agents = self._initialize_agents()
        self.graph = InvoiceReconciliationGraph(self.agents, self.config)
        
        logger.info(f"AgentService initialized with {len(self.po_database)} purchase orders from {po_path}")
    
    def _initialize_llm(self):
        """ Initialize LLM based on configuration
        from app.core.config import settings
        
        try:
            if settings.LLM_PROVIDER == 'groq':
                from langchain_groq import ChatGroq
                
                if not settings.GROQ_API_KEY:
                    raise ValueError("GROQ_API_KEY not set in environment")
                
                return ChatGroq(
                    model=settings.LLM_MODEL,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    groq_api_key=settings.GROQ_API_KEY
                )
            elif settings.LLM_PROVIDER == 'openai':
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=settings.LLM_MODEL,
                    temperature=settings.LLM_TEMPERATURE
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise"""
        logger.warning("LLM disabled - running in fallback mode")
        return None
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agents"""
        return {
            'document_intelligence': DocumentIntelligenceAgent(self.config, self.llm),
            'matching': MatchingAgent(self.config, self.llm, po_db=self.po_database),
            'discrepancy_detection': DiscrepancyDetectionAgent(self.config, self.llm),
            'resolution': ResolutionRecommendationAgent(self.config, self.llm)
        }
    
    def process_invoice(self, invoice_path: str, po_path: Optional[str] = None) -> Dict[str, Any]:
        """Process an invoice through the agent system"""
        try:
            # Create initial state
            initial_state = create_initial_state(
                invoice_path=invoice_path,
                config=self.config,
                po_database=self.po_database,
                uploaded_po_path=po_path
            )
            
            # Process through graph
            final_state = self.graph.process_invoice(initial_state)
            
            return final_state
        except Exception as e:
            logger.error(f"Error processing invoice: {e}")
            raise
    
    def reload_po_database(self, po_path: Optional[str] = None):
        """Reload purchase order database and reinitialize matching agent"""
        target_path = po_path or self.po_path
        self.po_database = load_purchase_orders(target_path)
        
        # Reinitialize matching agent with new PO database
        self.agents['matching'] = MatchingAgent(self.config, self.llm, po_db=self.po_database)
        
        logger.info(f"Reloaded {len(self.po_database)} purchase orders from {target_path} and reinitialized matching agent")

    
    def get_po_by_number(self, po_number: str) -> Dict[str, Any]:
        """Get specific purchase order"""
        for po in self.po_database:
            if po.get('po_number') == po_number:
                return po
        return None


# Global service instance
_agent_service = None


def get_agent_service() -> AgentService:
    """Get or create agent service instance"""
    global _agent_service
    if _agent_service is None:
        from app.core.config import settings
        _agent_service = AgentService(
            config_path=settings.CONFIG_PATH,
            po_path=settings.PO_DATABASE_PATH
        )
    return _agent_service
