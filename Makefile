PYTHON ?= python3
.RECIPEPREFIX := >

# Default file locations (override when invoking, e.g. `make parse-pdf PDF=foo.pdf`)
PDF ?=
CSV ?=transactions.csv
JSON ?=transactions.json
TXT ?=
EXCEL ?=output.xlsx
TEMPLATE ?=invoice.pdf
OUTPUT ?=filled_invoice.pdf
DB ?=database/bistro54_clients.db
OUTDIR ?=.
.PHONY: help parse-pdf parse-txt invoices batch-invoices clean

help:
> @echo "Available targets:"
> @echo "  parse-pdf   PDF=path/to/file [CSV=out.csv JSON=out.json]"
> @echo "  parse-txt   TXT=path/to/file [CSV=out.csv JSON=out.json EXCEL=out.xlsx]"
> @echo "  invoices    TEMPLATE=invoice.pdf OUTPUT=filled_invoice.pdf"
> @echo "  batch-invoices JSON=transactions.json TEMPLATE=invoice.pdf [DB=database/bistro54_clients.db OUTDIR=. ]"
> @echo "  clean       Remove generated CSV/JSON/Excel/PDF files"

parse-pdf:
> $(PYTHON) parse_transactions.py $(PDF) --csv $(CSV) --json $(JSON)

parse-txt:
> $(PYTHON) txt_journal_parser.py $(TXT) --csv $(CSV) --json $(JSON) --excel $(EXCEL)

invoices:
> $(PYTHON) generateInvoice.py $(TEMPLATE) $(OUTPUT)
batch-invoices:
> $(PYTHON) generate_invoices.py $(JSON) $(TEMPLATE) --db $(DB) --out-dir $(OUTDIR)
clean:
> $(PYTHON) cleanup_outputs.py --csv $(wildcard *.csv) \
>     --json $(wildcard *.json) --excel $(wildcard *.xlsx) \
>     --pdf $(wildcard filled_invoice*.pdf)
