# Quick Setup Guide

## Prerequisites Check

```bash
# Check Python version (need 3.9+)
python --version

# Check pip
pip --version

# Check Tesseract OCR
tesseract --version
```

If Tesseract is not installed:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

## Installation Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd invoice-reconciliation-system
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

This will install:
- LangGraph and LangChain
- Document processing libraries (pdfplumber, pytesseract)
- Image processing (OpenCV, Pillow)
- ML libraries (sentence-transformers, torch)
- All other dependencies

### 4. Set Up API Key

You need a **FREE Groq API key** (recommended):

```bash
# Get your FREE API key at: https://console.groq.com/keys
# Sign up (free, no credit card needed)
# Create an API key
# Set it:

export GROQ_API_KEY="gsk_..."

# Or create a .env file:
echo "GROQ_API_KEY=gsk_..." > .env
```

**Why Groq?**
- ✅ Completely FREE (no credit card required)
- ✅ Lightning fast inference (faster than OpenAI)
- ✅ Generous rate limits (plenty for this project)
- ✅ Powerful models (Llama 3.3 70B performs excellently)

**Alternative (if you prefer paid APIs):**
```bash
# OpenAI (paid)
export OPENAI_API_KEY="sk-..."

# Anthropic (paid)
export ANTHROPIC_API_KEY="sk-ant-..."

# Then update config.yaml to use openai/anthropic provider
```

### 5. Prepare Test Data

Create directory structure:
```bash
mkdir -p data/invoices
mkdir -p outputs
mkdir -p logs
```

Place your test invoice PDFs in `data/invoices/`:
- invoice_1.pdf (baseline)
- invoice_2.pdf (scanned)
- invoice_3.pdf (different format)
- invoice_4.pdf (price discrepancy)
- invoice_5.pdf (missing PO)

### 6. Verify Setup

Test with a single invoice:
```bash
python main.py --invoice data/invoices/invoice_1.pdf --debug
```

If successful, you'll see:
- Agent execution logs
- Processing completed message
- Output saved to `outputs/` directory

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'langchain_groq'"
**Solution**: Make sure you activated the virtual environment and ran `pip install -r requirements.txt`

### Issue: "pytesseract.pytesseract.TesseractNotFoundError"
**Solution**: Install Tesseract OCR system package (see Prerequisites)

### Issue: "groq.AuthenticationError" or "GROQ_API_KEY not found"
**Solution**: Get your FREE API key and set it:
```bash
# 1. Visit https://console.groq.com/keys
# 2. Sign up (free, no credit card)
# 3. Create an API key
# 4. Set it:
export GROQ_API_KEY="gsk_your-key-here"

# Verify it's set
echo $GROQ_API_KEY
```

### Issue: Processing is very slow
**Solution**: 
- Groq is already extremely fast (fastest available)
- If still slow, switch to lighter model in config.yaml:
  - Change `model: "llama-3.3-70b-versatile"` to `model: "gemma2-9b-it"`
- Check if using CPU-only torch
- Consider using smaller embedding model in config.yaml
- Disable semantic similarity if not needed

### Issue: Out of memory errors
**Solution**:
- Groq runs on their servers, so no local memory issues for LLM
- For local embedding model memory issues:
  - Reduce `max_concurrent_invoices` in config.yaml
  - Process invoices one at a time: `python main.py --invoice <file>`
  - Use smaller embedding model (already using MiniLM-L6-v2, one of the smallest)

## Running the System

### Process Single Invoice
```bash
python main.py --invoice data/invoices/invoice_1.pdf
```

### Process All Invoices
```bash
python main.py --invoice-dir data/invoices --report
```

### Enable Debug Mode
```bash
python main.py --debug
```

### Custom Configuration
```bash
python main.py --config custom_config.yaml
```

## Verifying Output

Check `outputs/` directory for:
- Individual invoice results: `invoice_1_result.json`
- Summary report: `summary_report.json`
- Logs in `logs/` directory

Open a result file to see:
- Extraction results with confidence scores
- Matching results and reasoning
- Discrepancies detected
- Recommended actions
- Complete agent reasoning chain

## Next Steps

1. Review the generated output JSON files
2. Check confidence scores and reasoning
3. Test with your own invoice files
4. Adjust configuration in `config.yaml` as needed
5. Create demo video following `DEMO_SCRIPT.md`

## Getting Help

- Check README.md for detailed documentation
- Review ANALYSIS.md for technical insights
- See examples/expected_output_format.json for output structure
- Enable --debug flag for detailed logs

If issues persist, check:
- Python version (3.9+)
- All dependencies installed
- API key is valid and has credits
- Tesseract is properly installed
- Input files are readable PDFs or images