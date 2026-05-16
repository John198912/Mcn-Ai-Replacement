"""Pytest configuration."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

pytest_plugins = ["pytest_asyncio"]
