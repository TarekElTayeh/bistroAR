#!/usr/bin/env python3
import io
from datetime import datetime
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def fill_invoice(template_path, output_path, invoice_data):
    """Fill a PDF invoice template with the provided data."""
    # 1) Create a PDF in memory with dynamic fields
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Example coordinates—adjust to match the template
    can.drawString(70, 730, invoice_data['client_name'])
    can.drawString(400, 730, invoice_data['period'])
    date_obj = datetime.strptime(invoice_data['date'], '%Y-%m-%d')
    can.drawString(70, 700, date_obj.strftime('%-m/%-d/%y'))
    can.drawString(400, 700, f"$ {invoice_data['amount']:.2f}")

    can.save()
    packet.seek(0)

    # 2) Read the template PDF and overlay
    template_pdf = PdfReader(template_path)
    overlay_pdf = PdfReader(packet)
    writer = PdfWriter()

    # 3) Merge the overlay onto the first page
    page = template_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    # 4) Write out the filled-in invoice
    with open(output_path, 'wb') as f:
        writer.write(f)


if __name__ == '__main__':
    # Example usage with dummy data
    invoice = {
        'client_name': 'Tarek El Tayeh',
        'period': 'May 1st to May 31st 2025',
        'date': '2025-05-01',
        'amount': 135.38,
    }
    fill_invoice('invoice.pdf', 'filled_invoice.pdf', invoice)
    print('Generated filled_invoice.pdf')
