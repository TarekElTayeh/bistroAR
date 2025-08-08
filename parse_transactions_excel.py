#!/usr/bin/env python3
"""
parse_transactions_excel.py

Convert a monthly transactions Excel report into the same CSV/JSON
structure expected by the automation pipeline. The input Excel file
should contain columns for client code, date, time, reference number,
employee, item description, and price. Column names are matched
case‑insensitively and with underscore/space normalization.

Usage:
    python3 parse_transactions_excel.py transactions.xlsx --csv july_txns.csv --json july_txns.json

This script produces a list of records with keys:
    client_code, date (YYYY-MM-DD), time (HH:MM), reference, employee,
    description, price
"""

import argparse
import csv
import json
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd


def normalise_columns(columns):
    return [c.strip().lower().replace(' ', '_') for c in columns]


def find_column(df_columns, keywords) -> Optional[str]:
    for kw in keywords:
        for col in df_columns:
            if kw in col:
                return col
    return None


def parse_excel(path: str) -> List[Dict[str, str]]:
    df = pd.read_excel(path)
    df.columns = normalise_columns(df.columns)
    # Identify columns heuristically
    code_col = find_column(df.columns, ['client_code', 'code', 'client'])
    date_col = find_column(df.columns, ['date', 'transaction_date'])
    time_col = find_column(df.columns, ['time', 'transaction_time'])
    reference_col = find_column(df.columns, ['reference', 'ref', '#'])
    employee_col = find_column(df.columns, ['employee', 'server'])
    desc_col = find_column(df.columns, ['description', 'item', 'detail'])
    price_col = find_column(df.columns, ['price', 'amount', 'total'])
    if not all([code_col, date_col, time_col, reference_col, employee_col, desc_col, price_col]):
        missing = [name for name, col in [
            ('client code', code_col),
            ('date', date_col),
            ('time', time_col),
            ('reference', reference_col),
            ('employee', employee_col),
            ('description', desc_col),
            ('price', price_col),
        ] if col is None]
        raise ValueError(f"Missing expected columns: {', '.join(missing)}")
    records: List[Dict[str, str]] = []
    for _, row in df.iterrows():
        code = str(row[code_col]).strip()
        # Parse date
        date_val = row[date_col]
        if pd.isna(date_val):
            continue
        if isinstance(date_val, datetime):
            date_iso = date_val.strftime('%Y-%m-%d')
        else:
            # Attempt to parse from string
            try:
                date_iso = pd.to_datetime(str(date_val)).strftime('%Y-%m-%d')
            except Exception:
                continue
        # Parse time
        time_val = row[time_col]
        time_str = ''
        if isinstance(time_val, datetime):
            time_str = time_val.strftime('%H:%M')
        elif isinstance(time_val, (int, float)):
            # Excel time stored as fraction of day
            try:
                time_str = (datetime(1899, 12, 30) + pd.to_timedelta(time_val, unit='d')).strftime('%H:%M')
            except Exception:
                time_str = ''
        else:
            time_str = str(time_val).strip()
        # Price
        try:
            price = float(str(row[price_col]).replace('$', '').replace(',', '').strip())
        except Exception:
            price = 0.0
        record = {
            'client_code': code,
            'date': date_iso,
            'time': time_str,
            'reference': str(row[reference_col]).strip(),
            'employee': str(row[employee_col]).strip(),
            'description': str(row[desc_col]).strip(),
            'price': price,
        }
        records.append(record)
    return records


def export_records(records: List[Dict[str, str]], csv_path: str, json_path: str) -> None:
    if not records:
        print("No records extracted from Excel file.")
        return
    # CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    # JSON
    with open(json_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(records, jsonfile, indent=2)
    print(f"Exported {len(records)} records to '{csv_path}' and '{json_path}'.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Convert a monthly transaction Excel report into CSV/JSON for the automation pipeline.'
    )
    parser.add_argument('excel_file', help='Path to the Excel file containing transaction details')
    parser.add_argument('--csv', default='transactions.csv', help='Path to output CSV file')
    parser.add_argument('--json', default='transactions.json', help='Path to output JSON file')
    args = parser.parse_args()
    records = parse_excel(args.excel_file)
    export_records(records, args.csv, args.json)


if __name__ == '__main__':
    main()