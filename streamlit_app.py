# streamlit_app.py
"""Streamlit entry point forwarding to dashboard/app.py."""
import runpy
from pathlib import Path

dashboard_file = Path(__file__).resolve().parent / "dashboard" / "app.py"
runpy.run_path(str(dashboard_file), run_name="__main__")