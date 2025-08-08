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


def _normalise(columns):
    return [c.strip().lower().replace(' ', '_') for c in columns]


def load_monthly_report(path: str) -> Dict[str, float]:
    ext = Path(path).suffix.lower()
    if ext in {'.xls', '.xlsx'}:
        raw = pd.read_excel(path, header=None)
    else:
        raw = pd.read_csv(path, header=None)

    header_row = 0
    for idx, row in raw.iterrows():
        cols = _normalise(row.fillna('').astype(str))
        if any('code' in c or 'client' in c for c in cols) and any(
            c.startswith('balance')
            or c.startswith('owed')
            or 'amount' in c
            or c.startswith('total')
            for c in cols
        ):
            header_row = idx
            break

    if ext in {'.xls', '.xlsx'}:
        df = pd.read_excel(path, header=header_row)
    else:
        df = pd.read_csv(path, header=header_row)

    df.columns = _normalise(df.columns)

    code_col = None
    balance_col = None
    for col in df.columns:
        if code_col is None and ('code' in col or 'client' in col):
            code_col = col
        if balance_col is None and (
            col.startswith('balance')
            or col.startswith('owed')
            or 'amount' in col
            or col.startswith('total')
        ):
            balance_col = col

    if code_col is None or balance_col is None:
        raise ValueError('Unable to determine code or balance columns in monthly report')

    report: Dict[str, float] = {}
    for _, row in df.iterrows():
        code = str(row[code_col]).strip()
        if not code or code.lower() == 'nan':
            continue
        try:
            balance = float(str(row[balance_col]).replace('$', '').replace(',', '').strip())
        except ValueError:
            continue
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