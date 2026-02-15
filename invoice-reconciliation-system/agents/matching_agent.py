"""
Matching Agent
Matches extracted invoice items to Purchase Orders using:
- Exact PO match
- Fuzzy string match (RapidFuzz)
- Semantic search (FAISS + SentenceTransformers)

Critical for Invoice 5.
"""

import logging
import time
from typing import List, Dict, Any

from core.state import InvoiceState, add_agent_step
from core.utils import (
    fuzzy_match_score,
    build_faiss_index,
    embed_texts,
    ConfidenceCalculator
)

logger = logging.getLogger(__name__)


class MatchingAgent:

    def __init__(self, config: dict, llm=None, po_db: List[Dict[str, Any]] = None):
        self.config = config.get("agents", {}).get("matching", {})
        self.fuzzy_threshold = self.config.get("fuzzy_threshold", 0.8)

        if po_db is not None:
            self.po_db = po_db
            logger.info(f"Using provided PO database with {len(self.po_db)} entries")
        else:
            # Load PO database once
            from core.utils import load_purchase_orders
            po_path = config.get("data", {}).get("purchase_orders_file", "data/purchase_orders.json")
            self.po_db = load_purchase_orders(po_path)
            logger.info(f"Loaded {len(self.po_db)} purchase orders from {po_path}")

        # Prepare semantic index for Invoice 5
        self.po_texts = []
        self.po_items = []

        for po in self.po_db:
            for item in po.get("line_items", []):
                text = f"{po.get('vendor','')} {item.get('description','')}"
                self.po_texts.append(text)
                self.po_items.append((po, item))

        logger.info(f"Prepared {len(self.po_texts)} PO items for semantic search")

        if self.po_texts:
            self.faiss_index, self.po_embeddings = build_faiss_index(self.po_texts)
        else:
            self.faiss_index = None
            logger.warning("No PO items available for semantic search")

    # ---------------- Main ---------------- #

    def process(self, state: InvoiceState) -> InvoiceState:
        start = time.time()
        extraction = state.get("extraction_result")
        
        # Priority 1: Use explicitly uploaded PO path from state
        # Priority 2: Use PO reference from invoice
        
        invoice_items = extraction.get("line_items", [])
        po_ref = extraction.get("po_reference")
        uploaded_po_path = state.get("uploaded_po_path")

        matched = []
        fuzzy = []
        unmatched = []

        matched_po = None
        
        # -------- Identify Target PO -------- #
        
        if uploaded_po_path:
            logger.info(f"Using explicitly uploaded PO for matching: {uploaded_po_path}")
            # Try to find this PO in our database (usually added during upload step)
            # Actually, the po_service.add_po saves it to the main database.
            # But the extraction might have returned a filename or ID. 
            # For now, let's assume we match against all POs but prioritize the one most recently added 
            # if we have no reference. Or if we have a path, we can try to find by ID.
            pass

        if po_ref:
            logger.info(f"Looking for PO reference: {po_ref}")
            for po in self.po_db:
                # Ensure we only match if po_number is also truthy
                db_po_num = po.get("po_number")
                if db_po_num and str(db_po_num).upper() == str(po_ref).upper():
                    matched_po = po
                    logger.info(f"Found exact PO match: {po_ref}")
                    break
            if not matched_po:
                logger.warning(f"PO reference '{po_ref}' not found in database.")
        else:
            logger.info("No PO reference provided in extraction result.")
        
        # -------- Matching Logic -------- #

        for inv in invoice_items:
            best = None
            best_score = 0
            best_po = None

            # 1. Try matching within the matched_po (if found)
            if matched_po:
                for item in matched_po.get("line_items", []):
                    score = fuzzy_match_score(inv.get("description", ""), item.get("description", ""))
                    if score > best_score:
                        best_score = score
                        best = item
                        best_po = matched_po

            # 2. If no high-confidence match in matched_po, search entire database
            if best_score < self.fuzzy_threshold:
                for po, item in self.po_items:
                    # Skip if we already checked this PO above
                    if matched_po and po.get("po_number") == matched_po.get("po_number"):
                        continue
                        
                    score = fuzzy_match_score(inv.get("description", ""), item.get("description", ""))
                    if score > best_score:
                        best_score = score
                        best = item
                        best_po = po

            # 3. Semantic fallback
            if best_score < self.fuzzy_threshold and self.faiss_index:
                try:
                    desc = inv.get("description", "")
                    if desc:
                        emb = embed_texts([desc])
                        D, I = self.faiss_index.search(emb.astype('float32'), 1)
                        if I[0][0] != -1:
                            semantic_po, semantic_item = self.po_items[I[0][0]]
                            # Map L2 distance to a 0-1 score (lower distance = higher score)
                            # Typical L2 distances for MiniLM are 0 to ~2
                            dist = float(D[0][0])
                            semantic_score = max(0, 1.0 - (dist / 2.0))
                            
                            if semantic_score > best_score:
                                best_score = semantic_score
                                best = semantic_item
                                best_po = semantic_po
                                logger.debug(f"Semantic search improved score for '{desc}' to {semantic_score:.2f}")
                except Exception as e:
                    logger.error(f"Semantic search failed: {e}")

            if best_score >= self.fuzzy_threshold:
                matched.append({
                    "invoice_item": inv,
                    "po_item": best,
                    "match_type": "exact" if matched_po and best_po.get("po_number") == matched_po.get("po_number") else "fuzzy",
                    "confidence": best_score
                })
                logger.info(f"MATCH SUCCESS: '{inv.get('description')}' -> '{best.get('description')}' (score: {best_score:.2f})")
                if not matched_po:
                    matched_po = best_po
            elif best_score > 0.4:
                fuzzy.append({
                    "invoice_item": inv,
                    "po_item": best,
                    "match_type": "semantic",
                    "confidence": best_score
                })
                logger.info(f"FUZZY MATCH: '{inv.get('description')}' -> '{best.get('description')}' (score: {best_score:.2f})")
                if not matched_po:
                    matched_po = best_po
            else:
                logger.warning(f"MATCH FAILURE: No match found for: '{inv.get('description')}' (best score: {best_score:.2f})")
                unmatched.append({"invoice_item": inv})

        # -------- Confidence Calculation (Improved) -------- #

        # Exact/High-confidence fuzzy count as full matches (1.0)
        # Semantic matches count as partial matches if they are above 0.5
        match_count = len(matched)
        for f in fuzzy:
            if f["confidence"] > 0.7:
                match_count += 0.8
            else:
                match_count += 0.5
                
        confidence = ConfidenceCalculator.match_confidence(match_count, len(invoice_items))

        match_result = {
            "po_number": matched_po.get("po_number") if matched_po else None,
            "match_type": "exact" if matched_po and any(m["match_type"] == "exact" for m in matched) else ("semantic" if matched_po else "none"),
            "match_confidence": confidence,
            "matched_items": matched,
            "fuzzy_matches": fuzzy,
            "unmatched_items": unmatched,
            "reasoning": f"{len(matched)} high-conf matches, {len(fuzzy)} semantic matches, {len(unmatched)} unmatched"
        }

        state["match_result"] = match_result
        state["matched_po"] = matched_po

        exec_time = time.time() - start

        state = add_agent_step(
            state,
            agent_name="matching",
            reasoning=match_result["reasoning"],
            confidence=confidence,
            input_summary=f"{len(invoice_items)} invoice items",
            output_summary=match_result["reasoning"],
            execution_time=exec_time
        )

        return state
