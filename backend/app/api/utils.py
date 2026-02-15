"""
API utility functions
"""

from typing import Dict, Any, Optional
import os
from datetime import datetime
import logging

from app.services.agent_service import get_agent_service
from app.services.processing_service import get_processing_service
from app.core.config import settings

logger = logging.getLogger(__name__)


async def process_invoice_background(job_id: str, invoice_path: str, po_path: Optional[str] = None):
    """Background task to process invoice"""
    agent_service = get_agent_service()
    processing_service = get_processing_service()
    
    try:
        # Update: processing started
        processing_service.update_job(
            job_id,
            status="processing",
            current_agent="document_intelligence",
            progress=10,
            message="Extracting invoice data..."
        )
        
        # Process through agent system
        logger.info(f"Job {job_id}: Starting agent processing")
        final_state = agent_service.process_invoice(invoice_path, po_path)
        
        # Update progress through agents
        processing_service.update_job(
            job_id,
            current_agent="matching",
            progress=50,
            message="Matching against purchase orders..."
        )
        
        processing_service.update_job(
            job_id,
            current_agent="discrepancy_detection",
            progress=70,
            message="Detecting discrepancies..."
        )
        
        processing_service.update_job(
            job_id,
            current_agent="resolution",
            progress=90,
            message="Generating recommendations..."
        )
        
        # Format result
        result = format_result_for_frontend(final_state)
        
        # Save result file
        import json
        result_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_result.json")
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        # Update: completed
        processing_service.update_job(
            job_id,
            status="completed",
            progress=100,
            message="Processing completed successfully",
            result=result,
            completed_at=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Job {job_id}: Completed successfully")
        
    except Exception as e:
        import traceback
        error_msg = f"Failed with error: {str(e)}"
        logger.error(f"Job {job_id}: {error_msg}")
        logger.error(traceback.format_exc())
        
        processing_service.update_job(
            job_id,
            status="failed",
            message="Processing failed",
            error=str(e)
        )


def format_result_for_frontend(state: Dict[str, Any]) -> Dict[str, Any]:
    """Format agent output for frontend"""
    extraction = state.get('extraction_result', {})
    match_result = state.get('match_result', {})
    discrepancies = state.get('discrepancies', [])
    recommendation = state.get('recommendation', {})
    agent_steps = state.get('agent_steps', [])
    
    # Format matched items
    matched_items = []
    for item in match_result.get('matched_items', []):
        matched_items.append({
            "invoice_item": item.get('invoice_item', {}),
            "po_item": item.get('po_item'),
            "match_score": item.get('match_score', 0),
            "match_type": item.get('match_type', 'unknown')
        })
    
    return {
        "extraction": {
            "invoice_number": extraction.get('invoice_number'),
            "supplier": extraction.get('supplier_name'),
            "po_reference": extraction.get('po_reference'),
            "invoice_date": extraction.get('invoice_date'),
            "total_amount": extraction.get('total', 0),
            "currency": extraction.get('currency', 'USD'),
            "line_items": [
                {
                    "item_number": item.get('item_number'),
                    "description": item.get('description'),
                    "quantity": item.get('quantity', 0),
                    "unit": item.get('unit'),
                    "unit_price": item.get('unit_price', 0),
                    "total_price": item.get('total_price', 0),
                    "confidence": item.get('confidence')
                }
                for item in extraction.get('line_items', [])
            ],
            "confidence": extraction.get('confidence_score', 0)
        },
        "matching": {
            "match_type": match_result.get('match_type', 'none'),
            "confidence_score": match_result.get('match_confidence', 0),
            "matched_po_id": match_result.get('po_number'),
            "matched_items": matched_items,
            "matched_items_count": len(match_result.get('matched_items', [])),
            "unmatched_items": match_result.get('unmatched_items', []),
            "unmatched_items_count": len(match_result.get('unmatched_items', []))
        },
        "discrepancies": [
            {
                "type": d.get('type'),
                "severity": d.get('severity'),
                "confidence": d.get('confidence', 0),
                "explanation": d.get('reasoning', ''),
                "details": d.get('details', ''),
                "expected_value": d.get('expected_value'),
                "actual_value": d.get('actual_value'),
                "difference": d.get('difference')
            }
            for d in discrepancies
        ],
        "resolution": {
            "action": recommendation.get('action', 'request_clarification'),
            "risk_level": recommendation.get('risk_assessment', 'medium'),
            "financial_impact": recommendation.get('estimated_financial_impact', 0),
            "ai_reasoning": recommendation.get('reasoning', ''),
            "summary": recommendation.get('summary', ''),
            "suggested_steps": recommendation.get('suggested_next_steps', [])
        },
        "agent_timeline": [
            {
                "agent": step.get('agent_name'),
                "timestamp": step.get('timestamp'),
                "confidence": step.get('confidence', 0),
                "reasoning": step.get('reasoning', ''),
                "execution_time": step.get('execution_time', 0)
            }
            for step in agent_steps
        ]
    }