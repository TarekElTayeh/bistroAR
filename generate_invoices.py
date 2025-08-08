#!/usr/bin/env python3
"""Generate invoices for each client from transaction JSON."""

import argparse
import json
import os
import sqlite3
from collections import defaultdict
from datetime import date

from generateInvoice import fill_invoice


def load_client_names(db_path: str) -> dict:
    """Return a mapping of client_code -> client_name from the SQLite DB."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        'SELECT "Unnamed: 1" AS code, "Unnamed: 2" AS name '\
        'FROM clients WHERE "Unnamed: 1" != "" AND "Unnamed: 1" != "Code"'
    )
    mapping = {code: name for code, name in cur.fetchall()}
    conn.close()
    return mapping


def group_transactions(json_path: str) -> dict:
    """Group transaction records by client_code."""
    with open(json_path, 'r', encoding='utf-8') as f:
        records = json.load(f)
    groups = defaultdict(list)
    for rec in records:
        groups[rec['client_code']].append(rec)
    return groups


def build_invoice_data(client_name: str, records: list) -> dict:
    amounts = [r['price'] for r in records]
    dates = [r['date'] for r in records]
    period = f"{min(dates)} to {max(dates)}" if dates else ""
    return {
        'client_name': client_name,
        'period': period,
        'date': date.today().isoformat(),
        'amount': sum(amounts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate one invoice PDF per client based on transaction JSON.'
    )
    parser.add_argument('json_file', help='Path to transactions.json produced by parse_transactions')
    parser.add_argument('template', help='Invoice PDF template path')
    parser.add_argument('--db', default='database/bistro54_clients.db', help='SQLite database of clients')
    parser.add_argument('--out-dir', default='.', help='Directory to store generated invoices')
    args = parser.parse_args()

    client_names = load_client_names(args.db)
    grouped = group_transactions(args.json_file)
    os.makedirs(args.out_dir, exist_ok=True)

    for code, records in grouped.items():
        name = client_names.get(code, f'Client {code}')
        invoice_data = build_invoice_data(name, records)
        output_path = os.path.join(args.out_dir, f'filled_invoice_{code}.pdf')
        fill_invoice(args.template, output_path, invoice_data)
        print(f'Generated {output_path}')


if __name__ == '__main__':
    main()
