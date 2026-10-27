## Multi-File Data Processing Pipeline
# Project Overview
This project implements a Python pipeline that processes multiple transaction CSV files, validates and cleans records, consolidates valid transactions, saves rejected records separately, and generates a processing summary


# Approach
The pipeline uses pathlib to discover files matching transactions_*.csv in the input directory. Each file is read using csv.DictReader, and each row is tagged with its source filename and row number.

Required columns are validated before individual records are checked for missing values, invalid or non-positive numeric values, and duplicate transaction IDs. Valid records are cleaned by stripping whitespace, converting quantity and unit_price to integers, and calculating line_total.

Accepted records from all input files are combined into one CSV. Rejected records are saved separately with explanations. The summary reports file processed, rows read, accepted transactions, rejected transactions, and total accepted revenue in KES, and the completion timestamp.

# Project Structure
```
multi-file-pipeline/
|--- pipeline.py
|--- data/
|   |--- transactions_2026-10-01.csv
|   |--- transactions_2026-10-02.csv
|   |--- transactions_2026-10-03.csv
|--- output/
|   |--- consolidated_transactions.csv
|   |--- rejected_trasactions.csv
|   |--- sumamary.text
|--- requirements.txt
|--- README.md
```
# Work Flow
- **Discover files:** Use pathlib to locate matching CSV files.
- **Validate columns:** Check for required fields: transaction_id, date, branch, customer_id, product, quantity, unit_price, and payment_method.
- **Validate records:** Identify missing values, invalid or non-positive numeric values, and duplicate transaction IDs.
- **Clean records:** Strip whitespace, convert numeric fields to integers, and calculate total(quantity * price)
- **Consolidate records:** Combine accepted transactions from all input files into one CSV.
- **Save rejected records:** Preserve invalid rows with their rejection reasons.
- **Generate a summary:** Summary report showing file counts, row counts, rejection categories, and total value.

# Outputs
- output/consolidated_transactions.csv ---> cleaned, accepted transactions
- output/ rejected_transactions.csv ---> Rejected records, source, information and rejection reasons.

# Conclusion
The pipeline demonstrates multi-file processing, schema validation, data cleaning, duplicate detection, exception handling, CSV consolidation, and reporting using Python.
