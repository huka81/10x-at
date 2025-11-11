"""Pytest configuration file."""
import sys
from pathlib import Path

# Add the project root and python directory to Python path
project_root = Path(__file__).parent
python_dir = project_root / "python"

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(python_dir))
