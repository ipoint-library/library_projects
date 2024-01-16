#!/bin/bash

# Change cwd to the directory of the script
cd "$(dirname "${BASH_SOURCE[0]}")"

# Check if Python is installed
if command -v python3 &>/dev/null; then
    :
else
    echo "Error: Python is not installed. Please install Python."
    exit 1
fi

# Create a virtual environment named "image_handler"
python3 -m venv image_handler

# Activate the virtual environment
source image_handler/bin/activate

# Upgrade pip and ignore installation errors
pip install --upgrade pip || true

# Install dependencies from "requirements.txt" ignoring errors
pip install -r requirements.txt || true

# Execute the "main.py" script
python scripts/main.py

# Deactivate the virtual environment
deactivate
