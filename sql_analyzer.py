#!/usr/bin/env python3
"""
SQL Query Performance Analyzer
A command-line tool to analyze MySQL query performance and provide optimization suggestions.
"""

import argparse
import sys
import time
from typing import List, Dict, Tuple, Any

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("Error: mysql-connector-python is not installed.")
    print("Install it using: pip install mysql-connector-python")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: 'rich' library not found. Using plain text output.")
    print("For better formatting, install it: pip install rich\n")


class SQLAnalyzer:
    def __init__(self, host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.console = Console() if RICH_AVAILABLE else None

    def connect(self) -> bool:
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return True
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")
            return False

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def measure_execution_time(self, query: str) -> Tuple[float, int]:
        cursor = self.connection.cursor()

        start_time = time.perf_counter()
        cursor.execute(query)
        results = cursor.fetchall()
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000
        row_count = len(results)

        cursor.close()
        return execution_time_ms, row_count

    def get_explain_plan(self, query: str) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor(dictionary=True)

        explain_query = f"EXPLAIN {query}"
        cursor.execute(explain_query)
        explain_results = cursor.fetchall()

        cursor.close()
        return explain_results

    def analyze_performance(self, explain_plan: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        problems = []
        suggestions = []

        for idx, row in enumerate(explain_plan):
            table_name = row.get('table', 'unknown')
            select_type = row.get('select_type', '')
            type_value = row.get('type', '')
            key_value = row.get('key')
            extra = row.get('Extra', '')
            rows = row.get('rows', 0)

            if type_value == 'ALL':
                problems.append(f"Full Table Scan on table '{table_name}'")
                suggestions.append(
                    f"A full table scan was detected on table '{table_name}'. "
                    f"Consider adding an index on the column(s) used in your WHERE or ON clauses."
                )

            if key_value is None and type_value not in ('ALL', 'index'):
                problems.append(f"No index used for table '{table_name}'")
                suggestions.append(
                    f"The query did not use an index for table '{table_name}'. "
                    f"Review your WHERE clause and consider adding an appropriate index."
                )

            if extra and 'Using filesort' in extra:
                problems.append(f"Using filesort for table '{table_name}'")
                suggestions.append(
                    f"The query is using a filesort operation on table '{table_name}'. "
                    f"Consider adding an index on the column(s) in your ORDER BY clause."
                )

            if extra and 'Using temporary' in extra:
                problems.append(f"Using temporary table for '{table_name}'")
                suggestions.append(
                    f"The query is creating a temporary table for '{table_name}'. "
                    f"This is often caused by GROUP BY or UNION. Review your query logic or "
                    f"ensure columns in GROUP BY are indexed."
                )

            if extra and 'Using where' in extra and key_value is None:
                problems.append(f"Unindexed WHERE clause on table '{table_name}'")
                suggestions.append(
                    f"The WHERE clause on table '{table_name}' is not using an index. "
                    f"This will significantly slow down the query. Add an index on the filtered columns."
                )

            if rows and rows > 10000:
                problems.append(f"Large number of rows scanned ({rows:,}) on table '{table_name}'")
                suggestions.append(
                    f"Table '{table_name}' is scanning {rows:,} rows. "
                    f"This indicates a potential performance bottleneck. "
                    f"Consider adding more selective indexes or refining your WHERE conditions."
                )

        if len(explain_plan) > 1:
            first_table_rows = explain_plan[0].get('rows', 0)
            if first_table_rows and first_table_rows > 1000:
                problems.append("Potential suboptimal join order")
                suggestions.append(
                    f"The first table in the join order scans {first_table_rows:,} rows. "
                    f"Consider reordering tables in your JOIN to start with the most selective table."
                )

        if not problems:
            suggestions.append("No obvious performance issues detected. Query appears to be well-optimized.")

        return problems, suggestions

    def format_rich_output(self, query: str, execution_time: float, row_count: int,
                          explain_plan: List[Dict[str, Any]], problems: List[str],
                          suggestions: List[str]):
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold cyan]SQL Query Performance Analysis Report[/bold cyan]",
            border_style="cyan"
        ))

        self.console.print("\n[bold yellow]Original Query:[/bold yellow]")
        self.console.print(f"[dim]{query}[/dim]\n")

        self.console.print(f"[bold green]Execution Time:[/bold green] {execution_time:.2f} ms")
        self.console.print(f"[bold green]Rows Returned:[/bold green] {row_count:,}\n")

        self.console.print("[bold yellow]EXPLAIN Plan:[/bold yellow]")
        if explain_plan:
            table = Table(show_header=True, header_style="bold magenta")

            headers = list(explain_plan[0].keys())
            for header in headers:
                table.add_column(header, style="cyan")

            for row in explain_plan:
                table.add_row(*[str(row.get(h, '')) for h in headers])

            self.console.print(table)

        self.console.print("\n[bold red]Problems Detected:[/bold red]")
        if problems:
            for problem in problems:
                self.console.print(f"  [red]⚠[/red]  {problem}")
        else:
            self.console.print("  [green]✓[/green] No issues found!")

        self.console.print("\n[bold blue]Optimization Suggestions:[/bold blue]")
        for idx, suggestion in enumerate(suggestions, 1):
            self.console.print(f"  [blue]{idx}.[/blue] {suggestion}")

        self.console.print("\n")

    def format_plain_output(self, query: str, execution_time: float, row_count: int,
                           explain_plan: List[Dict[str, Any]], problems: List[str],
                           suggestions: List[str]):
        print("\n" + "="*80)
        print("SQL QUERY PERFORMANCE ANALYSIS REPORT")
        print("="*80)

        print("\nOriginal Query:")
        print(f"  {query}\n")

        print(f"Execution Time: {execution_time:.2f} ms")
        print(f"Rows Returned: {row_count:,}\n")

        print("EXPLAIN Plan:")
        if explain_plan:
            headers = list(explain_plan[0].keys())
            col_widths = {h: max(len(h), max(len(str(row.get(h, ''))) for row in explain_plan))
                         for h in headers}

            header_line = " | ".join(h.ljust(col_widths[h]) for h in headers)
            print(f"  {header_line}")
            print("  " + "-" * len(header_line))

            for row in explain_plan:
                data_line = " | ".join(str(row.get(h, '')).ljust(col_widths[h]) for h in headers)
                print(f"  {data_line}")

        print("\nProblems Detected:")
        if problems:
            for problem in problems:
                print(f"  [WARNING] {problem}")
        else:
            print("  ✓ No issues found!")

        print("\nOptimization Suggestions:")
        for idx, suggestion in enumerate(suggestions, 1):
            print(f"  {idx}. {suggestion}")

        print("\n" + "="*80 + "\n")

    def analyze(self, query: str):
        try:
            execution_time, row_count = self.measure_execution_time(query)

            explain_plan = self.get_explain_plan(query)

            problems, suggestions = self.analyze_performance(explain_plan)

            if RICH_AVAILABLE:
                self.format_rich_output(query, execution_time, row_count,
                                       explain_plan, problems, suggestions)
            else:
                self.format_plain_output(query, execution_time, row_count,
                                        explain_plan, problems, suggestions)

        except Error as e:
            print(f"Error during analysis: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze MySQL query performance and provide optimization suggestions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python sql_analyzer.py --host localhost --user root --password secret \\
    --database mydb --query "SELECT * FROM users WHERE email LIKE '%@example.com'"
        """
    )

    parser.add_argument('--host', required=True, help='MySQL database host')
    parser.add_argument('--user', required=True, help='MySQL database username')
    parser.add_argument('--password', required=True, help='MySQL database password')
    parser.add_argument('--database', required=True, help='MySQL database name')
    parser.add_argument('--query', required=True, help='SQL query to analyze')

    args = parser.parse_args()

    analyzer = SQLAnalyzer(args.host, args.user, args.password, args.database)

    if not analyzer.connect():
        sys.exit(1)

    try:
        analyzer.analyze(args.query)
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
