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
├── generateInvoice.py      # Fills a single PDF invoice template with data
├── generate_invoices.py    # Batch-generate invoices from transaction JSON
├── cleanup_outputs.py      # Deletes generated CSV/JSON/Excel/PDF files
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
### 2. Parse Journal Entries (TXT)

```bash
python3 txt_journal_parser.py path/to/journal.txt \
  --csv ar.csv --json ar.json --excel ar.xlsx
```

* `--csv`: Path to output CSV file (default: output.csv).
* `--json`: Path to output JSON file (default: output.json).
* `--excel`: Path to output Excel file (default: output.xlsx).

### 3. Generate a Single Invoice

```bash
python3 generateInvoice.py invoice.pdf filled_invoice.pdf
```

* `invoice.pdf`: Path to your blank template.
* `filled_invoice.pdf`: Destination for the populated invoice.

### 4. Generate Invoices for Each Client

```bash
python3 generate_invoices.py transactions.json invoice.pdf \
  --db database/bistro54_clients.db --out-dir invoices
```

Reads `transactions.json`, groups records by `client_code`, looks up client names from the SQLite database, and writes one `filled_invoice_<code>.pdf` per client in the `invoices/` directory.

### 5. Cleanup Outputs

```bash
python3 cleanup_outputs.py --csv ar.csv --json ar.json --excel ar.xlsx
```

Removes specified output files if they exist.

### 6. Makefile Targets

```
make           # Show help
make clean     # Remove all *.csv, *.json, *.xlsx, *.pdf outputs
```

## Next Steps

* Replace PDF/TXT parsing with Veloce API calls when credentials are available.
* Add error handling, logging, and automated scheduling (cron, cloud scheduler, etc.).
