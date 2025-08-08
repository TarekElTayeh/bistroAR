#!/usr/bin/env python3
"""
Tiny parser for multi-day Veloce journal entry TXT files with Excel export.

Usage:
    python3 txt_journal_parser.py path/to/journal.txt \
        --csv ar.csv --json ar.json --excel ar.xlsx

This script:
  1. Reads each line of the TXT file.
  2. Detects lines starting with a date in MM-DD-YY format and sets current_date.
  3. For lines where the account column is "1105", records an entry with date and amount.
  4. Outputs all entries as CSV, JSON, and Excel.
"""
import csv
import json
import argparse
import sys
from datetime import datetime

# Optional: pandas for Excel export
try:
    import pandas as pd
except ImportError:
    pd = None


def parse_journal_entries(txt_path):
    """
    Parse a multi-day journal entry TXT file to extract all account 1105 transactions.

    Args:
        txt_path (str): Path to the journal entry TXT file.

    Returns:
        list of dict: Each dict has 'date', 'account', and 'amount'.
    """
    entries = []
    current_date = None
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(',')]
                # Check for date header (MM-DD-YY)
                if len(parts) >= 1:
                    try:
                        dt = datetime.strptime(parts[0], '%m-%d-%y')
                        current_date = dt.strftime('%Y-%m-%d')
                        continue
                    except ValueError:
                        pass
                # If we have a current_date, look for account 1105 lines
                if current_date and len(parts) >= 2 and parts[0] == '1105':
                    try:
                        amt = float(parts[1].replace(',', ''))
                    except ValueError:
                        print(f"Warning: invalid amount '{parts[1]}' on date {current_date}")
                        continue
                    entries.append({
                        'date': current_date,
                        'account': '1105',
                        'amount': amt
                    })
    except FileNotFoundError:
        raise ValueError(f"File not found: {txt_path}")
    except Exception as e:
        raise ValueError(f"Failed to read {txt_path}: {e}")

    if not entries:
        raise ValueError(f"No transactions for account 1105 found in {txt_path}")
    return entries


def main():
    parser = argparse.ArgumentParser(
        description='Parse a Veloce multi-day journal entry TXT and export CSV/JSON/Excel'
    )
    parser.add_argument(
        'txt_file',
        help='Path to the journal entry TXT file (e.g., test.txt)'
    )
    parser.add_argument(
        '--csv',
        default='output.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--json',
        default='output.json',
        help='Output JSON file path'
    )
    parser.add_argument(
        '--excel',
        default='output.xlsx',
        help='Output Excel file path (.xlsx)'
    )

    args = parser.parse_args()

    try:
        records = parse_journal_entries(args.txt_file)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Write CSV
    try:
        with open(args.csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['date', 'account', 'amount'])
            writer.writeheader()
            for r in records:
                writer.writerow(r)
    except Exception as e:
        print(f"Failed to write CSV: {e}")
        sys.exit(1)

    # Write JSON
    try:
        with open(args.json, 'w', encoding='utf-8') as jsonfile:
            json.dump(records, jsonfile, indent=2)
    except Exception as e:
        print(f"Failed to write JSON: {e}")
        sys.exit(1)

    # Write Excel if pandas is available
    if pd:
        try:
            df = pd.DataFrame(records)
            df.to_excel(args.excel, index=False)
        except Exception as e:
            print(f"Failed to write Excel: {e}")
            sys.exit(1)
    else:
        print("Pandas not installed; skipping Excel export. Install pandas to enable this feature.")

    # Print transactions to console
    print(f"Parsed {len(records)} transactions for account 1105:")
    for rec in records:
        print(f"{rec['date']}, Account {rec['account']}, Amount {rec['amount']}")

if __name__ == '__main__':
    main()
