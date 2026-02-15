"""
Document Intelligence Agent
Extracts structured invoice data from PDFs / images using OCR + heuristics.
Free stack: Tesseract + OpenCV.
"""

import cv2
import pytesseract
import numpy as np
import logging
import time
from pathlib import Path
from datetime import datetime
from datetime import datetime
try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

import pdfplumber

from core.state import InvoiceState, add_agent_step
from core.utils import normalize_text, extract_po_number, ConfidenceCalculator

logger = logging.getLogger(__name__)


class DocumentIntelligenceAgent:

    def __init__(self, config: dict, llm=None):
        self.config = config.get("agents", {}).get("document_intelligence", {})
        self.ocr_config = self.config.get("ocr_config", "--psm 6")
        self.llm = llm
        
        # Configure Tesseract path for Windows if not in PATH
        import platform
        if platform.system() == 'Windows':
            import os
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe')
            ]
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    logger.info(f"Tesseract found at: {path}")
                    break

    # ---------------- Main ---------------- #

    def process(self, state: InvoiceState) -> InvoiceState:
        start = time.time()

        path = state["invoice_path"]
        logger.info(f"OCR processing {path}")

        # Try native extraction first
        full_text = self._extract_text_native(path)
        processing_method = "native_pdf_extraction"
        
        # Check if native extraction produced good results
        # If text has no line breaks or seems jumbled, fallback to OCR
        if not full_text or len(full_text.strip()) < 50 or '\n' not in full_text:
            logger.info("Native extraction produced poor results. Falling back to OCR.")
            processing_method = "ocr_tesseract"
            
            try:
                images = self._load_images(path)
                full_text = ""
                for img in images:
                    img = self._preprocess(img)
                    full_text += pytesseract.image_to_string(img, config=self.ocr_config) + "\n"
            except Exception as e:
                logger.error(f"OCR failed: {e}")
                if not full_text:
                    # Reraise if we have absolutely no text
                     raise e

        # Extract fields using LLM if available
        if self.llm:
            try:
                structured = self._extract_fields_llm(full_text)
            except Exception as e:
                logger.error(f"LLM field extraction failed: {e}. Falling back to regex.")
                structured = self._extract_fields_regex(full_text)
        else:
            structured = self._extract_fields_regex(full_text)

        fields_found = sum(1 for k in structured if structured[k])
        confidence = ConfidenceCalculator.extraction_confidence(fields_found, 6)

        structured["confidence_score"] = confidence
        structured["ocr_quality"] = "good"
        structured["warnings"] = []

        state["extraction_result"] = structured

        exec_time = time.time() - start

        state = add_agent_step(
            state,
            agent_name="document_intelligence",
            reasoning=f"Document processed using {processing_method}. Fields extracted with {'LLM' if self.llm else 'regex'}.",
            confidence=confidence,
            input_summary="Raw PDF/Image",
            output_summary="Structured invoice fields",
            execution_time=exec_time
        )

        return state

    def _extract_fields_llm(self, text: str) -> dict:
        """Use LLM to extract structured invoice data"""
        from langchain.prompts import ChatPromptTemplate
        from langchain.output_parsers import ResponseSchema, StructuredOutputParser
        
        response_schemas = [
            ResponseSchema(name="invoice_number", description="The invoice number"),
            ResponseSchema(name="supplier_name", description="The supplier or vendor name"),
            ResponseSchema(name="po_reference", description="The purchase order reference number"),
            ResponseSchema(name="invoice_date", description="The date of the invoice"),
            ResponseSchema(name="total", description="The total amount of the invoice"),
            ResponseSchema(name="currency", description="The currency code (e.g. USD, EUR)"),
            ResponseSchema(name="line_items", description="List of items, each with description, quantity, and unit_price")
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()
        
        prompt = ChatPromptTemplate.from_template(
            "You are an expert document analyzer. Extract structured information from the following invoice text. "
            "Pay close attention to finding the Purchase Order (PO) reference number - it often looks like PO-XXXXX or is near the words 'Purchase Order' or 'PO Reference'. "
            "Also ensure the supplier_name is the actual company name, not a date or label.\n\n"
            "Invoice Text:\n{text}\n\n"
            "{format_instructions}"
        )
        
        chain = prompt | self.llm | output_parser
        result = chain.invoke({"text": text, "format_instructions": format_instructions})
        
        # Normalize line items
        line_items = []
        for item in result.get("line_items", []):
            try:
                price = float(str(item.get("unit_price", 0)).replace(',', '').replace('$', ''))
                qty = float(str(item.get("quantity", 0)).replace(',', ''))
                line_items.append({
                    "item_number": item.get("item_number"),
                    "description": item.get("description"),
                    "quantity": qty,
                    "unit": item.get("unit", "units"),
                    "unit_price": price,
                    "total_price": qty * price,
                    "confidence": 0.9
                })
            except (ValueError, TypeError):
                continue
        
        result["line_items"] = line_items
        result["total"] = float(str(result.get("total", 0)).replace(',', '').replace('$', ''))
        return result

    # ---------------- Native Extraction ---------------- #

    def _extract_text_native(self, path: str) -> str:
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

    # ---------------- Image Loading ---------------- #

    def _load_images(self, path):
        ext = Path(path).suffix.lower()

        if ext == ".pdf":
            # Try poppler first
            if convert_from_path:
                try:
                    return [np.array(p) for p in convert_from_path(path)]
                except Exception:
                    pass
            
            # Fallback to pypdf image extraction
            return self._extract_images_from_pdf(path)
        else:
            img = cv2.imread(path)
            return [img]

    def _extract_images_from_pdf(self, path):
        """Extract images from PDF using PyMuPDF (renders pages to images)"""
        if not fitz:
            raise ImportError("PyMuPDF (fitz) not installed. Install with: pip install pymupdf")
        
        images = []
        try:
            doc = fitz.open(path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Render page to image at 300 DPI for good OCR quality
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                # Convert to numpy array
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                # PyMuPDF returns RGB/RGBA, OpenCV expects BGR
                if pix.n == 4:  # RGBA
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:  # RGB
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                # else: grayscale, leave as is
                images.append(img)
            doc.close()
        except Exception as e:
            logger.error(f"Failed to render PDF pages: {e}")
            raise ImportError(f"Could not convert PDF to images: {e}")
        
        return images

    # ---------------- Preprocessing ---------------- #

    def _preprocess(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        gray = cv2.medianBlur(gray, 3)
        return gray

    # ---------------- Field Extraction ---------------- #

    def _extract_fields_regex(self, text: str):
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        joined = " ".join(lines)

        # Extract invoice number with better patterns
        invoice_number = self._find_invoice_number(joined)
        
        # Extract supplier (first non-empty line that looks like a company name)
        supplier = self._find_supplier(lines)
        
        # Extract PO reference
        po_ref = extract_po_number(joined)
        
        # Extract dates
        invoice_date = self._find_date(joined, ["invoice date", "date", "issued"])
        due_date = self._find_date(joined, ["due date", "payment due"])

        # Extract line items with validation - use original text, not joined
        line_items = self._extract_line_items(text)
        
        # Extract totals - prioritize total due over subtotal
        total = self._find_amount(joined, ["total due", "grand total", "total amount", "total"])
        subtotal = self._find_amount(joined, ["subtotal", "sub-total", "sub total"])
        tax = self._find_amount(joined, ["tax", "vat", "gst"])
        
        # If no explicit total found, calculate from line items
        if not total and line_items:
            total = sum(item.get('total_price', 0) for item in line_items)

        logger.info(f"Extracted: Invoice#{invoice_number}, Supplier={supplier}, PO={po_ref}, Items={len(line_items)}, Total={total}")

        return {
            "invoice_number": invoice_number,
            "supplier_name": supplier,
            "supplier_address": None,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "po_reference": po_ref,
            "line_items": line_items,
            "subtotal": subtotal,
            "tax": tax,
            "total": total or 0,
            "currency": "USD"
        }

    def _find(self, pattern, text):
        import re
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1) if m else None

    def _find_invoice_number(self, text):
        import re
        # Try multiple patterns
        patterns = [
            r"invoice\s*#?\s*:?\s*([A-Z0-9\-]+)",
            r"inv\s*#?\s*:?\s*([A-Z0-9\-]+)",
            r"#\s*([A-Z0-9\-]{3,})"
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None
    
    def _find_supplier(self, lines):
        # First line is usually the supplier, but skip if it looks like a header
        skip_keywords = ['invoice', 'bill', 'statement', 'receipt']
        for line in lines[:5]:  # Check first 5 lines
            if len(line) > 3 and not any(kw in line.lower() for kw in skip_keywords):
                # Stop at first line that looks like a company name
                if any(c.isalpha() for c in line):
                    return line
        return lines[0] if lines else ""
    
    def _find_date(self, text, keywords):
        import re
        for keyword in keywords:
            # Look for date near keyword
            pattern = rf"{keyword}\s*:?\s*(\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}})"
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None
    
    def _find_amount(self, text, keywords):
        import re
        for keyword in keywords:
            # Look for amount near keyword - improved pattern to handle commas and optional decimals
            pattern = rf"{keyword}\s*:?\s*£?\s*(\d{{1,3}}(?:,\d{{3}})*(?:\.\d{{2}})?)"
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                amount_str = m.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except:
                    pass
        return None

    def _extract_line_items(self, text):
        import re
        items = []
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        
        # Keywords that usually indicate we are NOT in the line items table anymore
        stop_keywords = ['total', 'subtotal', 'tax', 'vat', 'discount', 'payment', 'balance', 'due']
        
        # Additional keywords and patterns to filter out non-line-items
        exclude_keywords = [
            'tel:', 'phone:', 'email:', 'vat:', 'sort code:', 'account:', 'iban:', 
            'payment details', 'thank you', 'please quote', 'business', 'invoice number:',
            'bill to:', 'ship to:', 'payment terms:', 'net', 'days', 'unit', 'price', 'total',
            'item code', 'description', 'quantity', 'invoice date:', 'po reference:', 'po-',
            'limited', 'centre', 'united kingdom', 'manchester', 'uxbridge', 'industrial estate'
        ]
        
        for line in lines:
            line_lower = line.lower()
            
            # Skip noise lines and headers
            if any(kw in line_lower for kw in exclude_keywords):
                continue
            
            # Skip lines that look like addresses, contact info, or payment details
            if any(pattern in line_lower for pattern in ['sort code', 'account:', 'iban:', 'vat:', 'tel:']):
                continue
            
            # Find all numbers (including decimals)
            # Match formats like 100, 100.00, 1,000.00, and standalone integers
            number_matches = re.findall(r'(\d+(?:[,.]\d+)*(?:[,.]\d+)?)', line)
            
            # Skip lines that are too short or contain only separators
            if len(line.strip()) < 5 or line.strip() in ['---', '===', '|||']:
                continue
            
            # Only process lines that look like line items
            # Should contain product codes (like API-001)
            has_item_code = bool(re.search(r'[A-Z]{2,}-\d{3,}', line)) and not any(
                prefix in line.upper() for prefix in ['INV-', 'PO-', 'INVOICE-', 'PURCHASE-']
            )
            has_product_words = any(word in line_lower for word in [
                'monitor', 'keyboard', 'dell', 'wireless', 'mouse', 'laptop', 'computer',
                'paracetamol', 'cellulose', 'magnesium', 'titanium', 'stearate', 'dioxide',
                'bp', 'mg', 'kg', 'microcrystalline', 'ph eur'
            ])
            
            # More restrictive description check
            # Exclude lines that start with obvious headers
            line_start_excludes = ['invoice', 'date', 'po reference', 'supplier', 'bill to', 'item', 'qty', 'unit', 'price', 'amount', 'subtotal', 'shipping', 'total']
            starts_with_header = any(line_lower.startswith(exclude) for exclude in line_start_excludes)
            
            # Also exclude lines that contain obvious non-product patterns
            contains_non_product = any(pattern in line_lower for pattern in [
                'invoice number', 'inv-', 'po-', 'purchase order', 'date', 'supplier', 'bill to'
            ])
            
            # Also check if it has typical product description patterns
            has_description = (
                not starts_with_header and
                not contains_non_product and
                len(line.split()) >= 2 and  # At least 2 words
                any(char.isalpha() for char in line) and  # Contains letters
                len(number_matches) >= 2 and  # Has at least 2 numbers
                # Should not be just a header line with labels
                not all(word in ['item', 'qty', 'unit', 'price', 'amount', 'quantity', 'total'] for word in line_lower.split())
            )
            
            if not (has_item_code or has_product_words or has_description):
                continue
            
            if len(number_matches) >= 2:
                try:
                    # Clean the numbers
                    clean_nums = [float(n.replace(',', '')) for n in number_matches]
                    
                    # Validate that numbers are reasonable
                    # Filter out extremely large numbers (likely account numbers, etc.)
                    reasonable_nums = []
                    for num in clean_nums:
                        if num < 1000000:  # Ignore numbers over 1 million
                            reasonable_nums.append(num)
                    
                    if len(reasonable_nums) < 2:
                        continue
                    
                    clean_nums = reasonable_nums
                    
                    # Logic: 
                    # If 3+ numbers: usually [qty, price, total] or [item_nr, qty, price, total]
                    # If 2 numbers: [qty, price]
                    
                    if len(clean_nums) >= 3:
                        # Try different combinations to find qty, price, total
                        # Common patterns: [qty, price, total] or [item_id, qty, price, total]
                        
                        # Try: last three numbers are qty, price, total
                        if abs(clean_nums[-3] * clean_nums[-2] - clean_nums[-1]) < 0.01:
                            qty, price, total = clean_nums[-3], clean_nums[-2], clean_nums[-1]
                        # Try: middle three numbers are qty, price, total (when there's an item_id)
                        elif len(clean_nums) >= 4 and abs(clean_nums[-4+1] * clean_nums[-4+2] - clean_nums[-4+3]) < 0.01:
                            qty, price, total = clean_nums[-4+1], clean_nums[-4+2], clean_nums[-4+3]
                        else:
                            # Fallback: assume last two are qty and price, calculate total
                            qty, price = clean_nums[-2], clean_nums[-1]
                            total = qty * price
                    else:
                        qty, price = clean_nums[-2], clean_nums[-1]
                        total = qty * price

                    # Extract description: 
                    # It's usually the part of the line before the quantity number
                    # We need to find where the quantity starts in the line
                    
                    if len(clean_nums) >= 3:
                        # Find the position of the quantity number in the line
                        if abs(clean_nums[-3] * clean_nums[-2] - clean_nums[-1]) < 0.01:
                            # Last three are qty, price, total
                            qty_str = number_matches[-3]
                            qty_pos = line.find(qty_str)
                            description = line[:qty_pos].strip()
                        elif len(clean_nums) >= 4:
                            # Middle three are qty, price, total (item_id, qty, price, total)
                            qty_str = number_matches[-3]  # Second to last is qty in this pattern
                            qty_pos = line.find(qty_str)
                            # Find item_id position to exclude it from description
                            item_id_str = number_matches[0]
                            item_id_pos = line.find(item_id_str)
                            description = line[item_id_pos + len(item_id_str):qty_pos].strip()
                        else:
                            # Fallback
                            qty_str = number_matches[-2]
                            qty_pos = line.find(qty_str)
                            description = line[:qty_pos].strip()
                    else:
                        # Only 2 numbers (Qty, Price)
                        qty_str = number_matches[-2]
                        qty_pos = line.find(qty_str)
                        description = line[:qty_pos].strip()
                    
                    # Clean up description (remove leading/trailing separators)
                    description = re.sub(r"^[.\s\-_]+", "", description)
                    description = re.sub(r"[.\s\-_]+$", "", description)
                    
                    # Filter out short descriptions or headers
                    if len(description) < 3 or description.lower() in ['qty', 'description', 'price', 'unit']:
                        continue
                        
                    # Validate: should have letters
                    if not any(c.isalpha() for c in description):
                        continue
                    
                    # Additional validation for reasonable quantities and prices
                    if qty <= 0 or qty > 10000:  # Reasonable quantity range
                        continue
                    if price <= 0 or price > 100000:  # Reasonable price range
                        continue
                    if total > 1000000:  # Reasonable total range
                        continue

                    items.append({
                        "item_number": None,
                        "description": description,
                        "quantity": qty,
                        "unit": None,
                        "unit_price": price,
                        "total_price": total,
                        "confidence": 0.85
                    })
                except (ValueError, IndexError):
                    continue
        
        logger.info(f"Extracted {len(items)} line items with improved logic")
        return items
