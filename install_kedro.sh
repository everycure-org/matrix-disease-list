#!/bin/bash

# Function to check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
}

# Function to check if pip is installed
check_pip() {
    if ! command -v pip3 &> /dev/null; then
        echo "pip3 is not installed. Installing pip3..."
        if command -v apt &> /dev/null; then
            sudo apt update
            sudo apt install -y python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-pip
        else
            echo "Could not install pip3. Please install it manually."
            exit 1
        fi
    fi
}

# Function to check if virtual environment module is installed
check_venv() {
    if ! python3 -c "import venv" &> /dev/null; then
        echo "Python venv module is not installed. Installing venv..."
        if command -v apt &> /dev/null; then
            sudo apt update
            sudo apt install -y python3-venv
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-venv
        else
            echo "Could not install venv. Please install it manually."
            exit 1
        fi
    fi
}

# Function to check if Kedro is installed
check_kedro() {
    if ! command -v kedro &> /dev/null; then
        echo "Kedro is not installed. Installing Kedro..."
        
        # Create a virtual environment if it doesn't exist
        if [ ! -d "kedro_env" ]; then
            echo "Creating virtual environment..."
            python3 -m venv kedro_env
        fi
        
        # Activate virtual environment
        source kedro_env/bin/activate
        
        # Upgrade pip
        pip3 install --upgrade pip
        
        # Install Kedro
        pip3 install kedro
        
        if [ $? -eq 0 ]; then
            echo "Kedro has been successfully installed in the virtual environment."
            echo "To use Kedro, activate the virtual environment with:"
            echo "source kedro_env/bin/activate"
        else
            echo "Failed to install Kedro. Please try installing it manually."
            exit 1
        fi
    else
        echo "Kedro is already installed."
        kedro --version
    fi
}

# Main execution
echo "Checking dependencies..."
check_python
check_pip
check_venv
check_kedro