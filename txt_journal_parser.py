#!/usr/bin/env python3
"""
txt_journal_parser.py

Parse a text file containing daily journal entries exported from Veloce/Velbo
and extract the individual transactions for account 1105. The input file
may contain multiple days worth of data. For each transaction line on
account 1105, the script emits a record with the date (YYYY-MM-DD) and
the amount.

Usage:
    python3 txt_journal_parser.py journal.txt --csv ar.csv --json ar.json --excel ar.xlsx

If --csv/--json/--excel are not provided, defaults to output.csv/output.json/output.xlsx.

Requirements:
    - pandas (for Excel export)
"""

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict

try:
    import pandas as pd  # type: ignore
except ImportError:
    pd = None  # type: ignore


DATE_PATTERN = re.compile(r'^(\d{2})-(\d{2})-(\d{2})')
ENTRY_PATTERN = re.compile(r'^(\d+),\s*([-+]?[0-9]*\.?[0-9]+)')


def parse_journal_file(txt_path: str) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    current_date_iso = None
    with open(txt_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Check for date line
            date_match = DATE_PATTERN.match(line)
            if date_match:
                mm, dd, yy = date_match.groups()
                yyyy = '20' + yy
                try:
                    date_obj = datetime.strptime(f"{yyyy}-{mm}-{dd}", '%Y-%m-%d')
                    current_date_iso = date_obj.strftime('%Y-%m-%d')
                except Exception:
                    current_date_iso = None
                continue
            # Check for account entry line
            entry_match = ENTRY_PATTERN.match(line)
            if entry_match and current_date_iso:
                account = entry_match.group(1)
                amount_str = entry_match.group(2)
                try:
                    amount = float(amount_str)
                except ValueError:
                    continue
                # Only process account 1105
                if account == '1105':
                    records.append({
                        'date': current_date_iso,
                        'account': account,
                        'amount': amount,
                    })
    return records


def export_records(records: List[Dict[str, str]], csv_path: str, json_path: str, excel_path: str) -> None:
    if not records:
        print("No transactions found for account 1105.")
        return
    # CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    # JSON
    with open(json_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(records, jsonfile, indent=2)
    # Excel (optional)
    if excel_path:
        if pd is None:
            print("pandas is not installed; skipping Excel export.")
        else:
            df = pd.DataFrame(records)
            df.to_excel(excel_path, index=False)
    print(f"Exported {len(records)} records to {csv_path}, {json_path} and {excel_path if excel_path else 'N/A'}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Parse a Veloce journal TXT file and extract account 1105 transactions.'
    )
    parser.add_argument('txt_file', help='Path to the journal text file')
    parser.add_argument('--csv', default='output.csv', help='Path to output CSV')
    parser.add_argument('--json', default='output.json', help='Path to output JSON')
    parser.add_argument('--excel', default='output.xlsx', help='Path to output Excel (requires pandas)')
    args = parser.parse_args()

    records = parse_journal_file(args.txt_file)
    export_records(records, args.csv, args.json, args.excel)


if __name__ == '__main__':
    main()