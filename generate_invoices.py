#!/usr/bin/env python3
"""
generate_invoices.py

Generate invoice PDFs for all clients with visits in the given period. The
script reads visits and visit items from the SQLite database, aggregates
them by client, and produces one invoice per client using the
``generate_invoice`` module to draw the PDF layout programmatically.

Usage:
    python3 generate_invoices.py --db bistro54.db --period 2025-07 --out out/invoices

Invoices are saved in the specified output directory. Each invoice file
is named <client_code>_<period>.pdf. A record is inserted into the
invoices and invoice_items tables for each invoice.
"""

import argparse
import os
import sqlite3
import calendar
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from generate_invoice import build_invoice


def ordinal(n: int) -> str:
    """Return an ordinal string for n (1 -> '1st')."""
    if 11 <= n % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def period_bounds(period: str) -> Dict[str, str]:
    """Return start/end dates and display string for the period."""
    year, month = map(int, period.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    start = datetime(year, month, 1)
    end = datetime(year, month, last_day)
    display = f"{start.strftime('%B')} {ordinal(start.day)} to {end.strftime('%B')} {ordinal(end.day)} {end.year}"
    return {
        "start": start.strftime("%Y-%m-%d"),
        "end": end.strftime("%Y-%m-%d"),
        "display": display,
    }


def fetch_transactions_by_client(
    conn: sqlite3.Connection, period_start: str, period_end: str
) -> Dict[str, List[Dict[str, Any]]]:
    """Return mapping of client_code to list of transaction rows."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT v.client_code, v.id, v.date, v.time, v.reference, vi.description, vi.price
        FROM visits v
        JOIN visit_items vi ON vi.visit_id = v.id
        WHERE v.date BETWEEN ? AND ?
        ORDER BY v.client_code, v.date, v.time, vi.id
        """,
        (period_start, period_end),
    )
    txns_by_client: Dict[str, List[Dict[str, Any]]] = {}
    for client_code, visit_id, date, time, reference, description, price in cur.fetchall():
        txns_by_client.setdefault(client_code, []).append(
            {
                "visit_id": visit_id,
                "date": date,
                "time": time,
                "reference": reference,
                "type": description,
                "amount": price,
            }
        )
    return txns_by_client


def get_client_info(conn: sqlite3.Connection, client_code: str) -> Dict[str, str]:
    """Return a dictionary of client information."""
    cur = conn.cursor()
    cur.execute("SELECT name FROM clients WHERE code = ?", (client_code,))
    row = cur.fetchone()
    return {"name": row[0] if row else client_code}


def generate_invoices(db_path: str, period: str, output_dir: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        bounds = period_bounds(period)
        txns_by_client = fetch_transactions_by_client(conn, bounds["start"], bounds["end"])
        os.makedirs(output_dir, exist_ok=True)
        now = datetime.utcnow().isoformat(timespec="seconds")
        for client_code, transactions in txns_by_client.items():
            client = get_client_info(conn, client_code)
            total = sum(t["amount"] for t in transactions)
            invoice_id = f"{client_code}_{period}"
            # Insert invoice and items
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO invoices (
                        id, client_code, period_start, period_end,
                        subtotal, tax_tps, tax_tvq, total, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        invoice_id,
                        client_code,
                        bounds["start"],
                        bounds["end"],
                        total,
                        0.0,
                        0.0,
                        total,
                        now,
                    ),
                )
                for t in transactions:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO invoice_items (
                            invoice_id, visit_id, description, amount
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (
                            invoice_id,
                            t["visit_id"],
                            t["type"],
                            t["amount"],
                        ),
                    )
            # Generate invoice PDF
            invoice_data = {
                "client_name": client["name"],
                "period": bounds["display"],
                "transactions": transactions,
                "total": total,
            }
            output_path = Path(output_dir) / f"{client_code}_{period}.pdf"
            build_invoice(str(output_path), invoice_data)
            print(f"Generated invoice for {client_code} at {output_path}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate invoices for each client with visits in the given period.'
    )
    parser.add_argument('--db', required=True, help='Path to SQLite database')
    parser.add_argument('--period', required=True, help='Period string (YYYY-MM)')
    parser.add_argument('--out', required=True, help='Output directory for invoices')
    args = parser.parse_args()
    generate_invoices(args.db, args.period, args.out)


if __name__ == '__main__':
    main()
