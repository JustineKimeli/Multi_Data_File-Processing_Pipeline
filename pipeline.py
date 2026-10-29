
# =================================================
# Multi-File Data Processing Pipeline
# =================================================

# import necessary libraries
import csv
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone
# import pandas as pd

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



COLUMN_ALIASES: dict[str, str] = {
    "qty": "quantity",
}


def normalize_columns(header: list[str]) -> list[str]:
    return [
        COLUMN_ALIASES.get(
            column.strip().lower(),
            column.strip().lower()
        )
        for column in header
    ]



def discover_files(folder: Path, pattern: str = "transactions_*.csv"):

    return sorted(folder.glob(pattern))


def read_transactions(path: Path) -> tuple[list[str], list[dict]]:
    def normalize_columns(header: list[str]) -> list[str]:
        return [
        COLUMN_ALIASES.get(column.strip().lower(), column.strip().lower())
        for column in header
    ]
   
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        header = reader.fieldnames or []
        rows = []

        for line_number, row in enumerate(reader, start= 2):
            row["source_file"] = path.name
            row["row_number"] = line_number
            rows.append(row)

        return header, rows


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

    transaction_id = str(row.get("transaction_id") or "").strip()

    if transaction_id and transaction_id in seen_ids:
        problems.append(f"Duplicate transaction ID: {transaction_id}")

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

    cleaned.setdefault("payment_ref", "")

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
    
    if stats["rows_read"] != stats["accepted"] + stats["rejected"]:
        raise ValueError(
            "Summary counts do not reconcile: rows read must equal "
            "accepted plus rejected transactions."
        )
    
    
    
    summary = (
        "==========================================\n"
        "MULTI-FILE TRANSACTION PIPELINE SUMMARY\n"
        "==========================================\n"

        f"Files processed:       {stats['files_processed']}\n"
        f"Rows read:             {stats['rows_read']}\n"
        f"Rows Accepted:         {stats['accepted']}\n"
        f" - Missing Values:     {stats['missing_values']}\n"
        f" - Invalid numbers:    {stats['invalid_numbers']}\n"
        f" - Duplicate IDs:      {stats['duplicate_ids']}\n"
        f"Rows Rejected:         {stats['rejected']}\n"
        f"Total  Revenue (KES):  {stats['total_value']: .2f}\n"
        f"Run Finished At:       {stats['run_finished_at']}\n"
        "============================================\n" 
        "Status: SUCCESS\n"
    )


    return summary




def run_pipeline(input_dir: Path, output_dir: Path) -> dict:
    # Validate the input directory
    if not input_dir.exists():
        raise FileNotFoundError(
            f"Input directory does not exist: {input_dir}"
        )

    if not input_dir.is_dir():
        raise NotADirectoryError(
            f"Input path is not a directory: {input_dir}"
        )

    # Discover input files
    files = discover_files(input_dir)

    if not files:
        raise FileNotFoundError(
            f"No transaction CSV files found in {input_dir}"
        )

    logging.info("Starting transaction pipeline")
    logging.info("Input directory: %s", input_dir)
    logging.info("Output directory: %s", output_dir)
    logging.info("Discovered %d input files", len(files))

    # Initialise statistics
    stats = {
        "files_discovered": len(files),
        "files_processed": 0,
        "file_errors": [],
        "column_issues": [],
        "rows_read": 0,
        "accepted": 0,
        "rejected": 0,
        "missing_values": 0,
        "invalid_numbers": 0,
        "duplicate_ids": 0,
        "total_value": 0,
        "run_finished_at": "",
    }

    accepted_rows = []
    rejected_rows = []
    seen_ids = set()
    input_columns = []

    # Process each input file once
    for path in files:
        logging.info("Processing file: %s", path.name)

        # Read the file safely
        try:
            header, rows = read_transactions(path)
        except (OSError, csv.Error, UnicodeError) as error:
            message = f"{path.name}: {error}"
            logging.error("Could not read file: %s", message)
            stats["file_errors"].append(message)
            continue

        stats["files_processed"] += 1

        # Normalize column names
        normalized_header = normalize_columns(header)

        for row in rows:
            normalized_row = {}

            for original_column, normalized_column in zip(
                header, normalized_header
            ):
                normalized_row[normalized_column] = row.get(
                    original_column
                )

            normalized_row["source_file"] = row["source_file"]
            normalized_row["row_number"] = row["row_number"]

            row.clear()
            row.update(normalized_row)

        header = normalized_header

        # Collect columns for the rejected CSV
        input_columns.extend(header)

        # Check the file's columns
        missing_columns = validate_columns(header)

        if missing_columns:
            message = (
                f"{path.name}: missing "
                + ", ".join(sorted(missing_columns))
            )
            stats["column_issues"].append(message)
            logging.warning("%s", message)

        # Process every row in this file
        for row in rows:
            stats["rows_read"] += 1

            # Validate the row
            if missing_columns:
                problems = [
                    "Missing required columns: "
                    + ", ".join(sorted(missing_columns))
                ]
            else:
                problems = find_problems(row, seen_ids)

            # Reject invalid rows exactly once
            if problems:
                rejected_row = row.copy()
                rejected_row["reasons"] = "; ".join(problems)
                rejected_rows.append(rejected_row)
                stats["rejected"] += 1

                for problem in problems:
                    if problem.startswith("Missing value:"):
                        stats["missing_values"] += 1
                    elif (
                        problem.startswith("Invalid numeric value")
                        or "must be greater than zero" in problem
                    ):
                        stats["invalid_numbers"] += 1
                    elif problem.startswith(
                        "Duplicate transaction ID:"
                    ):
                        stats["duplicate_ids"] += 1

                continue

            # Clean the valid row
            try:
                cleaned = clean_row(row)
            except (ValueError, TypeError, KeyError) as error:
                rejected_row = row.copy()
                rejected_row["reasons"] = f"Cleaning error: {error}"
                rejected_rows.append(rejected_row)
                stats["rejected"] += 1
                logging.warning(
                    "Rejected row %s from %s: %s",
                    row.get("row_number"),
                    path.name,
                    error,
                )
                continue

            # Accept the row exactly once
            accepted_rows.append(cleaned)
            stats["accepted"] += 1
            stats["total_value"] += cleaned["line_total"]

            # Remember the accepted transaction ID
            seen_ids.add(
                str(cleaned["transaction_id"]).strip()
            )

    # Define accepted output columns
    accepted_fields = [
        "transaction_id",
        "date",
        "branch",
        "customer_id",
        "product",
        "quantity",
        "unit_price",
        "line_total",
        "payment_method",
        "payment_ref",
        "source_file",
    ]

    # Define rejected output columns
    rejected_fields = list(dict.fromkeys(
        input_columns
        + ["source_file", "row_number", "transaction_id", "reasons"]
    ))

    # Write output CSV files
    write_csv(
        accepted_rows,
        output_dir / "consolidated_transactions.csv",
        accepted_fields,
    )

    write_csv(
        rejected_rows,
        output_dir / "rejected_transactions.csv",
        rejected_fields,
    )

    # Record the finish time
    stats["run_finished_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    # Verify that every read row has an outcome
    if stats["rows_read"] != stats["accepted"] + stats["rejected"]:
        raise ValueError(
            "Row counts do not reconcile: rows read must equal "
            "accepted plus rejected."
        )

    # Build and save the summary inside the pipeline
    summary = build_summary(stats)

    summary_path = output_dir / "summary.txt"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")

    logging.info(
        "Pipeline finished: %d files discovered, "
        "%d files processed, %d rows read, "
        "%d accepted, %d rejected",
        stats["files_discovered"],
        stats["files_processed"],
        stats["rows_read"],
        stats["accepted"],
        stats["rejected"],
    )
    logging.info("Summary saved to %s", summary_path)

    return stats




# 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="pipeline.py",
        description="Multi-file transaction pipeline",
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data"),
        help="Directory containing input CSV files",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for output results",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        stats = run_pipeline(args.input, args.output)

        print("\nSUMMARY - Pipeline counts")
        print("Files discovered:", stats["files_discovered"])
        print("Files processed:", stats["files_processed"])
        print("Rows read:", stats["rows_read"])
        print("Rows accepted:", stats["accepted"])
        print("Rows rejected:", stats["rejected"])
        print("Accepted + rejected:", stats["accepted"] + stats["rejected"])

        summary = build_summary(stats)

        # Save the summary to a text file.
        summary_path = args.output / "summary.txt"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")

        logging.info("Summary saved to %s", summary_path)

    except (ValueError, OSError, csv.Error) as error:
        logging.error("Pipeline failed: %s", error)
        raise SystemExit(1)


