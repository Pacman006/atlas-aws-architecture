"""Runs without AWS credentials, a database, or built React assets."""
import sys
import types
import unittest
from pathlib import Path

# Local CI should install dependencies before running these tests. A no-dependency
# syntax check is provided separately in scripts/static-check.py.
class SourceContract(unittest.TestCase):
    def test_application_compiles(self):
        path = Path(__file__).resolve().parents[1] / 'backend' / 'application.py'
        compile(path.read_text(), str(path), 'exec')

    def test_secure_defaults_are_present(self):
        text = (Path(__file__).resolve().parents[1] / 'backend' / 'application.py').read_text()
        for required in ('Cache-Control', 'X-Content-Type-Options', 'Content-Security-Policy',
                         "@application.get('/health')", "@application.get('/api/status')"):
            self.assertIn(required, text)


if __name__ == '__main__':
    unittest.main()
