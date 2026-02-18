I have a Jupyter notebook at `/workspace/process_data.ipynb` that works great on small test files, but when I try to run it on production CSVs (over 1GB), I keep getting MemoryError crashes.

The notebook reads sales data, does some cleaning and transforms, aggregates by category and date, then exports the results to CSV files. The problem is it's loading everything into memory at once - RAM usage just keeps climbing until it crashes. I need it to stay under 1GB peak memory even with 1GB+ files (so it must use chunking or streaming).

Could you help me optimize this notebook to be more memory-efficient? Maybe using chunking or some other technique? The output should be exactly the same, just more memory efficient.

The data files will be in `/workspace/data/` and outputs should go to `/workspace/output/`.

The notebook should generate these output files:
- `daily_summary.csv` - columns: `date`, `category`, `revenue`, `quantity`, `profit_margin`
- `monthly_summary.csv` - columns: `year`, `month`, `category`, `revenue`, `quantity`, `profit_margin`
- `category_summary.csv` - Category-level statistics (multi-level columns with sum/mean/std)
- `pivot_daily.csv` - Daily revenue pivot table by category
- `pivot_monthly.csv` - Monthly revenue pivot table by category
- `data_YYYY.csv` - columns: `order_id`, `date`, `category`, `year`, `month`, `revenue`, `profit_margin`, `tax`

**Note:** The notebook currently has the function call commented out at the bottom. Please uncomment it (or add the call) so the notebook actually processes `data/sales_data.csv` and outputs to the `output/` directory when executed.
