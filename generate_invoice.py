#!/usr/bin/env python3
"""Utilities for rendering invoice PDFs.

This module builds an invoice layout directly with ReportLab so the project
does not rely on an external PDF template.  The invoice contains a simple
header, table grid and a summary row.

Example
-------

```
from generate_invoice import build_invoice

invoice_data = {
    "client_name": "Acme Inc.",
    "period": "July 1st to July 31st 2025",
    "transactions": [
        {"date": "2025-07-01", "time": "09:00", "type": "Visit", "reference": "A1", "amount": 10.0},
    ],
    "total": 10.0,
}
build_invoice("invoice.pdf", invoice_data)
```

The function above is used by ``generate_invoices.py`` to create one invoice
per client for a given period.
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def build_invoice(output_path: str, invoice_data: Dict[str, Any]) -> None:
    """Render ``invoice_data`` into ``output_path`` using ReportLab.

    Parameters
    ----------
    output_path:
        Destination PDF file.
    invoice_data:
        Mapping containing ``client_name`` (str), ``period`` (str),
        ``transactions`` (list of dicts) and ``total`` (float).
    """

    can = canvas.Canvas(output_path, pagesize=letter)

    # Header
    can.setFont("Helvetica-Bold", 14)
    can.drawString(40, 750, "Client Statement")
    can.setFont("Helvetica", 12)
    can.drawString(40, 735, invoice_data.get("client_name", ""))
    can.drawString(40, 720, invoice_data.get("period", ""))

    # Table grid bounds
    left, right = 40, 560
    top, bottom = 680, 150
    can.rect(left, bottom, right - left, top - bottom)

    # Column lines (date, time, type, reference, amount)
    columns = [40, 100, 160, 350, 450, 560]
    for x in columns:
        can.line(x, top, x, bottom)

    # Horizontal lines for rows (including header row)
    line_height = 18
    num_rows = 20
    for i in range(num_rows + 1):
        y = top - i * line_height
        can.line(left, y, right, y)

    # Column headers
    headers = ["Date", "Time", "Transaction", "Reference", "Amount"]
    header_y = top - 14
    for x, text in zip(columns[:-1], headers):
        can.drawString(x + 2, header_y, text)

    # Transaction rows
    start_y = top - line_height * 2  # first line after headers
    transactions = invoice_data.get("transactions", [])[:num_rows - 1]
    for i, txn in enumerate(transactions):
        y = start_y - i * line_height
        can.drawString(columns[0] + 2, y, txn.get("date", ""))
        can.drawString(columns[1] + 2, y, txn.get("time", ""))
        can.drawString(columns[2] + 2, y, txn.get("type", ""))
        can.drawString(columns[3] + 2, y, txn.get("reference", ""))
        can.drawRightString(columns[5] - 2, y, f"{txn.get('amount', 0):.2f}")

    # Total row just below the table
    can.setFont("Helvetica-Bold", 12)
    can.drawString(columns[3] + 2, bottom - 20, "Total $")
    can.drawRightString(columns[5] - 2, bottom - 20, f"{invoice_data.get('total', 0):.2f}")

    can.save()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a single invoice PDF.")
    parser.add_argument("output", help="Path to write the invoice PDF")
    parser.add_argument("--client_name", required=True, help="Client name to display")
    parser.add_argument("--period", required=True, help="Billing period string")
    parser.add_argument("--total", type=float, required=True, help="Invoice total amount")
    parser.add_argument(
        "--transaction",
        action="append",
        default=[],
        help="Transaction as date,time,type,reference,amount; may be repeated",
    )
    args = parser.parse_args()

    transactions: List[Dict[str, Any]] = []
    for t in args.transaction:
        date, time, ttype, reference, amount = t.split(",")
        transactions.append(
            {
                "date": date,
                "time": time,
                "type": ttype,
                "reference": reference,
                "amount": float(amount),
            }
        )

    invoice = {
        "client_name": args.client_name,
        "period": args.period,
        "transactions": transactions,
        "total": args.total,
    }

    build_invoice(args.output, invoice)
    print(f"Generated invoice at {args.output}")


if __name__ == "__main__":
    main()

