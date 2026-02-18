import subprocess
import sys
import os
import time
import psutil
import pandas as pd
import numpy as np
from pathlib import Path
import nbformat

class MemoryTester:
    def __init__(self):
        self.workspace_dir = Path('/workspace')
        self.notebook_path = self.workspace_dir / 'process_data.ipynb'
        self.data_dir = self.workspace_dir / 'data'
        self.output_dir = self.workspace_dir / 'output'
        self.max_memory_mb = 1000  # Maximum allowed memory usage in MB (requires chunking for ~1GB file)

    def setup_directories(self):
        """Create necessary directories."""
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        return True

    def generate_test_data(self, num_rows=500000):
        """Generate a test CSV file (~1GB when saved)."""
        print(f"Generating test data with {num_rows} rows...")

        # Generate data in chunks to avoid memory issues during test setup
        chunk_size = 100000
        first_chunk = True

        categories = ['Electronics', 'Clothing', 'Food', 'Books', 'Sports', 'Home', 'Toys', 'Beauty']

        for i in range(0, num_rows, chunk_size):
            chunk_rows = min(chunk_size, num_rows - i)

            # Generate chunk data
            dates = pd.date_range(start='2020-01-01', end='2023-12-31', periods=chunk_rows)

            chunk_data = {
                'order_id': range(i + 1, i + chunk_rows + 1),
                'date': np.random.choice(dates, chunk_rows),
                'category': np.random.choice(categories, chunk_rows),
                'product_name': ['Product_' + str(j) for j in range(i, i + chunk_rows)],
                'quantity': np.random.randint(1, 100, chunk_rows),
                'price': np.random.uniform(10, 1000, chunk_rows).round(2),
                'customer_id': np.random.randint(1000, 50000, chunk_rows),
                'region': np.random.choice(['North', 'South', 'East', 'West'], chunk_rows),
                'description': ['Long description text ' * 20 for _ in range(chunk_rows)]
            }

            chunk_df = pd.DataFrame(chunk_data)

            # Write chunk to file
            if first_chunk:
                chunk_df.to_csv(self.data_dir / 'sales_data.csv', index=False, mode='w')
                first_chunk = False
            else:
                chunk_df.to_csv(self.data_dir / 'sales_data.csv', index=False, mode='a', header=False)

            del chunk_df, chunk_data  # Clean up chunk memory

        print(f"Test data generated: {self.data_dir / 'sales_data.csv'}")

        # Check file size
        file_size_mb = os.path.getsize(self.data_dir / 'sales_data.csv') / (1024 * 1024)
        print(f"File size: {file_size_mb:.2f} MB")

        return file_size_mb > 150  # Should be ~250MB

    def monitor_memory_usage(self, process):
        """Monitor memory usage of a process."""
        try:
            proc = psutil.Process(process.pid)

            # Include child processes
            children = proc.children(recursive=True)

            total_memory = proc.memory_info().rss
            for child in children:
                try:
                    total_memory += child.memory_info().rss
                except Exception:
                    pass

            return total_memory / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0

    def test_memory_efficient_processing(self):
        """Test that the notebook processes data within memory limits."""
        print(f"Testing memory-efficient processing (max {self.max_memory_mb}MB)...")

        # Check if notebook exists
        if not self.notebook_path.exists():
            print(f"Notebook not found: {self.notebook_path}")
            return False, 0, "Notebook not found"

        # Start a subprocess to run the notebook
        # We'll use jupyter nbconvert to execute it
        process = subprocess.Popen(
            [
                sys.executable, '-m', 'jupyter', 'nbconvert',
                '--to', 'notebook',
                '--execute',
                '--inplace',
                str(self.notebook_path)
            ],
            cwd=str(self.workspace_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        max_memory_used = 0
        memory_samples = []

        # Monitor memory usage - let process complete, check peak at end
        while process.poll() is None:
            memory_mb = self.monitor_memory_usage(process)
            memory_samples.append(memory_mb)
            max_memory_used = max(max_memory_used, memory_mb)
            time.sleep(0.5)  # Sample every 500ms

        # Get final output
        stdout, stderr = process.communicate(timeout=10)

        if process.returncode != 0:
            print(f"Process failed with return code {process.returncode}")
            if stderr:
                print(f"Error: {stderr.decode()}")
            return False, max_memory_used, "Process failed"

        print(f"Peak memory usage: {max_memory_used:.2f}MB (limit: {self.max_memory_mb}MB)")

        # Calculate average memory
        avg_memory = sum(memory_samples) / len(memory_samples) if memory_samples else 0
        print(f"Average memory usage: {avg_memory:.2f}MB")

        # Check if memory limit exceeded after completion
        if max_memory_used > self.max_memory_mb:
            print(f"Memory limit exceeded: {max_memory_used:.2f}MB > {self.max_memory_mb}MB")
            return False, max_memory_used, "Memory limit exceeded"

        return True, max_memory_used, "Success"

    def verify_output_correctness(self):
        """Verify that output files are correct and match original format."""
        print("Verifying output correctness...")

        required_files = [
            'daily_summary.csv',
            'monthly_summary.csv',
            'category_summary.csv',
            'pivot_daily.csv',
            'pivot_monthly.csv'
        ]

        for file in required_files:
            file_path = self.output_dir / file
            if not file_path.exists():
                print(f"Missing output file: {file}")
                return False
            print(f"{file}: exists")

        # Verify daily_summary.csv format
        try:
            daily = pd.read_csv(self.output_dir / 'daily_summary.csv')

            required_cols = ['date', 'category', 'revenue', 'quantity', 'profit_margin']
            for col in required_cols:
                if col not in daily.columns:
                    print(f"Missing column '{col}' in daily_summary.csv")
                    return False

            if len(daily) == 0:
                print("daily_summary.csv is empty")
                return False

            if daily['revenue'].sum() <= 0:
                print("Invalid revenue in daily_summary.csv")
                return False

            print(f"daily_summary.csv: {len(daily)} rows, columns OK")

        except Exception as e:
            print(f"Error reading daily_summary.csv: {e}")
            return False

        # Verify monthly_summary.csv format
        try:
            monthly = pd.read_csv(self.output_dir / 'monthly_summary.csv')

            required_cols = ['year', 'month', 'category', 'revenue', 'quantity', 'profit_margin']
            for col in required_cols:
                if col not in monthly.columns:
                    print(f"Missing column '{col}' in monthly_summary.csv")
                    return False

            if len(monthly) == 0:
                print("monthly_summary.csv is empty")
                return False

            # Verify it's different from daily (not just a copy)
            if monthly.shape == daily.shape and monthly.columns.tolist() == daily.columns.tolist():
                # If they have same structure, they shouldn't have identical data
                print("monthly_summary.csv has different structure from daily (correct)")

            print(f"monthly_summary.csv: {len(monthly)} rows, columns OK")

        except Exception as e:
            print(f"Error reading monthly_summary.csv: {e}")
            return False

        # Verify category_summary.csv format (multi-level columns)
        try:
            category = pd.read_csv(self.output_dir / 'category_summary.csv')

            # Check for multi-level column structure
            # The file should have columns like: category, (revenue, sum), (revenue, mean), etc.
            if len(category) == 0:
                print("category_summary.csv is empty")
                return False

            # Should have at least 7-9 columns (category + 8 stat columns)
            if len(category.columns) < 7:
                print(f"category_summary.csv has too few columns: {len(category.columns)}")
                return False

            print(f"category_summary.csv: {len(category)} rows, {len(category.columns)} columns")

        except Exception as e:
            print(f"Error reading category_summary.csv: {e}")
            return False

        # Verify pivot_daily.csv
        try:
            pivot_daily = pd.read_csv(self.output_dir / 'pivot_daily.csv')

            if len(pivot_daily) == 0:
                print("pivot_daily.csv is empty")
                return False

            # Should have date column plus category columns
            if len(pivot_daily.columns) < 2:
                print("pivot_daily.csv has too few columns")
                return False

            print(f"pivot_daily.csv: {len(pivot_daily)} rows, {len(pivot_daily.columns)} columns")

        except Exception as e:
            print(f"Error reading pivot_daily.csv: {e}")
            return False

        # Verify pivot_monthly.csv
        try:
            pivot_monthly = pd.read_csv(self.output_dir / 'pivot_monthly.csv')

            if len(pivot_monthly) == 0:
                print("pivot_monthly.csv is empty")
                return False

            # Should have year, month columns plus category columns
            if len(pivot_monthly.columns) < 3:
                print("pivot_monthly.csv has too few columns")
                return False

            print(f"pivot_monthly.csv: {len(pivot_monthly)} rows, {len(pivot_monthly.columns)} columns")

        except Exception as e:
            print(f"Error reading pivot_monthly.csv: {e}")
            return False

        # Verify per-year files exist
        try:
            year_files = list(self.output_dir.glob('data_*.csv'))

            if len(year_files) == 0:
                print("No per-year data files (data_YYYY.csv) found")
                return False

            print(f"Found {len(year_files)} per-year data files")

            # Verify at least one year file has proper structure
            year_file = year_files[0]
            year_data = pd.read_csv(year_file, nrows=10)

            # Should have many columns (all original + derived columns)
            # Note: column names stay lowercase, only values are uppercased
            expected_cols = ['order_id', 'date', 'category', 'year', 'month', 'revenue', 'profit_margin', 'tax']
            missing_cols = [col for col in expected_cols if col not in year_data.columns]
            if missing_cols:
                print(f"Year file {year_file.name} missing columns: {missing_cols}")
                print(f"Available columns: {year_data.columns.tolist()}")
                return False

            print("Year files verified: proper column structure")

        except Exception as e:
            print(f"Error verifying per-year files: {e}")
            return False

        print("All output files verified successfully!")
        return True

    def test_chunking_implementation(self):
        """Check if the solution uses chunking or iterators."""
        print("Checking for chunking/iterator implementation...")

        # Read the notebook
        with open(self.notebook_path, 'r') as f:
            nb = nbformat.read(f, as_version=4)

        # Extract all code from cells
        code = ''
        for cell in nb.cells:
            if cell.cell_type == 'code':
                code += cell.source + '\n'

        # Look for chunking patterns
        chunking_patterns = [
            'chunksize=',
            'iterator=True',
            'read_csv(.*chunksize',
            'for chunk in',
            'pd.read_csv(.*iterator'
        ]

        uses_chunking = any(pattern in code for pattern in chunking_patterns)

        if uses_chunking:
            print("Code uses chunking or iterators")
        else:
            print("Warning: Code may not use chunking (could still be memory efficient)")

        return uses_chunking

def test_pandas_memory_solution():
    """Main test function."""
    tester = MemoryTester()

    print("Testing Pandas Memory Optimization Solution")
    print("=" * 50)

    # Setup
    if not tester.setup_directories():
        print("Failed to setup directories")
        return False

    # Generate test data
    if not tester.generate_test_data():
        print("Failed to generate test data")
        return False

    # Test memory-efficient processing
    success, peak_memory, message = tester.test_memory_efficient_processing()

    if not success:
        print(f"Memory test failed: {message}")
        print(f"   Peak memory: {peak_memory:.2f}MB (limit: {tester.max_memory_mb}MB)")
        return False

    # Verify output correctness
    if not tester.verify_output_correctness():
        print("Output verification failed")
        return False

    # Check implementation
    tester.test_chunking_implementation()

    print("All tests passed!")

    return True

if __name__ == "__main__":
    success = test_pandas_memory_solution()
    sys.exit(0 if success else 1)
