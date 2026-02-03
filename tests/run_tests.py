import unittest
import sys
import os

# Add the project root to path so we can import app and database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_all_tests():
    loader = unittest.TestLoader()
    # Discover all tests in this folder
    suite = loader.discover(start_dir='tests', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on success
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
