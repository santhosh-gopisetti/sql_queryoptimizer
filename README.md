# SQL Query Performance Analyzer

A command-line tool built in Python to analyze the performance of MySQL queries, measure execution time, and provide actionable optimization suggestions based on the `EXPLAIN` plan.

This tool helps developers quickly identify performance bottlenecks like full table scans, missing indexes, and inefficient operations, offering clear guidance on how to fix them.

## Key Features

-   **Execution Time:** Measures the precise execution time of your query in milliseconds.
-   **`EXPLAIN` Plan Analysis:** Automatically runs `EXPLAIN` on your query and parses the output.
-   **Problem Detection:** Identifies common performance issues, including:
    -   Full Table Scans (`type: ALL`)
    -   Missing Indexes (`key: NULL`)
    -   Inefficient Operations (`Extra: Using filesort`, `Extra: Using temporary`)
-   **Actionable Suggestions:** Provides human-readable tips to fix the detected problems (e.g., "Consider adding an index...").
-   **Summary Report:** Displays all findings in a clean, easy-to-read report directly in your console.

## Technology Stack

-   **Python** 3.9+
-   **`mysql-connector-python`**: For connecting to and querying the MySQL database.
-   **`argparse`**: For parsing all command-line arguments.
-   **`rich`**: For beautifully formatting the final summary report in the terminal.

## Installation

1.  Clone this repository:
    ```bash
    git clone [https://github.com/your-username/sql-analyzer.git](https://github.com/your-username/sql-analyzer.git)
    cd sql-analyzer
    ```

2.  Install the required Python libraries (you must first create a `requirements.txt` file):
    ```bash
    pip install -r requirements.txt
    ```

    Your `requirements.txt` file should contain:
    ```text
    mysql-connector-python
    rich
    ```

## Usage

Run the tool from your terminal, providing the database credentials and the query you wish to analyze.

```bash
python sql_analyzer.py \
  --host "localhost" \
  --user "root" \
  --password "mysecretpassword" \
  --database "app_db" \
  --query "SELECT * FROM orders WHERE customer_id = 123 ORDER BY order_date;"
