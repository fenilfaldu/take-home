import subprocess
import sys

def test_pandas_memory_optimization():
    """Test that the pandas memory optimization solution works."""
    # Run the actual test script
    result = subprocess.run(
        [sys.executable, '/tests/test_memory_optimization.py'],
        capture_output=True,
        text=True,
        timeout=360
    )

    # Print the output for debugging
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print("STDERR:", result.stderr)

    # Check if the test passed
    assert result.returncode == 0, "Memory optimization test failed"
    assert "All tests passed!" in result.stdout, "Not all tests passed"
