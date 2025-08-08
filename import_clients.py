#!/usr/bin/env python3
"""
import_clients.py

Import client data from an Excel or CSV file into the clients table of
the Bistro54 automation database.

Usage:
    python3 import_clients.py --db path/to/database.db --input client_list.xlsx

The input file should contain at least the following columns:
    Code, Name, Phone, Address(1), Address(2), Prepaid balance,
    Owed amount, E-Mail (optional)

CSV files are supported as well. Column names are case‑insensitive.
"""

import argparse
import sqlite3
from pathlib import Path
from typing import Dict

import pandas as pd


def normalise_column_names(cols):
    return [c.strip().lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_') for c in cols]


def import_clients(db_path: str, input_path: str) -> None:
    # Load data using pandas
    ext = Path(input_path).suffix.lower()
    if ext in {'.xls', '.xlsx'}:
        df = pd.read_excel(input_path)
    else:
        df = pd.read_csv(input_path)

    # Normalise column names
    df.columns = normalise_column_names(df.columns)
    # Expected columns
    # code, name, phone, address1, address2, prepaid_balance,
    # owed_amount, e_mail
    # Some spreadsheets may name address columns differently
    mapping: Dict[str, str] = {
        'adress1': 'address1',
        'adress2': 'address2',
        'prepaid_balance': 'prepaid_balance',
        'owed_amount': 'owed_amount',
        'e_mail': 'email',
    }
    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

    # Keep only relevant columns
    keep_cols = ['code', 'name', 'phone', 'address1', 'address2', 'prepaid_balance', 'owed_amount', 'email']
    for col in keep_cols:
        if col not in df.columns:
            df[col] = None
    df = df[keep_cols]

    # Convert balances to floats if possible
    for numeric_col in ['prepaid_balance', 'owed_amount']:
        df[numeric_col] = pd.to_numeric(df[numeric_col].astype(str).str.replace('[^0-9.-]', '', regex=True), errors='coerce')

    # Insert into database
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            df.to_sql('clients', conn, if_exists='append', index=False)
    finally:
        conn.close()
    print(f"Imported {len(df)} clients into {db_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Import client data into the database.'
    )
    parser.add_argument('--db', required=True, help='Path to SQLite database file')
    parser.add_argument('--input', required=True, help='Path to Excel or CSV file containing clients')
    args = parser.parse_args()
    import_clients(args.db, args.input)


if __name__ == '__main__':
    main()
