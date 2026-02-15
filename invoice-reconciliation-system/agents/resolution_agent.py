"""
Resolution Recommendation Agent
Decides: auto-approve, request clarification, escalate to human.
Pure rule + confidence based (no paid LLM).
"""

import os
import logging
import time
from datetime import datetime
from core.state import InvoiceState, add_agent_step

logger = logging.getLogger(__name__)


class ResolutionRecommendationAgent:

    def __init__(self, config: dict, llm=None):
        self.config = config.get("agents", {}).get("resolution", {})
        self.auto_threshold = self.config.get("auto_approve_confidence", 0.9)
        self.clarify_threshold = self.config.get("request_clarification_confidence", 0.7)

    def process(self, state: InvoiceState) -> InvoiceState:
        import os  # PARANOID IMPORT to fix persistent NameError
        start = time.time()
        logger.info("Running Resolution Agent")

        discrepancies = state.get("discrepancies", [])
        extraction = state.get("extraction_result", {})
        match = state.get("match_result", {})

        critical = [d for d in discrepancies if d.get("severity") == "critical"]
        warnings = [d for d in discrepancies if d.get("severity") == "warning"]

        extraction_conf = extraction.get("confidence_score", 0.0)
        match_conf = match.get("match_confidence", 0.0)

        avg_disc_conf = (
            sum(d.get("confidence", 0.0) for d in discrepancies) / len(discrepancies)
            if discrepancies else 1.0
        )

        overall_conf = (extraction_conf + match_conf + avg_disc_conf) / 3.0

        # Exact match bonus: if all items are high-confidence matches, boost confidence
        # We consider score >= 0.98 as effectively "exact" for risk assessment
        all_exact = all(
            m.get("match_type") == "exact" or m.get("confidence", 0) >= 0.98 
            for m in match.get("matched_items", [])
        ) if match.get("matched_items") else False
        
        if all_exact and not critical:
            overall_conf = max(overall_conf, 0.95)

        # Special Case: If the only critical error is missing_po_reference,
        # but we found a high-confidence semantic match, we can treat it as a warning.
        non_ref_critical = [d for d in critical if d.get("type") != "missing_po_reference"]
        if critical and not non_ref_critical and match_conf >= 0.8:
            logger.info("Downgrading missing_po_reference to warning for resolution decision (High Match Conf)")
            warnings.extend(critical)
            critical = []

        # ---------------- Decision ---------------- #

        if critical:
            action = "escalate_to_human"
            # More specific reasoning for better diagnostics
            reasons = [f"{d.get('type')} ({d.get('details', 'No details')})" for d in critical]
            reason = "Critical: " + "; ".join(reasons)
            summary = "Needs immediate human review due to severe discrepancies."
        
        elif extraction_conf < 0.5:
            action = "unapproved"
            reason = "Extremely low extraction confidence."
            summary = "The AI failed to reliably extract data from the document. Please re-upload a clearer copy."

        elif (not discrepancies or (all_exact and not critical)) and overall_conf >= self.auto_threshold:
            action = "auto_approve"
            reason = "Invoice fully matches PO with high confidence."
            summary = "Matching successful. Ready for payment processing."

        else:
            action = "pending"
            reason = "Minor issues detected."
            summary = "Automatic matching was partially successful. Manual confirmation required."

        # Safe financial impact calculation
        estimated_impact = 0.0
        for d in discrepancies:
            diff = d.get("difference")
            if diff is not None:
                estimated_impact += abs(diff)

        recommendation = {
            "action": action,
            "confidence": overall_conf,
            "risk_assessment": (
                "high" if action in ["escalate_to_human", "unapproved"] or critical
                else "low" if action == "auto_approve" or (all_exact and not critical)
                else "medium"
            ),
            "requires_human_review": action != "auto_approve",
            "estimated_financial_impact": estimated_impact,
            "suggested_next_steps": self._next_steps(action),
            "reasoning": reason,
            "summary": summary
        }

        state["recommendation"] = recommendation
        state["processing_completed"] = datetime.utcnow().isoformat()
        state["status"] = "completed"

        exec_time = time.time() - start

        state = add_agent_step(
            state,
            agent_name="resolution",
            reasoning=reason,
            confidence=overall_conf,
            input_summary=f"{len(discrepancies)} discrepancies",
            output_summary=f"Action: {action}",
            execution_time=exec_time,
        )

        return state

    def _next_steps(self, action):
        if action == "auto_approve":
            return ["Approve invoice automatically"]
        
        if action == "unapproved":
            return [
                "Re-scan or re-upload the document",
                "Verify document integrity",
                "Contact supplier for better quality PDF"
            ]

        if action == "escalate_to_human":
            return [
                "Review critical discrepancies",
                "Verify authorization",
                "Contact supplier if required",
            ]

        if action == "pending":
            return [
                "Verify quantities and prices",
                "Confirm semantic matches",
                "Manually match if necessary"
            ]

        return [
            "Request clarification from supplier",
            "Verify quantities and prices",
        ]
