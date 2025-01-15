#!/bin/bash

# Set error handling
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Ollama is installed
check_ollama() {
    if command_exists ollama; then
        log_info "Ollama is already installed"
        return 0
    else
        log_info "Ollama is not installed"
        return 1
    fi
}

# Install Ollama based on OS
install_ollama() {
    local os_type
    os_type=$(uname -s)

    case "$os_type" in
        "Darwin")
            if command_exists brew; then
                log_info "Installing Ollama using Homebrew..."
                brew install ollama
            else
                log_error "Homebrew is required but not installed. Please install Homebrew first."
                exit 1
            fi
            ;;
        "Linux")
            log_info "Installing Ollama using the official install script..."
            curl -fsSL https://ollama.ai/install.sh | sh
            ;;
        *)
            log_error "Unsupported operating system: $os_type"
            exit 1
            ;;
    esac
}

# Check if a model is installed
check_model() {
    local model_name="$1"
    if ollama list | grep -q "$model_name"; then
        log_info "Model $model_name is already installed"
        return 0
    else
        log_info "Model $model_name is not installed"
        return 1
    fi
}

# Install a model
install_model() {
    local model_name="$1"
    log_info "Installing model $model_name..."
    ollama pull "$model_name"
}

# Start Ollama service if not running
ensure_ollama_running() {
    # Check if Ollama service is running
    if ! pgrep -f "ollama serve" >/dev/null; then
        log_info "Starting Ollama service..."
        ollama serve >/dev/null 2>&1 &
        # Wait for service to start
        sleep 5
    fi
}

# Main execution
main() {
    log_info "Starting Ollama setup..."

    # Check and install Ollama if needed
    if ! check_ollama; then
        log_info "Installing Ollama..."
        install_ollama
    fi

    # Ensure Ollama service is running
    ensure_ollama_running

    # Model to install
    local model_name="llama3.1"

    # Check and install model if needed
    if ! check_model "$model_name"; then
        log_info "Installing $model_name model..."
        install_model "$model_name"
    fi

    log_info "Setup completed successfully!"
}

# Execute main function
main