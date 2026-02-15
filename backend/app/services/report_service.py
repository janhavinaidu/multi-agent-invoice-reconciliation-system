from fpdf import FPDF
import os
from datetime import datetime
from typing import Dict, Any

class ReportService:
    def __init__(self):
        pass

    def generate_pdf_report(self, result: Dict[str, Any], output_path: str):
        """Generate a professional PDF report from reconciliation result"""
        pdf = FPDF()
        pdf.add_page()
        
        # --- Header ---
        pdf.set_font("helvetica", "B", 24)
        pdf.set_text_color(33, 150, 243) # Blue
        pdf.cell(0, 15, "Invoice Reconciliation Report", ln=True, align="C")
        pdf.ln(5)
        
        # --- Info Section ---
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(100, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        pdf.cell(0, 10, f"Processing ID: {os.path.basename(output_path).split('.')[0]}", align="R", ln=True)
        pdf.ln(5)
        
        # --- Invoice Data ---
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "1. Invoice Summary", ln=True)
        pdf.set_font("helvetica", "", 12)
        
        extraction = result.get("extraction", {})
        pdf.cell(40, 10, "Invoice #:", border="B")
        pdf.cell(60, 10, str(extraction.get("invoice_number", "N/A")), border="B")
        pdf.cell(40, 10, "Supplier:", border="B")
        pdf.cell(0, 10, str(extraction.get("supplier", "N/A")), border="B", ln=True)
        
        pdf.cell(40, 10, "Date:", border="B")
        pdf.cell(60, 10, str(extraction.get("invoice_date", "N/A")), border="B")
        pdf.cell(40, 10, "PO Reference:", border="B")
        pdf.cell(0, 10, str(extraction.get("po_reference", "N/A")), border="B", ln=True)
        
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(40, 10, "Total Amount:", border="B")
        pdf.set_text_color(255, 0, 0)
        pdf.cell(60, 10, f"${extraction.get('total_amount', 0):,.2f}", border="B")
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 10, "Currency:", border="B")
        pdf.cell(0, 10, str(extraction.get("currency", "USD")), border="B", ln=True)
        pdf.ln(10)
        
        # --- Matching Results ---
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "2. Matching Results", ln=True)
        
        matching = result.get("matching", {})
        pdf.set_font("helvetica", "", 12)
        pdf.cell(50, 10, "Matched PO:")
        pdf.cell(0, 10, str(matching.get("matched_po_id", "None")), ln=True)
        pdf.cell(50, 10, "Match Type:")
        pdf.cell(0, 10, str(matching.get("match_type", "None")).capitalize(), ln=True)
        pdf.cell(50, 10, "Match Confidence:")
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, f"{matching.get('confidence_score', 0)*100:.0f}%", ln=True)
        pdf.ln(5)
        
        # --- Discrepancies ---
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "3. Detected Discrepancies", ln=True)
        
        discrepancies = result.get("discrepancies", [])
        if not discrepancies:
            pdf.set_font("helvetica", "I", 12)
            pdf.set_text_color(76, 175, 80) # Green
            pdf.cell(0, 10, "No discrepancies found. Invoice matches PO within tolerance.", ln=True)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_font("helvetica", "B", 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(40, 10, "Type", border=1, fill=True)
            pdf.cell(25, 10, "Severity", border=1, fill=True)
            pdf.cell(15, 10, "Conf.", border=1, fill=True)
            pdf.cell(110, 10, "Details", border=1, fill=True, ln=True)
            
            pdf.set_font("helvetica", "", 9)
            for d in discrepancies:
                pdf.cell(40, 8, str(d.get("type", "")), border=1)
                
                severity = str(d.get("severity", "info"))
                if severity == "critical":
                    pdf.set_text_color(255, 0, 0)
                elif severity == "warning":
                    pdf.set_text_color(255, 152, 0)
                pdf.cell(25, 8, severity.upper(), border=1)
                pdf.set_text_color(0, 0, 0)
                
                pdf.cell(15, 8, f"{d.get('confidence', 0)*100:.0f}%", border=1)
                pdf.cell(110, 8, str(d.get("details", "")), border=1, ln=True)
        pdf.ln(10)
        
        # --- Final Recommendation ---
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "4. AI Resolution Recommendation", ln=True)
        
        res = result.get("resolution", {})
        action = str(res.get("action", "")).replace("_", " ").upper()
        
        pdf.set_font("helvetica", "B", 14)
        if "APPROVE" in action:
            pdf.set_text_color(76, 175, 80)
        elif "ESCALATE" in action or "UNAPPROVED" in action:
            pdf.set_text_color(255, 0, 0)
        else:
            pdf.set_text_color(255, 152, 0)
            
        pdf.cell(0, 12, f"Final Decision: {action}", border=1, ln=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        if res.get("summary"):
            pdf.set_font("helvetica", "B", 11)
            pdf.set_fill_color(230, 242, 255)
            pdf.cell(0, 8, "Decision Summary:", fill=True, ln=True)
            pdf.set_font("helvetica", "", 11)
            pdf.multi_cell(0, 8, str(res.get("summary")), border=1)
            pdf.ln(5)
        
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "Suggested Next Steps:", ln=True)
        pdf.set_font("helvetica", "", 11)
        for i, step in enumerate(res.get("suggested_steps", [])):
            pdf.cell(10, 8, f"{i+1}.")
            pdf.cell(0, 8, str(step), ln=True)
        
        # --- Footer ---
        pdf.set_y(-20)
        pdf.set_font("helvetica", "I", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "Antigravity AI Invoice Reconciliation System - Confidential Report", align="C")
        
        pdf.output(output_path)
        return output_path

_report_service = None

def get_report_service():
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service
