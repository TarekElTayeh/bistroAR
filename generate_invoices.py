#!/usr/bin/env python3
"""
generate_invoices.py

Generate invoice PDFs for all clients with visits in the given period. The
script reads visits and visit items from the SQLite database, aggregates
them by client, and produces one invoice per client. It uses the
generate_invoice.py module to overlay data onto the invoice template.

Usage:
    python3 generate_invoices.py --db bistro54.db --period 2025-07 \
        --template invoice.pdf --out out/invoices

Invoices are saved in the specified output directory. Each invoice file
is named <client_code>_<period>.pdf. A record is inserted into the
invoices and invoice_items tables for each invoice.
"""

import argparse
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from generate_invoice import fill_invoice


def aggregate_client_visits(conn: sqlite3.Connection, period: str) -> Dict[str, List[Dict[str, str]]]:
    """Return a mapping of client_code to list of visits for the period."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT v.id, v.client_code, v.date, v.time, v.reference, v.total
        FROM visits v
        WHERE v.date LIKE ?
        ORDER BY v.client_code, v.date, v.time
        """,
        (f"{period}-%",),
    )
    visits_by_client: Dict[str, List[Dict[str, str]]] = {}
    for visit_id, client_code, date, time, reference, total in cur.fetchall():
        visits_by_client.setdefault(client_code, []).append({
            'visit_id': visit_id,
            'date': date,
            'time': time,
            'reference': reference,
            'total': total,
        })
    return visits_by_client


def get_client_info(conn: sqlite3.Connection, client_code: str) -> Dict[str, str]:
    """Return a dictionary of client information."""
    cur = conn.cursor()
    cur.execute("SELECT name FROM clients WHERE code = ?", (client_code,))
    row = cur.fetchone()
    return {'name': row[0] if row else client_code}


def generate_invoices(db_path: str, period: str, template_path: str, output_dir: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        visits_by_client = aggregate_client_visits(conn, period)
        os.makedirs(output_dir, exist_ok=True)
        now = datetime.utcnow().isoformat(timespec='seconds')
        for client_code, visits in visits_by_client.items():
            client = get_client_info(conn, client_code)
            # Compute totals
            subtotal = sum(v['total'] for v in visits)
            tax_tps = 0.0
            tax_tvq = 0.0
            total = subtotal
            invoice_id = f"{client_code}_{period}"
            period_start = f"{period}-01"
            period_end = f"{period}-31"
            # Insert invoice record
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO invoices (
                        id, client_code, period_start, period_end,
                        subtotal, tax_tps, tax_tvq, total, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        invoice_id, client_code, period_start, period_end,
                        subtotal, tax_tps, tax_tvq, total, now,
                    ),
                )
                # Insert invoice_items linking visits to invoice
                for v in visits:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO invoice_items (
                            invoice_id, visit_id, description, amount
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (invoice_id, v['visit_id'], f"Reference {v['reference']} on {v['date']} {v['time']}", v['total']),
                    )
            # Generate invoice PDF
            invoice_data = {
                'client_name': client['name'],
                'period': period,
                'date': period_start,
                'amount': total,
            }
            output_path = Path(output_dir) / f"{client_code}_{period}.pdf"
            fill_invoice(template_path, str(output_path), invoice_data)
            print(f"Generated invoice for {client_code} at {output_path}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate invoices for each client with visits in the given period.'
    )
    parser.add_argument('--db', required=True, help='Path to SQLite database')
    parser.add_argument('--period', required=True, help='Period string (YYYY-MM)')
    parser.add_argument('--template', default='invoice.pdf', help='Path to blank invoice template')
    parser.add_argument('--out', required=True, help='Output directory for invoices')
    args = parser.parse_args()
    generate_invoices(args.db, args.period, args.template, args.out)


if __name__ == '__main__':
    main()