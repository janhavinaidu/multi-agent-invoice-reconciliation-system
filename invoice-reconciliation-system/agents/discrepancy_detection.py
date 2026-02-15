"""
Discrepancy Detection Agent
Detects price, quantity, total mismatches and missing PO.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any

from core.state import InvoiceState
from core.utils import calculate_percentage_difference
from core.state import add_agent_step

logger = logging.getLogger(__name__)


class DiscrepancyDetectionAgent:

    def __init__(self, config: dict, llm=None):
        self.config = config.get("agents", {}).get("discrepancy_detection", {})
        self.price_tolerance = self.config.get("price_tolerance_percent", 5.0)
        self.quantity_tolerance = self.config.get("quantity_tolerance", 0)

    def process(self, state: InvoiceState) -> InvoiceState:
        start = time.time()
        logger.info("Running Discrepancy Detection Agent")

        extraction = state.get("extraction_result")
        match = state.get("match_result")

        if not extraction or not match:
            state["status"] = "failed"
            return state

        discrepancies = []

        # Missing PO (Invoice 5)
        if not extraction.get("po_reference"):
            discrepancies.append(self._missing_po(extraction, bool(match.get("po_number"))))

        matched = match.get("matched_items", [])
        fuzzy = match.get("fuzzy_matches", [])

        # Deduplicate items to avoid double reporting if same item is extracted/matched twice
        all_items = matched + fuzzy
        seen_items = []
        unique_items = []
        
        for item in all_items:
            # Create a unique key for the item based on description, qty, and price
            inv_item = item.get("invoice_item", {})
            item_key = (
                str(inv_item.get("description", "")).lower().strip(),
                inv_item.get("quantity"),
                inv_item.get("unit_price")
            )
            if item_key not in seen_items:
                seen_items.append(item_key)
                unique_items.append(item)
            else:
                logger.warning(f"Skipping duplicate matched item for discrepancy check: {item_key[0]}")

        discrepancies += self._price_checks(unique_items)
        discrepancies += self._quantity_checks(unique_items)

        if match.get("unmatched_items"):
            discrepancies.append(self._unmatched(match["unmatched_items"]))

        total_disc = self._total_check(extraction, matched + fuzzy)
        if total_disc:
            discrepancies.append(total_disc)

        state["discrepancies"] = discrepancies

        exec_time = time.time() - start

        reasoning = (
            "No discrepancies found."
            if not discrepancies
            else f"Detected {len(discrepancies)} discrepancies."
        )

        confidence = 0.95 if not discrepancies else max(0.4, 1 - 0.1 * len(discrepancies))

        state = add_agent_step(
            state,
            agent_name="discrepancy_detection",
            reasoning=reasoning,
            confidence=confidence,
            input_summary="Comparing invoice vs PO items",
            output_summary=f"{len(discrepancies)} discrepancies",
            execution_time=exec_time
        )

        return state

    # ---------------- Helpers ---------------- #

    def _missing_po(self, extraction: dict, match_found: bool) -> dict:
        severity = "warning" if match_found else "critical"
        return {
            "discrepancy_id": str(uuid.uuid4()),
            "type": "missing_po_reference",
            "severity": severity,
            "confidence": 0.95,
            "expected_value": "PO reference",
            "actual_value": extraction.get("po_reference"),
            "details": "Invoice does not contain valid PO number",
            "reasoning": "Missing PO reference on document. Semantic match found instead." if match_found else "Missing PO prevents direct authorization check."
        }

    def _price_checks(self, items):
        out = []

        for m in items:
            inv = m.get("invoice_item", {})
            po = m.get("po_item")

            if not po:
                continue

            ip = inv.get("unit_price", 0)
            pp = po.get("unit_price", 0)

            if not ip or not pp:
                continue

            pct = calculate_percentage_difference(ip, pp)

            if pct > self.price_tolerance:
                severity = "critical" if pct >= 10 else "warning"
                out.append({
                    "discrepancy_id": str(uuid.uuid4()),
                    "type": "price_mismatch",
                    "severity": severity,
                    "confidence": min(0.9 + pct / 100, 1.0),
                    "expected_value": pp,
                    "actual_value": ip,
                    "percentage_difference": pct,
                    "details": f"Price differs by {pct:.1f}% for '{inv.get('description', 'item')}'",
                    "reasoning": f"Invoice price for '{inv.get('description', 'item')}' exceeds PO tolerance."
                })

        return out

    def _quantity_checks(self, items):
        out = []

        for m in items:
            inv = m.get("invoice_item", {})
            po = m.get("po_item")

            if not po:
                continue

            iq = inv.get("quantity", 0)
            pq = po.get("quantity", 0)

            if not iq or not pq:
                continue

            EPSILON = 1e-5
            if abs(iq - pq) > (self.quantity_tolerance + EPSILON):
                pct = calculate_percentage_difference(iq, pq)
                out.append({
                    "discrepancy_id": str(uuid.uuid4()),
                    "type": "quantity_mismatch",
                    "severity": "warning",
                    "confidence": 0.85,
                    "expected_value": pq,
                    "actual_value": iq,
                    "percentage_difference": pct,
                    "details": f"Quantity mismatch for '{inv.get('description', 'item')}'",
                    "reasoning": f"Invoice quantity for '{inv.get('description', 'item')}' does not match PO."
                })

        return out

    def _unmatched(self, items):
        return {
            "discrepancy_id": str(uuid.uuid4()),
            "type": "unmatched_items",
            "severity": "warning",
            "confidence": 0.8,
            "details": f"{len(items)} invoice items not found in PO",
            "reasoning": "Some invoice items are not present in purchase order."
        }

    def _total_check(self, extraction, items):
        invoice_total = extraction.get("total", 0)

        expected = 0
        for m in items:
            inv = m.get("invoice_item", {})
            expected += inv.get("quantity", 0) * inv.get("unit_price", 0)

        if not expected:
            return None

        pct = calculate_percentage_difference(invoice_total, expected)

        if pct > 15:
            return {
                "discrepancy_id": str(uuid.uuid4()),
                "type": "total_amount_mismatch",
                "severity": "warning",
                "confidence": 0.7,
                "expected_value": expected,
                "actual_value": invoice_total,
                "percentage_difference": pct,
                "details": "Invoice total differs from line items",
                "reasoning": "Possible tax/fee or calculation error."
            }

        return None
