"""
PO Extraction Agent
Extracts structured purchase order data from PDFs/images.
Similar to document intelligence but focused on PO fields.
"""

import logging
import time
from pathlib import Path
from datetime import datetime
import re

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

import pdfplumber

from core.state import add_agent_step
from core.utils import normalize_text, ConfidenceCalculator

logger = logging.getLogger(__name__)


class POExtractionAgent:
    
    def __init__(self, config: dict = None, llm=None):
        self.config = config or {}
        self.llm = llm
    
    def extract(self, file_path: str) -> dict:
        """Extract PO data from document"""
        start = time.time()
        
        logger.info(f"Extracting PO from {file_path}")
        
        # Extract text
        full_text = self._extract_text_native(file_path)
        
        if not full_text or len(full_text.strip()) < 50:
            logger.warning("Insufficient text extracted from PO")
            full_text = ""
        
        # Extract fields
        if self.llm:
            try:
                po_data = self._extract_po_fields_llm(full_text)
            except Exception as e:
                logger.error(f"LLM extraction failed: {e}. Falling back to regex.")
                po_data = self._extract_po_fields_regex(full_text)
        else:
            po_data = self._extract_po_fields_regex(full_text)
        
        # Calculate confidence
        fields_found = sum(1 for k in ['po_number', 'vendor', 'line_items'] 
                          if po_data.get(k))
        confidence = ConfidenceCalculator.extraction_confidence(fields_found, 3)
        
        po_data['confidence'] = confidence
        po_data['extraction_time'] = time.time() - start
        
        logger.info(f"Extracted PO: {po_data.get('po_number')}, Vendor: {po_data.get('vendor')}, Items: {len(po_data.get('line_items', []))}")
        
        return po_data

    def _extract_po_fields_llm(self, text: str) -> dict:
        """Use LLM to extract structured PO data"""
        from langchain.prompts import ChatPromptTemplate
        from langchain.output_parsers import ResponseSchema, StructuredOutputParser
        
        response_schemas = [
            ResponseSchema(name="po_number", description="The purchase order number"),
            ResponseSchema(name="vendor", description="The supplier or vendor name"),
            ResponseSchema(name="order_date", description="The date of the purchase order"),
            ResponseSchema(name="line_items", description="List of items, each with description, quantity, and unit_price")
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()
        
        prompt = ChatPromptTemplate.from_template(
            "You are an expert procurement analyst. Extract structured information from the following Purchase Order (PO) text. "
            "Identify the PO number, vendor name, order date, and all line items. "
            "Ensure the vendor name is the actual supplier company, not a date or label.\n\n"
            "PO Text:\n{text}\n\n"
            "{format_instructions}"
        )
        
        chain = prompt | self.llm | output_parser
        result = chain.invoke({"text": text, "format_instructions": format_instructions})
        
        # Normalize line items
        line_items = []
        for item in result.get("line_items", []):
            try:
                line_items.append({
                    "item_number": item.get("item_number"),
                    "description": item.get("description"),
                    "quantity": float(str(item.get("quantity", 0)).replace(',', '')),
                    "unit": item.get("unit", "units"),
                    "unit_price": float(str(item.get("unit_price", 0)).replace(',', '').replace('$', ''))
                })
            except (ValueError, TypeError):
                continue
        
        result["line_items"] = line_items
        result["status"] = "approved"
        return result

    def _extract_text_native(self, path: str) -> str:
        """Extract text using pdfplumber"""
        text = ""
        try:
            if Path(path).suffix.lower() == '.pdf':
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
        except Exception as e:
            logger.warning(f"Native PDF extraction failed: {e}")
        return text
    
    def _extract_po_fields_regex(self, text: str) -> dict:
        """Extract PO fields from text using regex (fallback)"""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        joined = " ".join(lines)
        
        # Extract PO number
        po_number = self._find_po_number(joined)
        
        # Extract vendor
        vendor = self._find_vendor(lines)
        
        # Extract order date
        order_date = self._find_date(joined, ["order date", "po date", "date"])
        
        # Extract line items
        line_items = self._extract_line_items(text)
        
        return {
            "po_number": po_number,
            "vendor": vendor,
            "order_date": order_date,
            "status": "approved",  # Default status
            "line_items": line_items
        }
    
    def _find_po_number(self, text: str) -> str:
        """Find PO number in text"""
        patterns = [
            r"po\s*#?:?\s*([A-Z0-9\-]+)",
            r"purchase\s*order\s*#?:?\s*([A-Z0-9\-]+)",
            r"p\.?o\.?\s*number:?\s*([A-Z0-9\-]+)"
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None
    
    def _find_vendor(self, lines: list) -> str:
        """Find vendor name (usually in first few lines)"""
        skip_keywords = ['purchase', 'order', 'po', 'vendor', 'supplier']
        for line in lines[:10]:
            if len(line) > 3 and not any(kw in line.lower() for kw in skip_keywords):
                if any(c.isalpha() for c in line):
                    return line
        return lines[0] if lines else ""
    
    def _find_date(self, text: str, keywords: list) -> str:
        """Find date in text"""
        for keyword in keywords:
            pattern = rf"{keyword}\s*:?\s*(\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}})"
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None
    
    def _extract_line_items(self, text: str) -> list:
        """Extract line items from PO"""
        items = []
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        
        for line in lines:
            # Skip header and metadata lines
            if any(kw in line.lower() for kw in ['purchase', 'order', 'total', 'subtotal', 'tax', 'date', 'vendor', 'ship to', 'bill to']):
                continue
            
            # Look for lines with numbers (qty and price)
            numbers = re.findall(r'(\d+(?:[,.]\d+)*(?:[,.]\d+)?)', line)
            
            if len(numbers) >= 3:
                try:
                    # Clean the numbers
                    clean_nums = [float(n.replace(',', '')) for n in numbers]
                    
                    # Try different combinations to find qty, price, total
                    # Common patterns: [qty, price, total] or [item_id, qty, price, total]
                    
                    # Try: last three numbers are qty, price, total
                    if abs(clean_nums[-3] * clean_nums[-2] - clean_nums[-1]) < 0.01:
                        qty, unit_price = clean_nums[-3], clean_nums[-2]
                    # Try: middle three numbers are qty, price, total (when there's an item_id)
                    elif len(clean_nums) >= 4 and abs(clean_nums[-4+1] * clean_nums[-4+2] - clean_nums[-4+3]) < 0.01:
                        qty, unit_price = clean_nums[-4+1], clean_nums[-4+2]
                    else:
                        # Fallback: assume last two are qty and price, calculate total
                        qty, unit_price = clean_nums[-2], clean_nums[-1]
                        
                    # Extract description
                    desc_match = re.match(r'^(.+?)\s+\d+', line)
                    description = desc_match.group(1).strip() if desc_match else line.split()[0]
                    
                    # Validate
                    if not any(c.isalpha() for c in description):
                        continue
                    if len(description) < 3:
                        continue
                    
                    # Extract item number if present
                    item_num_match = re.match(r'^([A-Z]{2,}-\d+)', description)
                    item_number = item_num_match.group(1) if item_num_match else None
                    
                    items.append({
                        "item_number": item_number,
                        "description": description,
                        "quantity": qty,
                        "unit": None,  # Don't default to "kg"
                        "unit_price": unit_price
                    })
                except (ValueError, IndexError):
                    continue
        
        logger.info(f"Extracted {len(items)} line items from PO")
        return items
