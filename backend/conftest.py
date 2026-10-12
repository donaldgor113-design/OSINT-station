import sys
from pathlib import Path

# Make the `app` package importable regardless of the CWD pytest is run from.
sys.path.insert(0, str(Path(__file__).resolve().parent))
