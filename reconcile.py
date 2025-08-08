#!/usr/bin/env python3
"""
reconcile.py

Reconcile aggregated visit totals against a monthly report. The monthly
report is expected to be a CSV or Excel file containing client codes
and their corresponding balances for the month. The script compares
the summed totals in the visits table for the given period against
these balances and outputs discrepancies.

Usage:
    python3 reconcile.py --db bistro54.db --monthly report.csv --period 2025-07

The script writes a CSV of reconciliation issues and prints a summary.
"""

import argparse
import csv
import sqlite3
from pathlib import Path
from typing import Dict

import pandas as pd


def load_monthly_report(path: str) -> Dict[str, float]:
    ext = Path(path).suffix.lower()
    if ext in {'.xls', '.xlsx'}:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    # Normalise column names
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    # Determine code column and balance column heuristically
    code_col = None
    balance_col = None
    for col in df.columns:
        if col.startswith('code') or col == 'client_code':
            code_col = col
        if col.startswith('balance') or col.startswith('owed'):
            balance_col = col
    if code_col is None or balance_col is None:
        raise ValueError('Unable to determine code or balance columns in monthly report')
    report = {}
    for _, row in df.iterrows():
        code = str(row[code_col]).strip()
        try:
            balance = float(str(row[balance_col]).replace('$', '').replace(',', ''))
        except ValueError:
            balance = 0.0
        report[code] = report.get(code, 0.0) + balance
    return report


def reconcile(db_path: str, monthly_report_path: str, period: str, output_path: str) -> None:
    report = load_monthly_report(monthly_report_path)
    conn = sqlite3.connect(db_path)
    discrepancies = []
    try:
        cur = conn.cursor()
        for code, expected_balance in report.items():
            # Sum totals for visits in period for this client
            cur.execute(
                """
                SELECT SUM(total) FROM visits
                WHERE client_code = ? AND date LIKE ?
                """,
                (code, f"{period}-%"),
            )
            row = cur.fetchone()
            actual = row[0] if row[0] is not None else 0.0
            diff = actual - expected_balance
            if abs(diff) > 0.01:
                discrepancies.append({
                    'client_code': code,
                    'expected_balance': expected_balance,
                    'actual_total': actual,
                    'difference': diff,
                })
    finally:
        conn.close()

    if discrepancies:
        # Write discrepancies to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['client_code', 'expected_balance', 'actual_total', 'difference'])
            writer.writeheader()
            writer.writerows(discrepancies)
        print(f"Found {len(discrepancies)} reconciliation issues. See '{output_path}'.")
    else:
        print("No reconciliation issues found.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Reconcile visits totals against a monthly report.'
    )
    parser.add_argument('--db', required=True, help='Path to SQLite database')
    parser.add_argument('--monthly', required=True, help='Path to monthly report (CSV or Excel)')
    parser.add_argument('--period', required=True, help='Period string (YYYY-MM)')
    parser.add_argument('--out', default='recon_issues.csv', help='Output CSV path for discrepancies')
    args = parser.parse_args()
    reconcile(args.db, args.monthly, args.period, args.out)


if __name__ == '__main__':
    main()