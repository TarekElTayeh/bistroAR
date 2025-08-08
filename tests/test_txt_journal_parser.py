import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parents[1]))

import txt_journal_parser as parser


def test_parse_journal_file_extracts_account_1105_transactions():
    records = parser.parse_journal_file('test/test.txt')
    assert len(records) == 1
    record = records[0]
    assert record['date'] == '2025-08-05'
    assert record['account'] == '1105'
    assert record['amount'] == 31.85
