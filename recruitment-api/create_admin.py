"""Compatibility entry point for the shared administrator bootstrap script."""
import runpy
from pathlib import Path


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "scripts" / "create_admin.py"), run_name="__main__")
