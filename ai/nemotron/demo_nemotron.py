#!/usr/bin/env python3
"""Convenience runner for SentraFlow's NVIDIA Nemotron Integration Demo."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    demo_script = Path(__file__).resolve().parent.parent.parent / "examples" / "run_nemotron_demo.py"
    python_bin = Path(__file__).resolve().parent.parent.parent / "backend" / ".venv" / "bin" / "python3"
    
    executable = str(python_bin) if python_bin.exists() else sys.executable
    sys.exit(subprocess.call([executable, str(demo_script)]))
