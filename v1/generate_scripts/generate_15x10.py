#!/usr/bin/env python3
"""Quick script to generate 15cm box"""
import subprocess
import sys

# Prepare inputs for 150mm box
inputs = [
    "",  # Stock width (default 600)
    "",  # Stock height (default 600)
    "",  # Material thickness (default 3.0)
    "150",  # Box side length (15cm)
    "100",  # Box height (10cm)
    "",  # Include divider (default yes)
    "",  # Divider position (default 0.5)
    "n",  # Screws (disable)
    "",  # Fractal (default yes)
    "",  # Lid (default yes)
    "",  # Text on base (default DIGITAL MANUFACTURING)
    "",  # Text on bottom (default LORENZO | DIANE)
    "",  # Logo (default no)
]

# Run box_generator.py with inputs
input_str = "\n".join(inputs) + "\n"
result = subprocess.run(
    ["python3", "box_generator.py"],
    input=input_str,
    text=True,
    capture_output=True
)

print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)
