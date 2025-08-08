#!/usr/bin/env python3
"""
init_db.py

Initialise a SQLite database using a provided SQL schema.

Usage:
    python3 init_db.py --db path/to/database.db --schema path/to/schema.sql

This script reads a schema file containing one or more CREATE TABLE
statements and executes them against the specified SQLite database.
It will create the database file if it does not exist.
"""

import argparse
import sqlite3
from pathlib import Path


def init_db(db_path: str, schema_path: str) -> None:
    # Read schema SQL
    schema = Path(schema_path).read_text(encoding='utf-8')
    # Connect to database (creates file if necessary)
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            conn.executescript(schema)
    finally:
        conn.close()
    print(f"Database initialised at {db_path} using schema {schema_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Initialise a SQLite database from a schema file.'
    )
    parser.add_argument('--db', required=True, help='Path to SQLite database file')
    parser.add_argument('--schema', required=True, help='Path to schema SQL file')
    args = parser.parse_args()
    init_db(args.db, args.schema)


if __name__ == '__main__':
    main()