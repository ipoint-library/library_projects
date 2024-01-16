#!/bin/bash

# Function to check if a command is available
is_command_available() {
    command -v "$1" &> /dev/null
}

# Install or update Homebrew
if ! is_command_available "brew"; then
    echo "Homebrew is not installed. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew is already installed. Updating Homebrew..."
    brew update
fi

# Function to check if a package is installed
is_package_installed() {
    brew list --formula "$1" &> /dev/null
}

# List of required packages
required_packages=("python")

# Check if required packages are installed
missing_packages=()
for package in "${required_packages[@]}"; do
    if ! is_package_installed "$package"; then
        missing_packages+=("$package")
    fi
done

# Install missing packages using Homebrew
if [ ${#missing_packages[@]} -gt 0 ]; then
    echo "Installing required packages..."
    brew install "${missing_packages[@]}"
fi

# Check if pip is installed
if ! is_command_available "pip"; then
    echo "pip is not installed. Installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    rm get-pip.py
fi

# Install python-tk package using Homebrew
if ! is_package_installed "python-tk"; then
    echo "Installing python-tk package..."
    brew install python-tk
fi

# Install required Python packages using pip
echo "Installing Python packages..."
pip install boto3

# Get the directory path of the shell script
script_directory=$(dirname "$0")

# Execute the Python script
echo "Running the Python script..."
python3 "$script_directory/Wasabi_Uploader.py"
