"""
Run the Phase 8 Streamlit frontend.

Usage: streamlit run phase8_frontend/app.py
Or: python -m phase8_frontend.run_ui
"""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).resolve().parent / "app.py"
    sys.exit(subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port=8501"] + sys.argv[1:]).returncode)
