#!/usr/bin/env python3
import pdfplumber
import re
import csv
import json
import argparse

def parse_transaction_pdf(pdf_path):
    """
    Parses a transaction PDF and returns a list of records where each record is a dict:
      {
        "client_code": str,
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "reference": str,
        "employee": str,
        "description": str,
        "price": float
      }
    """
    records = []
    header_info = {}

    # regex to detect header lines: code, date, time, reference, employee
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
                # Try matching header
                m = header_pattern.match(line)
                if m:
                    info = m.groupdict()
                    # Normalize date to YYYY-MM-DD
                    mm, dd, yy = info['date'].split('/')
                    yyyy = '20' + yy
                    info['date'] = f"{yyyy}-{int(mm):02d}-{int(dd):02d}"
                    info['client_code'] = info.pop('code')
                    info['reference']   = info.pop('ref')
                    info['employee']    = info.pop('emp')
                    info['time']        = info['time']
                    header_info = info
                else:
                    # Attempt to parse an item line: description + price at end
                    parts = line.rsplit(' ', 1)
                    if len(parts) == 2 and header_info:
                        desc, price_str = parts
                        # Clean price string
                        price_str = price_str.replace('$', '').replace(',', '')
                        try:
                            price = float(price_str)
                        except ValueError:
                            continue
                        record = {
                            "client_code": header_info['client_code'],
                            "date":        header_info['date'],
                            "time":        header_info['time'],
                            "reference":   header_info['reference'],
                            "employee":    header_info['employee'],
                            "description": desc.strip(),
                            "price":       price
                        }
                        records.append(record)
    return records

def export_data(records, csv_path, json_path):
    if not records:
        print("No records to export. ")
        return
    
    # Write CSV
    with open(csv_path,'w', newline='') as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    # Write JSON
    with open(json_path, 'w') as f_json:
        json.dump(records, f_json, indent=2)

    print(f"Exported {len(records)} records to '{csv_path}' and '{json_path}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract transaction details from a PDF and export to CSV/JSON")
    
    parser.add_argument("pdf file", help="Path to the transaction PDF")
    parser.add_argument("--csv", default="transactions.csv", help="output CSV file parth")
    parser.add_argument("--json", default="transactions.json", help="Output JSON file path")
    args = parser.parse_args()

    records = parse_transaction_pdf(args.pdf_file)
    export_data(records, args.csv, args.json)
    
