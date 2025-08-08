#!/usr/bin/env python3
"""
parse_transactions.py

This script extracts detailed transaction records from a multi‑page PDF of Veloce
client transactions. Each record includes the client code, date, time,
reference number, employee name, item description and price.

Usage:
    python3 parse_transactions.py input.pdf --csv output.csv --json output.json

Requirements:
    - pdfplumber
"""

import argparse
import csv
import json
import re
from typing import Dict, List

import pdfplumber


def parse_transaction_pdf(pdf_path: str) -> List[Dict[str, str]]:
    """Parse a transaction PDF into a list of records.

    Each record is a dictionary containing:
        client_code (str)
        date (YYYY-MM-DD)
        time (HH:MM)
        reference (str)
        employee (str)
        description (str)
        price (float)
    """
    records: List[Dict[str, str]] = []
    header_info: Dict[str, str] = {}

    # Header pattern: code, date, time, reference and employee
    header_pattern = re.compile(
        r'^(?P<code>\d+)\s+'
        r'(?P<date>\d{1,2}/\d{1,2}/\d{2})\s+'
        r'(?P<time>\d{1,2}:\d{2})\s+'
        r'#?(?P<ref>\d+)\s+'
        r'(?P<emp>\S+)'
    )

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                line = line.strip()
                # Check if this line is a header
                match = header_pattern.match(line)
                if match:
                    info = match.groupdict()
                    # Normalize date from mm/dd/yy to YYYY-MM-DD
                    mm, dd, yy = info['date'].split('/')
                    yyyy = '20' + yy
                    info['date'] = f"{yyyy}-{int(mm):02d}-{int(dd):02d}"
                    info['client_code'] = info.pop('code')
                    info['reference'] = info.pop('ref')
                    info['employee'] = info.pop('emp')
                    header_info = info
                else:
                    # Attempt to parse item line: description + price at end
                    if not header_info:
                        continue
                    parts = line.rsplit(' ', 1)
                    if len(parts) != 2:
                        continue
                    desc, price_str = parts
                    price_str = price_str.replace('$', '').replace(',', '')
                    try:
                        price = float(price_str)
                    except ValueError:
                        continue
                    record = {
                        'client_code': header_info['client_code'],
                        'date': header_info['date'],
                        'time': header_info['time'],
                        'reference': header_info['reference'],
                        'employee': header_info['employee'],
                        'description': desc.strip(),
                        'price': price,
                    }
                    records.append(record)
    return records


def export_records(records: List[Dict[str, str]], csv_path: str, json_path: str) -> None:
    """Export parsed records to CSV and JSON files."""
    if not records:
        print("No records found.")
        return

    # Write CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    # Write JSON
    with open(json_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(records, jsonfile, indent=2)

    print(f"Exported {len(records)} records to '{csv_path}' and '{json_path}'.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Extract client transactions from a Veloce PDF and export them to CSV and JSON.'
    )
    parser.add_argument('pdf_file', help='Path to the input PDF file')
    parser.add_argument('--csv', default='transactions.csv', help='Path to output CSV file')
    parser.add_argument('--json', default='transactions.json', help='Path to output JSON file')
    args = parser.parse_args()

    records = parse_transaction_pdf(args.pdf_file)
    export_records(records, args.csv, args.json)


if __name__ == '__main__':
    main()