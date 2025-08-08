#!/usr/bin/env python3
"""
etl_load.py

Load transaction records from CSV into the visits and visit_items tables of
the Bistro54 automation database. This script reads the CSV output from
parse_transactions.py and groups rows into visits based on client_code,
date, time and reference number. It aggregates totals and inserts
individual line items into visit_items.

Usage:
    python3 etl_load.py --db bistro54.db --txns transactions.csv --period 2025-07

The period parameter is stored on each visit to facilitate filtering by
month when generating invoices.
"""

import argparse
import csv
import sqlite3
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def load_transactions(db_path: str, csv_path: str, period: str) -> None:
    # Read all transaction rows
    rows: List[Dict[str, str]] = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    # Group by visit key: (client_code, date, time, reference)
    visits: Dict[Tuple[str, str, str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (row['client_code'], row['date'], row['time'], row['reference'])
        visits[key].append(row)

    conn = sqlite3.connect(db_path)
    try:
        with conn:
            for (client_code, date, time, reference), items in visits.items():
                # Generate unique ID for visit
                visit_id = str(uuid.uuid4())
                # Compute totals
                total = sum(float(item['price']) for item in items)
                # Insert into visits table. For now taxes, tip and discount are 0.
                conn.execute(
                    """
                    INSERT INTO visits (
                        id, client_code, date, time, reference, employee,
                        subtotal, tax_tps, tax_tvq, tip, discount, total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        visit_id,
                        client_code,
                        date,
                        time,
                        reference,
                        items[0].get('employee', ''),
                        total,  # subtotal
                        0.0,    # tax_tps
                        0.0,    # tax_tvq
                        0.0,    # tip
                        0.0,    # discount
                        total,
                    ),
                )
                # Insert each item
                for item in items:
                    conn.execute(
                        """
                        INSERT INTO visit_items (
                            visit_id, description, price
                        ) VALUES (?, ?, ?)
                        """,
                        (visit_id, item['description'], float(item['price'])),
                    )
    finally:
        conn.close()
    print(f"Loaded {len(visits)} visits and {len(rows)} items into {db_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Load transaction CSV into the database.'
    )
    parser.add_argument('--db', required=True, help='Path to SQLite database file')
    parser.add_argument('--txns', required=True, help='Path to CSV file of transactions')
    parser.add_argument('--period', required=True, help='Period string (e.g., 2025-07) stored for invoice grouping')
    args = parser.parse_args()
    load_transactions(args.db, args.txns, args.period)


if __name__ == '__main__':
    main()