#!/usr/bin/env python3
"""
generate_invoice.py

Simple script to generate filled invoices from a PDF template.
It overlays invoice data onto a blank invoice template using
pypdf (PyPDF2) for reading/writing PDFs and reportlab for
drawing text.

Usage:
    python3 generate_invoice.py template.pdf output.pdf --client_name 'Acme Inc.' --period 'July 2025' --date 2025-07-01 --amount 123.45

This script is intentionally kept simple. In the wider automation
pipeline, generate_invoices.py will call this module repeatedly to
produce one invoice per client for a given period.

Requirements:
    - reportlab
    - pypdf (PyPDF2 also works)
"""

import argparse
import io
from datetime import datetime
from typing import Dict

try:
    from pypdf import PdfReader, PdfWriter  # use pypdf if available
except ImportError:
    from PyPDF2 import PdfReader, PdfWriter  # fallback to PyPDF2

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def fill_invoice(template_path: str, output_path: str, invoice_data: Dict[str, str]) -> None:
    """Fill the invoice template and write to output_path."""
    # Create an in-memory PDF for overlay
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Coordinates need to be adjusted to match your template
    # These values are examples only and may need tweaking
    can.drawString(70, 720, invoice_data.get('client_name', ''))
    can.drawString(400, 720, invoice_data.get('period', ''))

    # Format date for invoice
    try:
        date_obj = datetime.strptime(invoice_data['date'], '%Y-%m-%d')
        date_str = date_obj.strftime('%m/%d/%y')
    except Exception:
        date_str = invoice_data.get('date', '')
    can.drawString(70, 695, date_str)
    can.drawString(400, 695, f"$ {invoice_data.get('amount', 0):.2f}")

    can.save()
    packet.seek(0)

    # Read original template and overlay
    template_pdf = PdfReader(template_path)
    overlay_pdf = PdfReader(packet)
    writer = PdfWriter()
    page = template_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    # Write out the filled invoice
    with open(output_path, 'wb') as f:
        writer.write(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Overlay invoice data onto a PDF template.'
    )
    parser.add_argument('template', help='Path to the blank invoice template PDF')
    parser.add_argument('output', help='Path to write the filled invoice PDF')
    parser.add_argument('--client_name', required=True, help='Client name to display on invoice')
    parser.add_argument('--period', required=True, help='Billing period (e.g., "July 2025")')
    parser.add_argument('--date', required=True, help='Invoice date in YYYY-MM-DD format')
    parser.add_argument('--amount', type=float, required=True, help='Invoice total amount')
    args = parser.parse_args()

    invoice = {
        'client_name': args.client_name,
        'period': args.period,
        'date': args.date,
        'amount': args.amount,
    }

    fill_invoice(args.template, args.output, invoice)
    print(f"Generated invoice at {args.output}")


if __name__ == '__main__':
    main()