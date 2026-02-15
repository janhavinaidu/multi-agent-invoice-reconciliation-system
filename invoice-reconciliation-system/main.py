"""
Main entry point for the invoice reconciliation system.
"""

import os
import sys
import argparse
import logging
import time
import json
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.utils import load_config, load_purchase_orders, save_result, setup_logging
from core.state import create_initial_state
from core.graph import InvoiceReconciliationGraph
from agents.document_intelligence import DocumentIntelligenceAgent
from agents.matching_agent import MatchingAgent
from agents.discrepancy_detection import DiscrepancyDetectionAgent
from agents.resolution_agent import ResolutionRecommendationAgent

logger = logging.getLogger(__name__)


def initialize_llm(config: Dict[str, Any]):
    """Initialize the LLM based on configuration"""
    llm_config = config.get('llm', {})
    provider = llm_config.get('provider', 'groq')
    
    try:
        if provider == 'groq':
            from langchain_groq import ChatGroq
            
            # Check for API key
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                logger.error("GROQ_API_KEY not found in environment variables")
                logger.error("Get your FREE API key at: https://console.groq.com/keys")
                logger.error("Then set it: export GROQ_API_KEY='your-key-here'")
                sys.exit(1)
            
            logger.info(f"Using Groq (FREE) with model: {llm_config.get('model')}")
            return ChatGroq(
                model=llm_config.get('model', 'llama-3.3-70b-versatile'),
                temperature=llm_config.get('temperature', 0.1),
                max_tokens=llm_config.get('max_tokens', 4096),
                groq_api_key=groq_api_key
            )
        elif provider == 'openai':
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=llm_config.get('model', 'gpt-4o-mini'),
                temperature=llm_config.get('temperature', 0.1),
                max_tokens=llm_config.get('max_tokens', 4096)
            )
        elif provider == 'anthropic':
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=llm_config.get('model', 'claude-3-5-sonnet-20241022'),
                temperature=llm_config.get('temperature', 0.1),
                max_tokens=llm_config.get('max_tokens', 4096)
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    except ImportError as e:
        logger.error(f"Failed to import LLM library: {e}")
        logger.error("Install required package:")
        logger.error(f"  pip install langchain-{provider}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        if provider == 'groq':
            logger.error("\nTo get a FREE Groq API key:")
            logger.error("1. Visit https://console.groq.com/keys")
            logger.error("2. Sign up (free)")
            logger.error("3. Create an API key")
            logger.error("4. Set it: export GROQ_API_KEY='your-key-here'")
        sys.exit(1)


def initialize_agents(config: Dict[str, Any], llm) -> Dict[str, Any]:
    """Initialize all agents"""
    logger.info("Initializing agents...")
    
    agents = {
        'document_intelligence': DocumentIntelligenceAgent(config, llm),
        'matching': MatchingAgent(config, llm),
        'discrepancy_detection': DiscrepancyDetectionAgent(config, llm),
        'resolution': ResolutionRecommendationAgent(config, llm)
    }
    
    logger.info(f"Initialized {len(agents)} agents")
    return agents


def process_invoice(
    invoice_path: str,
    config: Dict[str, Any],
    po_database: List[Dict[str, Any]],
    graph: InvoiceReconciliationGraph
) -> Dict[str, Any]:
    """Process a single invoice"""
    logger.info(f"Processing invoice: {invoice_path}")
    
    # Create initial state
    initial_state = create_initial_state(invoice_path, config, po_database)
    
    # Process through graph
    start_time = time.time()
    final_state = graph.process_invoice(initial_state)
    processing_time = time.time() - start_time
    
    # Format output
    output = format_output(final_state, processing_time)
    
    return output


def format_output(state: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
    """Format the final output"""
    extraction = state.get('extraction_result', {})
    match_result = state.get('match_result', {})
    discrepancies = state.get('discrepancies', [])
    recommendation = state.get('recommendation', {})
    
    output = {
        'processing_metadata': {
            'processing_id': state.get('processing_id'),
            'invoice_filename': state.get('invoice_filename'),
            'processing_started': state.get('processing_started'),
            'processing_completed': state.get('processing_completed'),
            'processing_time_seconds': round(processing_time, 2),
            'status': state.get('status'),
            'overall_confidence': round(state.get('overall_confidence', 0), 4)
        },
        'extraction': {
            'invoice_number': extraction.get('invoice_number'),
            'supplier': {
                'name': extraction.get('supplier_name'),
                'address': extraction.get('supplier_address')
            },
            'dates': {
                'invoice_date': extraction.get('invoice_date'),
                'due_date': extraction.get('due_date')
            },
            'po_reference': extraction.get('po_reference'),
            'line_items': extraction.get('line_items', []),
            'financial': {
                'subtotal': extraction.get('subtotal'),
                'tax': extraction.get('tax'),
                'total': extraction.get('total'),
                'currency': extraction.get('currency', 'USD')
            },
            'extraction_quality': {
                'confidence_score': round(extraction.get('confidence_score', 0), 4),
                'ocr_quality': extraction.get('ocr_quality'),
                'warnings': extraction.get('warnings', [])
            }
        },
        'matching': {
            'po_number': match_result.get('po_number'),
            'match_type': match_result.get('match_type'),
            'match_confidence': round(match_result.get('match_confidence', 0), 4),
            'matched_items_count': len(match_result.get('matched_items', [])),
            'fuzzy_matches_count': len(match_result.get('fuzzy_matches', [])),
            'unmatched_items_count': len(match_result.get('unmatched_items', [])),
            'reasoning': match_result.get('reasoning')
        },
        'discrepancies': [
            {
                'id': d.get('discrepancy_id'),
                'type': d.get('type'),
                'severity': d.get('severity'),
                'confidence': round(d.get('confidence', 0), 4),
                'expected_value': d.get('expected_value'),
                'actual_value': d.get('actual_value'),
                'difference': d.get('difference'),
                'percentage_difference': round(d.get('percentage_difference', 0), 2) if d.get('percentage_difference') else None,
                'details': d.get('details'),
                'reasoning': d.get('reasoning')
            }
            for d in discrepancies
        ],
        'recommendation': {
            'action': recommendation.get('action'),
            'confidence': round(recommendation.get('confidence', 0), 4),
            'risk_assessment': recommendation.get('risk_assessment'),
            'requires_human_review': recommendation.get('requires_human_review'),
            'estimated_financial_impact': recommendation.get('estimated_financial_impact'),
            'reasoning': recommendation.get('reasoning'),
            'suggested_next_steps': recommendation.get('suggested_next_steps', [])
        },
        'agent_reasoning_chain': [
            {
                'agent': step.get('agent_name'),
                'timestamp': step.get('timestamp'),
                'confidence': round(step.get('confidence', 0), 4),
                'reasoning': step.get('reasoning'),
                'execution_time': round(step.get('execution_time', 0), 2)
            }
            for step in state.get('agent_steps', [])
        ],
        'errors': state.get('errors', [])
    }
    
    return output


def process_all_invoices(
    invoice_dir: str,
    config: Dict[str, Any],
    po_database: List[Dict[str, Any]],
    graph: InvoiceReconciliationGraph
) -> List[Dict[str, Any]]:
    """Process all invoices in a directory"""
    
    # Find all invoice files
    invoice_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']
    invoice_files = []
    
    for ext in invoice_extensions:
        invoice_files.extend(Path(invoice_dir).glob(f'*{ext}'))
        invoice_files.extend(Path(invoice_dir).glob(f'*{ext.upper()}'))
    
    logger.info(f"Found {len(invoice_files)} invoice files")
    
    results = []
    for invoice_path in invoice_files:
        try:
            result = process_invoice(str(invoice_path), config, po_database, graph)
            results.append(result)
            
            # Save individual result
            output_filename = f"{invoice_path.stem}_result.json"
            save_result(result, config.get('output', {}).get('output_directory', 'outputs'), output_filename)
            
        except Exception as e:
            logger.error(f"Failed to process {invoice_path}: {e}")
            results.append({
                'invoice_filename': invoice_path.name,
                'status': 'failed',
                'error': str(e)
            })
    
    return results


def generate_summary_report(results: List[Dict[str, Any]], output_dir: str):
    """Generate summary report of all processed invoices"""
    
    summary = {
        'total_invoices': len(results),
        'successful': sum(1 for r in results if r.get('processing_metadata', {}).get('status') == 'completed'),
        'failed': sum(1 for r in results if r.get('processing_metadata', {}).get('status') == 'failed'),
        'actions': {
            'auto_approve': sum(1 for r in results if r.get('recommendation', {}).get('action') == 'auto_approve'),
            'request_clarification': sum(1 for r in results if r.get('recommendation', {}).get('action') == 'request_clarification'),
            'escalate': sum(1 for r in results if r.get('recommendation', {}).get('action') == 'escalate_to_human')
        },
        'average_processing_time': sum(r.get('processing_metadata', {}).get('processing_time_seconds', 0) for r in results) / len(results) if results else 0,
        'average_confidence': sum(r.get('processing_metadata', {}).get('overall_confidence', 0) for r in results) / len(results) if results else 0,
        'invoices': [
            {
                'filename': r.get('processing_metadata', {}).get('invoice_filename'),
                'invoice_number': r.get('extraction', {}).get('invoice_number'),
                'status': r.get('processing_metadata', {}).get('status'),
                'recommendation': r.get('recommendation', {}).get('action'),
                'discrepancies_count': len(r.get('discrepancies', [])),
                'confidence': r.get('processing_metadata', {}).get('overall_confidence')
            }
            for r in results
        ]
    }
    
    save_result(summary, output_dir, 'summary_report.json')
    logger.info(f"Summary: {summary['successful']}/{summary['total_invoices']} successful")
    
    return summary


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Invoice Reconciliation System')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--invoice', help='Single invoice file to process')
    parser.add_argument('--invoice-dir', default='data/invoices', help='Directory containing invoices')
    parser.add_argument('--po-file', default='data/purchase_orders.json', help='Purchase orders file')
    parser.add_argument('--output-dir', default='outputs', help='Output directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--report', action='store_true', help='Generate summary report')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.debug else 'INFO'
    log_file = f"logs/invoice_processing_{time.strftime('%Y%m%d_%H%M%S')}.log"
    setup_logging(log_level, log_file)
    
    logger.info("=" * 60)
    logger.info("Invoice Reconciliation System")
    logger.info("=" * 60)
    
    # Load configuration
    config = load_config(args.config)
    
    # Override output directory if specified
    if args.output_dir:
        config.setdefault('output', {})['output_directory'] = args.output_dir
    
    # Load purchase orders
    po_database = load_purchase_orders(args.po_file)
    logger.info(f"Loaded {len(po_database)} purchase orders")
    
    # Initialize LLM
    llm = initialize_llm(config)
    
    # Initialize agents
    agents = initialize_agents(config, llm)
    
    # Create graph
    graph = InvoiceReconciliationGraph(agents, config)
    
    # Process invoices
    start_time = time.time()
    
    if args.invoice:
        # Process single invoice
        result = process_invoice(args.invoice, config, po_database, graph)
        results = [result]
        
        # Save result
        output_filename = f"{Path(args.invoice).stem}_result.json"
        save_result(result, args.output_dir, output_filename)
        
        logger.info(f"Result saved to {args.output_dir}/{output_filename}")
        
    else:
        # Process all invoices
        results = process_all_invoices(args.invoice_dir, config, po_database, graph)
    
    total_time = time.time() - start_time
    
    # Generate summary report
    if args.report or len(results) > 1:
        summary = generate_summary_report(results, args.output_dir)
        logger.info(f"Summary report saved to {args.output_dir}/summary_report.json")
    
    logger.info("=" * 60)
    logger.info(f"Processing complete: {len(results)} invoices in {total_time:.2f} seconds")
    logger.info(f"Average time per invoice: {total_time/len(results):.2f} seconds")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()