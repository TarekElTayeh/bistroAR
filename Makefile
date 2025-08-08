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

.PHONY: help parse-pdf parse-txt invoices clean

help:
> @echo "Available targets:"
> @echo "  parse-pdf   PDF=path/to/file [CSV=out.csv JSON=out.json]"
> @echo "  parse-txt   TXT=path/to/file [CSV=out.csv JSON=out.json EXCEL=out.xlsx]"
> @echo "  invoices    TEMPLATE=invoice.pdf OUTPUT=filled_invoice.pdf"
> @echo "  clean       Remove generated CSV/JSON/Excel/PDF files"

parse-pdf:
> $(PYTHON) parse_transactions.py $(PDF) --csv $(CSV) --json $(JSON)

parse-txt:
> $(PYTHON) txt_journal_parser.py $(TXT) --csv $(CSV) --json $(JSON) --excel $(EXCEL)

invoices:
> $(PYTHON) generateInvoice.py $(TEMPLATE) $(OUTPUT)

clean:
> $(PYTHON) cleanup_outputs.py --csv $(wildcard *.csv) \
>     --json $(wildcard *.json) --excel $(wildcard *.xlsx) \
>     --pdf $(wildcard filled_invoice*.pdf)
