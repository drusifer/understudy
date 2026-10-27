"""Convert a flat financial CSV export into Understudy's staged JSONL rows."""

import argparse
import csv
import json
from datetime import date, datetime
from pathlib import Path


def convert_csv_to_jsonl(
    source_path: Path,
    destination_path: Path,
    source: str,
    date_column: str,
    amount_column: str,
    merchant_column: str,
) -> int:
    """Write one normalized, provenance-bearing JSON object per CSV row."""
    count = 0
    with source_path.open(encoding="utf-8-sig", newline="") as source_file:
        reader = csv.DictReader(source_file)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row")
        missing = [
            column
            for column in (date_column, amount_column, merchant_column)
            if column not in reader.fieldnames
        ]
        if missing:
            raise ValueError(f"CSV is missing mapped columns: {', '.join(missing)}")
        with destination_path.open("w", encoding="utf-8", newline="\n") as output:
            for row_number, row in enumerate(reader, start=1):
                record = {
                    "source": source,
                    "source_row_number": row_number,
                    "transaction_date": _normalize_date(row[date_column]),
                    "amount": row[amount_column],
                    "merchant": row[merchant_column],
                    "raw_record": row,
                }
                output.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
    return count


def _normalize_date(value: str | None) -> str | None:
    """Normalize supported export date formats while raw_record retains the source text."""
    if not value:
        return value
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        try:
            return datetime.strptime(value, "%m/%d/%Y").date().isoformat()
        except ValueError:
            return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_path", type=Path)
    parser.add_argument("destination_path", type=Path)
    parser.add_argument("source")
    parser.add_argument("date_column")
    parser.add_argument("amount_column")
    parser.add_argument("merchant_column")
    args = parser.parse_args()
    convert_csv_to_jsonl(
        args.source_path,
        args.destination_path,
        args.source,
        args.date_column,
        args.amount_column,
        args.merchant_column,
    )


if __name__ == "__main__":
    main()
