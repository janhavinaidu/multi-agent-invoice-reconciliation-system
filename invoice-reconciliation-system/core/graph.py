"""
LangGraph workflow for invoice reconciliation.
Orchestrates multi-agent system with intelligent retries and loopbacks.
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from core.state import InvoiceState, calculate_overall_confidence

logger = logging.getLogger(__name__)


class InvoiceReconciliationGraph:

    def __init__(self, agents: Dict[str, Any], config: Dict[str, Any]):
        self.agents = agents
        self.config = config
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(InvoiceState)

        # Nodes
        workflow.add_node("document_intelligence", self._document_node)
        workflow.add_node("matching", self._matching_node)
        workflow.add_node("discrepancy", self._discrepancy_node)
        workflow.add_node("resolution", self._resolution_node)
        workflow.add_node("error", self._error_node)

        workflow.set_entry_point("document_intelligence")

        # Conditional edges

        workflow.add_conditional_edges(
            "document_intelligence",
            self._after_document,
            {
                "match": "matching",
                "error": "error"
            }
        )

        workflow.add_conditional_edges(
            "matching",
            self._after_matching,
            {
                "discrepancy": "discrepancy",
                "retry": "document_intelligence",
                "error": "error"
            }
        )

        workflow.add_conditional_edges(
            "discrepancy",
            self._after_discrepancy,
            {
                "resolve": "resolution",
                "rematch": "matching",
                "error": "error"
            }
        )

        workflow.add_conditional_edges(
            "resolution",
            self._after_resolution,
            {
                "complete": END,
                "error": "error"
            }
        )

        workflow.add_edge("error", END)

        return workflow.compile()

    # ---------------- Nodes ---------------- #

    def _document_node(self, state: InvoiceState) -> InvoiceState:
        logger.info("Document Intelligence Agent")
        return self.agents["document_intelligence"].process(state)

    def _matching_node(self, state: InvoiceState) -> InvoiceState:
        logger.info("Matching Agent")
        return self.agents["matching"].process(state)

    def _discrepancy_node(self, state: InvoiceState) -> InvoiceState:
        logger.info("Discrepancy Detection Agent")
        return self.agents["discrepancy_detection"].process(state)

    def _resolution_node(self, state: InvoiceState) -> InvoiceState:
        logger.info("Resolution Agent")
        state = self.agents["resolution"].process(state)
        state["overall_confidence"] = calculate_overall_confidence(state)
        state["status"] = "completed"
        return state

    def _error_node(self, state: InvoiceState) -> InvoiceState:
        logger.error("Error handler triggered")

        if state.get("retry_count", 0) < 2:
            state["retry_count"] = state.get("retry_count", 0) + 1
            logger.info(f"Retrying pipeline (attempt {state['retry_count']})")
            return state

        state["status"] = "failed"
        return state

    # ---------------- Routing ---------------- #

    def _after_document(self, state: InvoiceState) -> str:
        if not state.get("extraction_result"):
            return "error"

        return "match"

    def _after_matching(self, state: InvoiceState) -> str:
        match = state.get("match_result")
        extraction = state.get("extraction_result", {})
        extraction_conf = extraction.get("confidence_score", 0.0)

        # Prevent infinite loops by checking how many times we've matched
        matching_attempts = len([s for s in state.get("agent_steps", []) if s.get("agent_name") == "matching"])

        if not match:
            # If extraction was good, don't keep retrying extraction just because matching failed
            if extraction_conf >= 0.8:
                return "discrepancy"
            return "retry" if matching_attempts < 2 else "error"

        if match.get("match_confidence", 0) < 0.5:
            # Only retry extraction if confidence was low AND extraction might be the cause
            logger.info(f"Low match confidence ({match.get('match_confidence')}). Extraction confidence: {extraction_conf}. Matching attempts: {matching_attempts}")
            if extraction_conf < 0.8 and matching_attempts < 2:
                logger.info("Retrying Document Intelligence...")
                return "retry"
            logger.info("Proceeding to Discrepancy Detection despite low match confidence.")
            return "discrepancy"

        return "discrepancy"

    def _after_discrepancy(self, state: InvoiceState) -> str:
        discrepancies = state.get("discrepancies", [])
        
        # Count how many times we've been through discrepancy detection
        discrepancy_attempts = len([s for s in state.get("agent_steps", []) if s.get("agent_name") == "discrepancy_detection"])

        # If missing PO and haven't rematched too many times → rematch (Invoice 5)
        for d in discrepancies:
            if d.get("type") == "missing_po_reference" and discrepancy_attempts < 2:
                return "rematch"

        return "resolve"

    def _after_resolution(self, state: InvoiceState) -> str:
        if state.get("status") == "completed":
            return "complete"

        return "error"

    # ---------------- API ---------------- #

    def process_invoice(self, initial_state: InvoiceState) -> InvoiceState:
        logger.info(f"Processing invoice: {initial_state['invoice_filename']}")
        return self.graph.invoke(initial_state)
