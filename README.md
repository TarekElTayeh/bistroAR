# Bistro54 AR Automation

Automation toolkit to parse Veloce journal dumps and transaction PDFs, generate invoice PDFs, and manage outputs.

## Overview
This project provides scripts to:

- **Parse** Veloce TXT journal dumps for account `1105` transactions (daily or multi-day).  
- **Extract** detailed client transactions from a multi-page PDF (with item descriptions and prices).  
- **Export** parsed results as CSV, JSON, and Excel.  
- **Generate** filled invoice PDFs by merging data onto a PDF template.  
- **Cleanup** generated output files.  
- **Manage** outputs via a Makefile.

## Prerequisites

- Python 3.8+  
- Virtual environment (recommended)  
- Libraries:
  - `pandas` & `openpyxl` (for Excel export)  
  - `PyPDF2` (or `pypdf`) & `reportlab` (for PDF templating)  
  - **`pdfplumber`** (for PDF transaction extraction)  
- `make` (for Makefile targets)

## Installation

1. **Clone the repo:**
    ```bash
    git clone https://github.com/your-org/bistro54-ar-automation.git
    cd bistro54-ar-automation
    ```
2. **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3. **Install requirements:**
    ```bash
    pip install pandas openpyxl PyPDF2 reportlab pdfplumber
    ```
4. **Ensure `make` is available:**
    ```bash
    sudo apt update && sudo apt install make
    ```

## Project Structure

├── Makefile
├── README.md
├── txt_journal_parser.py # Parses TXT dumps to CSV/JSON/Excel
├── parse_transactions.py # Extracts detailed transactions from PDF
├── generateInvoice.py # Fills PDF invoice template with data
├── cleanup_outputs.py # Deletes generated CSV/JSON/Excel/PDF files
├── invoice.pdf # Blank invoice template
└── venv/ # Python virtual environment


## Usage

### 1. Extract Detailed Transactions from PDF

```bash
python3 parse_transactions.py path/to/DOC080725-001.pdf \
  --csv transactions.csv --json transactions.json

    --csv: Path to output CSV file (default: transactions.csv).

    --json: Path to output JSON file (default: transactions.json).

This produces one row per item with columns:
client_code, date (YYYY-MM-DD), time (HH:MM), reference, employee, description, price.
2. Parse Journal Entries (TXT)

python3 txt_journal_parser.py path/to/journal.txt \
  --csv ar.csv --json ar.json --excel ar.xlsx

    --csv: Path to output CSV file (default: output.csv).

    --json: Path to output JSON file (default: output.json).

    --excel: Path to output Excel file (default: output.xlsx).

3. Generate Invoices

python3 generateInvoice.py invoice.pdf filled_invoice.pdf

    invoice.pdf: Path to your blank template.

    filled_invoice.pdf: Destination for the populated invoice.

Customize generateInvoice.py to loop over parsed data and produce one PDF per customer or per day.
4. Cleanup Outputs

python3 cleanup_outputs.py --csv ar.csv --json ar.json --excel ar.xlsx

Removes specified output files if they exist.
5. Makefile Targets

make           # Show help
make clean     # Remove all *.csv, *.json, *.xlsx, *.pdf outputs

Next Steps

    Group extracted transactions by client_code and pass to the invoice generator so each customer’s visits appear as separate line-items.

    Swap in API calls once Veloce API credentials are available to replace PDF/TXT parsing.

    Add error handling, logging, and automated scheduling (cron, cloud scheduler, etc.).