"""
Set up the workspace for the pandas-memory-optimization-colab task.

1. Installs required dependencies (psutil, jupyter, nbformat, nbconvert, ipykernel).
2. Creates /workspace/data/ and /workspace/output/ directories.
3. Writes the original (non-chunked, broken) notebook to /workspace/process_data.ipynb.
   The notebook loads the entire CSV into memory at once, causing MemoryError on large files.
   The agent must rewrite it to use chunked reading and stay under 1GB peak memory.
"""
import subprocess
import sys
import os
import json

subprocess.run(
    [sys.executable, "-m", "pip", "install",
     "psutil", "jupyter", "nbformat", "nbconvert", "ipykernel", "--quiet"],
    check=True,
)

os.makedirs("/workspace/data", exist_ok=True)
os.makedirs("/workspace/output", exist_ok=True)

# The original broken notebook — loads all data at once, function call commented out.
# Agent must rewrite it to use chunking and uncomment/add the function call.
BROKEN_NOTEBOOK = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Sales Data Processing\n",
                "\n",
                "This notebook reads sales data, cleans and transforms it, aggregates by category and date, and exports results to CSV files."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd\n",
                "import numpy as np\n",
                "import os\n",
                "import gc\n",
                "from collections import defaultdict\n",
                "\n",
                "def sum_sq(x):\n",
                "    return (x**2).sum()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "def process_sales_data(input_file, output_dir):\n",
                "    \"\"\"Process sales CSV. Loads entire file into memory — causes MemoryError on large files.\"\"\"\n",
                "\n",
                "    print(f\"Loading {input_file}...\")\n",
                "\n",
                "    # BUG: loads the entire file at once — will OOM on files > ~500MB\n",
                "    df = pd.read_csv(input_file)\n",
                "    total_rows = len(df)\n",
                "    print(f\"Loaded {total_rows} rows\")\n",
                "\n",
                "    # Parse dates and derive columns\n",
                "    df['date'] = pd.to_datetime(df['date'])\n",
                "    df['year'] = df['date'].dt.year\n",
                "    df['month'] = df['date'].dt.month\n",
                "    df['revenue'] = df['quantity'] * df['price']\n",
                "    df['profit_margin'] = df['revenue'] * 0.3\n",
                "    df['tax'] = df['revenue'] * 0.1\n",
                "\n",
                "    print(\"Writing output files...\")\n",
                "    os.makedirs(output_dir, exist_ok=True)\n",
                "\n",
                "    # Daily summary\n",
                "    daily_summary = df.groupby(['date', 'category']).agg(\n",
                "        revenue=('revenue', 'sum'),\n",
                "        quantity=('quantity', 'sum'),\n",
                "        profit_margin=('profit_margin', 'mean')\n",
                "    ).reset_index()\n",
                "    daily_summary.to_csv(os.path.join(output_dir, 'daily_summary.csv'), index=False)\n",
                "\n",
                "    # Monthly summary\n",
                "    monthly_summary = df.groupby(['year', 'month', 'category']).agg(\n",
                "        revenue=('revenue', 'sum'),\n",
                "        quantity=('quantity', 'sum'),\n",
                "        profit_margin=('profit_margin', 'mean')\n",
                "    ).reset_index()\n",
                "    monthly_summary.to_csv(os.path.join(output_dir, 'monthly_summary.csv'), index=False)\n",
                "\n",
                "    # Category summary (multi-level columns)\n",
                "    category_summary = df.groupby('category').agg(\n",
                "        revenue=('revenue', ['sum', 'mean', 'std']),\n",
                "        quantity=('quantity', ['sum', 'mean', 'std']),\n",
                "        profit_margin=('profit_margin', ['mean', 'std'])\n",
                "    )\n",
                "    category_summary.to_csv(os.path.join(output_dir, 'category_summary.csv'))\n",
                "\n",
                "    # Pivot tables\n",
                "    pivot_daily = daily_summary.pivot_table(\n",
                "        values='revenue', index='date', columns='category', aggfunc='sum', fill_value=0\n",
                "    )\n",
                "    pivot_daily.to_csv(os.path.join(output_dir, 'pivot_daily.csv'))\n",
                "\n",
                "    pivot_monthly = monthly_summary.pivot_table(\n",
                "        values='revenue', index=['year', 'month'], columns='category', aggfunc='sum', fill_value=0\n",
                "    )\n",
                "    pivot_monthly.to_csv(os.path.join(output_dir, 'pivot_monthly.csv'))\n",
                "\n",
                "    # Per-year files\n",
                "    for year, group in df.groupby('year'):\n",
                "        cols = ['order_id', 'date', 'category', 'year', 'month', 'revenue', 'profit_margin', 'tax']\n",
                "        group[cols].to_csv(os.path.join(output_dir, f'data_{year}.csv'), index=False)\n",
                "\n",
                "    print(f\"Done. Output saved to {output_dir}\")\n",
                "    return {\n",
                "        'total_rows': total_rows,\n",
                "        'total_revenue': df['revenue'].sum(),\n",
                "        'unique_categories': df['category'].nunique(),\n",
                "        'date_range': f\"{df['date'].min()} to {df['date'].max()}\"\n",
                "    }"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Main execution — currently commented out, uncomment to run\n",
                "# results = process_sales_data('data/sales_data.csv', 'output')\n",
                "# print(f\"Results: {results}\")"
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

notebook_path = "/workspace/process_data.ipynb"
with open(notebook_path, "w") as f:
    json.dump(BROKEN_NOTEBOOK, f, indent=1)

print(f"Written broken notebook → {notebook_path}")
print("Workspace ready: /workspace/data/ and /workspace/output/ created")
