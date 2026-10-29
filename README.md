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
|---| data/
|   |--- transactions_2026-10-01.csv
|   |--- transactions_2026-10-02.csv
|   |--- transactions_2026-10-03.csv
|---| output/
|   |--- consolidated_transactions.csv
|   |--- rejected_trasactions.csv
|   |--- summary.text
|--- requirements.txt
|--- README.md
```
The output files are generated when the pipeline runs.

# Requirements
- Python 3.10
- Git Bash
- Data/directory --> 3 transactions.csv files

# Setup and Run Instructions
**1. Open the project directory**

Navigate to the project root in Git Bash:

cd /c/Users/USER/OneDrive/Desktop/Day2/day2-multi-file-pipeline

**2. Create a virtual environment**

python  venv day2-multi-file-pipelineenv

**3. Activate the environment**

source day2-multi-file-pipelineenv/Scripts/activate

**4. Install dependencies**

pip install -r requirements.txt

**5. Run the pipeline**

python pipeline.py

The pipeline reads CSV files from data/ and writes the results to output/.

**6. Verify the outputs**
Run the command in Git Bash 
ls output
cat output/summary.txt

Confirms the output files
output/consolidated_transactions.csv — validated transactions.

output/rejected_transactions.csv — rejected transactions and their reasons.

output/summary.txt — processing statistics and total revenue.

# Data Processing and Validation
**Validation rules**
The pipeline checks for:
- Missing required values.
- Invalid or non-positive quantities and unit prices.
- Duplicate transaction IDs.
- Missing required columns.
- Errors encountered while cleaning transaction records.
- Rejected rows are recorded with the reasons for rejection.

**Duplicate transaction IDs**

The pipeline uses a set of previously accepted transaction IDs to identify duplicates.
When a transaction ID has already been accepted, a later row with the same ID is rejected. The first accepted occurrence is retained, and subsequent occurrences are recorded in ```rejected_transactions.csv.```

If the first occurrence is itself rejected for another validation error, the current implementation may allow a later occurrence to be accepted. Duplicate handling is therefore based on previously accepted IDs rather than every ID encountered in the input files.


# Output Files
** consolidated_transactions.csv**

It contains accepted transactions with standardized columns, including transaction_id, date, branch, customer_id, product, quantity, unit_price, line_total, payment_method, payment_ref, and source_file.

**rejected_transactions.csv**
It contains rejected transactions, their source file and row number, and the reasons why they were rejected.

**summary.txt**

This reports files discovered and processing counts, row counts, row number, total revenue in KES and the time the pipeline was finished(timestamp).
It also verifies that the number of rows read equals the number accepted and those that were rejected.

# Conclusion
The pipeline demonstrates multi-file processing, schema validation, data cleaning, duplicate detection, exception handling, CSV consolidation, and reporting using Python.
