"""
Utility functions for the invoice reconciliation system.
Free-stack compatible (Ollama + OCR + FAISS).
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import re

import numpy as np
from rapidfuzz import fuzz
# from sentence_transformers import SentenceTransformer
# import faiss


# ---------------- CONFIG ---------------- #

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.warning(f"Could not load config: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    return {
        "agents": {
            "document_intelligence": {"confidence_threshold": 0.7},
            "matching": {"fuzzy_threshold": 0.8},
            "discrepancy_detection": {"price_tolerance_percent": 5.0},
            "resolution": {"auto_approve_confidence": 0.9}
        },
        "llm": {
            "provider": "local",
            "model": "llama3",
            "temperature": 0.1
        }
    }


# ---------------- DATA ---------------- #

def load_purchase_orders(po_file: str) -> List[Dict[str, Any]]:
    try:
        with open(po_file, "r") as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]
    except Exception as e:
        logging.error(f"Failed to load purchase orders: {e}")
        return []


def save_result(result: Dict[str, Any], output_dir: str, filename: str):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)

    with open(path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    logging.info(f"Saved result to {path}")


# ---------------- TEXT NORMALIZATION ---------------- #

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = " ".join(text.split())
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return text.strip()


def fuzzy_match_score(a: str, b: str) -> float:
    return fuzz.token_sort_ratio(normalize_text(a), normalize_text(b)) / 100.0


# ---------------- SEMANTIC SEARCH ---------------- #

_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


# ---------------- SEMANTIC SEARCH (DISABLED FOR DEPLOYMENT) ---------------- #

def embed_texts(texts: List[str]) -> np.ndarray:
    return np.zeros((len(texts), 384))  # dummy embeddings


def build_faiss_index(texts: List[str]):
    dim = 384
    index = faiss.IndexFlatL2(dim)
    embeddings = embed_texts(texts)
    index.add(embeddings)
    return index, embeddings


def semantic_similarity(a: str, b: str) -> float:
    return 0.0  # fallback



# ---------------- NUMERIC HELPERS ---------------- #

def extract_numbers(text: str) -> List[float]:
    matches = re.findall(r"\d+(?:\.\d+)?", text)
    return [float(m) for m in matches]


def calculate_percentage_difference(v1: float, v2: float) -> float:
    if v2 == 0:
        return 0.0
    return abs((v1 - v2) / v2) * 100


# ---------------- DATE ---------------- #

def parse_date(date_string: str) -> Optional[datetime]:
    if not date_string:
        return None

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y"
    ]

    for f in formats:
        try:
            return datetime.strptime(date_string, f)
        except ValueError:
            continue

    return None


# ---------------- PO EXTRACTION ---------------- #

def extract_po_number(text: str) -> Optional[str]:
    # Support complex patterns like PO-2026-001 or standard PO-12345
    patterns = [
        r"((?:PO|Purchase\s+Order)[-\s]?[A-Z0-9]+(?:[-\s][A-Z0-9]+)*)"
    ]

    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = m.group(1).replace(" ", "").upper()
            if val in ["PO", "PURCHASEORDER"]:
                continue
            return val


# ---------------- LOGGING ---------------- #

def setup_logging(level="INFO", log_file: Optional[str] = None):
    handlers = [logging.StreamHandler()]
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True  # useful if logging was already configured
    )


# ---------------- VALIDATION ---------------- #

def validate_invoice_structure(data: Dict[str, Any]) -> bool:
    for k in ["invoice_number", "supplier_name", "total", "line_items"]:
        if k not in data:
            return False
    return True


def calculate_totals(items: List[Dict[str, Any]]) -> Dict[str, float]:
    subtotal = 0
    qty = 0

    for i in items:
        q = i.get("quantity", 0)
        p = i.get("unit_price", 0)
        subtotal += q * p
        qty += q

    return {
        "subtotal": subtotal,
        "item_count": len(items),
        "total_quantity": qty
    }


# ---------------- CONFIDENCE ---------------- #

class ConfidenceCalculator:

    @staticmethod
    def extraction_confidence(fields_found: int, total_fields: int) -> float:
        if total_fields == 0:
            return 0
        return min(fields_found / total_fields, 1.0)

    @staticmethod
    def match_confidence(matches: int, total: int) -> float:
        if total == 0:
            return 0
        return min(matches / total, 1.0)

    @staticmethod
    def discrepancy_confidence(delta_percent: float) -> float:
        return min(delta_percent / 10.0, 1.0)


def calculate_hash(data: Any) -> str:
    return hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
