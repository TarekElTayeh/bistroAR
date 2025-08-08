#!/usr/bin/env python3
"""
deliver_invoices.py

Deliver generated invoices via email and/or store them in an external
location. Currently this script creates a manifest CSV containing the
client code, invoice file path and status. If SMTP credentials are
provided via environment variables, the script will attempt to send
each invoice as an email attachment. Otherwise it skips sending and
records a status of SKIPPED.

Environment variables (optional):
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SENDER

Usage:
    python3 deliver_invoices.py --db bistro54.db --period 2025-07 --indir out/invoices
"""

import argparse
import csv
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
import sqlite3
from typing import List


def get_invoices(db_path: str, period: str) -> List[dict]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, client_code FROM invoices
        WHERE period_start LIKE ?
        """,
        (f"{period}-%",),
    )
    invoices = [{'invoice_id': row[0], 'client_code': row[1]} for row in cur.fetchall()]
    conn.close()
    return invoices


def get_client_email(db_path: str, client_code: str) -> str:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT email FROM clients WHERE code = ?", (client_code,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return row[0]
    return ''


def send_email(recipient: str, subject: str, body: str, attachment_path: Path) -> bool:
    host = os.environ.get('SMTP_HOST')
    port = os.environ.get('SMTP_PORT')
    user = os.environ.get('SMTP_USER')
    password = os.environ.get('SMTP_PASS')
    sender = os.environ.get('SENDER')
    if not (host and port and user and password and sender):
        return False
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    msg.set_content(body)
    with open(attachment_path, 'rb') as f:
        data = f.read()
    msg.add_attachment(data, maintype='application', subtype='pdf', filename=attachment_path.name)
    try:
        with smtplib.SMTP(host, int(port)) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email to {recipient}: {e}")
        return False


def deliver_invoices(db_path: str, period: str, indir: str, manifest_path: str) -> None:
    invoices = get_invoices(db_path, period)
    rows = []
    for inv in invoices:
        client_code = inv['client_code']
        invoice_file = Path(indir) / f"{client_code}_{period}.pdf"
        email = get_client_email(db_path, client_code)
        status = 'SKIPPED'
        if email:
            subject = f"Bistro54 Invoice for {period}"
            body = f"Dear {client_code},\n\nPlease find your invoice for {period} attached.\n\nRegards,\nBistro54"
            success = send_email(email, subject, body, invoice_file)
            status = 'SENT' if success else 'FAILED'
        rows.append({'client_code': client_code, 'invoice_file': str(invoice_file), 'email': email, 'status': status})
        print(f"Delivery status for {client_code}: {status}")
    # Write manifest CSV
    with open(manifest_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['client_code', 'invoice_file', 'email', 'status'])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Manifest written to {manifest_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Send or record invoices for a given period.'
    )
    parser.add_argument('--db', required=True, help='Path to SQLite database')
    parser.add_argument('--period', required=True, help='Period string (YYYY-MM)')
    parser.add_argument('--indir', required=True, help='Directory containing invoice PDFs')
    parser.add_argument('--manifest', default='manifest.csv', help='Path to output manifest CSV')
    args = parser.parse_args()
    deliver_invoices(args.db, args.period, args.indir, args.manifest)


if __name__ == '__main__':
    main()