
# =================================================
# Multi-File Data Processing Pipeline
# =================================================


import csv
import logging
import argparse
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS: set[str] = {
    "transaction_id", 
    "date", 
    "branch",
    "customer_id",
    "product",
    "quantity", 
    "unit_price", 
    "payment_method",
}



COLUMN_ALIASES: dict[str, str] = {}


def discover_files(folder: Path, pattern: str = "transactions_*.csv"):

    return sorted(folder.glob(pattern))


def read_transactions(path: Path) -> tuple[list[str], list[dict]]:
   
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        header = reader.fieldnames or []
        rows = []

        for line_number, row in enumerate(reader, start= 2):
            row["source_file"] = path.name
            row["row_number"] = line_number
            rows.append(row)

        return header, rows
from pathlib import Path

files = [
    Path("data/transactions_2026-10-01.csv"),
    Path("data/transactions_2026-10-02.csv"),
    Path("data/transactions_2026-10-03.csv"),
]

for path in files:
    header, rows = read_transactions(path)

    print(f"\nFile: {path.name}")
    print("Columns:", header)
    print("Number of rows:", len(rows))

    if rows:
        print("First row:", rows[0])


def validate_columns(header: list[str], required: set[str] = REQUIRED_COLUMNS) -> set[str]:
    return required - set(header)

def find_problems(row: dict, seen_ids: set[str]) -> list[str]:
    
    problems = []

    # check blank required values
    for column in REQUIRED_COLUMNS:
        value = row.get(column)


        if value is None or not str(value).strip():
            problems.append(f"Missing value: {column}")


    # check quantity and unit_price
    for column in ("quantity", "unit_price"):
        value = row.get(column)

        if value is None or not str(value).strip():
            continue

        try:
            number = float(value)

            if number <= 0:
                problems.append(f"{column} must be greater than zero")
            

        except (ValueError, TypeError):
            problems.append(f"Invalid numeric value for {column}:{value}")

        # checking duplicate ids

    transaction_id = str(row.get("transaction_id", "")).strip()

    if transaction_id and transaction_id in seen_ids:
            problems.append(f"Dupliacte trasaction ID: {transaction_id}")

    return problems
    

def clean_row(row: dict) -> dict:
    # strip whitespace from string values
    cleaned = {
        key: value.strip() if isinstance(value,str) else value 
        for key, value in row.items()
    }


    #convert numeric values to intergers
    for column in ("quantity", "unit_price"):
        cleaned[column] = int(cleaned[column])

    #calculate the total transaction total
    cleaned["line_total"] = cleaned["quantity"] * cleaned["unit_price"]


    return cleaned




def write_csv(rows: list[dict], path: Path, fieldnames: list[str]) -> None:

    path.parent.mkdir(parents=True,exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer= csv.DictWriter(
            file,
            fieldnames= fieldnames,
            extrasaction= "ignore"
        )

        writer.writeheader()
        writer.writerows(rows)



def build_summary(stats: dict) -> str:

    # build pipeline summary
    summary = (
        "==========================================\n"
        "MULTI-FILE TRANSACTION PIPELINE SUMMARY\n"
        "==========================================\n"

        f"Files processed: {stats['files_processed']}\n"
        f"Rows read: {stats['rows_read']}\n"
        f"Accepted transactions: {stats['accepted']}\n"
        f"Rejected transactions: {stats['rejected']}\n"
        f"Total Accepted value: KES {stats['total_value']}\n"
    )


    return summary



def run_pipeline(input_dir: Path, output_dir: Path) -> dict:
    #  input files
    files = discover_files(input_dir)
    for path in files:
        header, rows = read_transactions(path)


    # Initialise statistics and collections
    stats = {
        "files_processed": 0,
        "rows_read": 0,
        "accepted": 0,
        "rejected": 0,
        "total_value": 0,
        

    }

    accepted_rows = []
    rejected_rows = []
    seen_ids = set()
    input_columns = []

    # Process  files
    for path in files:
        stats["files_processed"] += 1

        header, rows = read_transactions(path)

        
        for column in header:
            if column not in input_columns:
                input_columns.append(column)

        missing_columns = validate_columns(header)

        # for loop to access Process in each row
        for row in rows:
            stats["rows_read"] += 1

            if missing_columns:
                problems = [
                    "Missing required columns: "
                    + ", ".join(sorted(missing_columns))
                ]
            else:
                problems = find_problems(row, seen_ids)

            # Reject invalid rows
            if problems:
                rejected_row = row.copy()
                rejected_row["rejection_reason"] = "; ".join(problems)
                rejected_rows.append(rejected_row)
                stats["rejected"] += 1
                continue

            # Clean valid rows
            try:
                cleaned = clean_row(row)
            except (ValueError, TypeError, KeyError) as error:
                rejected_row = row.copy()
                rejected_row["rejection_reason"] = (
                    f"Cleaning error: {error}"
                )
                rejected_rows.append(rejected_row)
                stats["rejected"] += 1
                continue

            accepted_rows.append(cleaned)
            stats["accepted"] += 1
            stats["total_value"] += cleaned["line_total"]

            # Transaction IDs for duplicate detection
            seen_ids.add(str(cleaned["transaction_id"]).strip())

    # output columns
    accepted_fields = list(dict.fromkeys(
        input_columns + ["source_file", "row_number", "line_total"]
    ))

    rejected_fields = list(dict.fromkeys(
        input_columns + ["source_file", "row_number", "rejection_reason"]
    ))

    # Write to files
    write_csv(
        accepted_rows,
        output_dir / "accepted_transactions.csv",
        accepted_fields,
    )

    write_csv(
        rejected_rows,
        output_dir / "rejected_transactions.csv",
        rejected_fields,
    )

    #Returning statistics for build_summary()
    return stats
    
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog ='pipeline.py',
        description = "Multi-file transaction pipeline"
    )

    parser.add_argument(
        "--input",
        type = Path,
        default= Path("data"),
        help ="Directory containing input csv files"
    )


    parser.add_argument(
            "--output",
            type = Path,
            default=Path("output"),
            help ="Directory for output results"
    )


    args = parser.parse_args()

    logging.basicConfig(
        level = logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    stats = run_pipeline(args.input, args.output)
    print(build_summary(stats))

