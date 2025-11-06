#!/bin/bash
#
# Run: ./sherloc.sh [--install] [--nosudo]
#
# Sets up the environment for Sherloc to run. 
# Creates a new virtual environment, activates, and installs requirements.
# Then, runs Sherloc.
# Deactivates afterward.

VENV="sherloc-venv"

# Check for --install and --notsudo arguments
INSTALL_REQS=false
USE_SUDO=true
for arg in "$@"; do
    if [[ "$arg" == "--install" ]]; then
        INSTALL_REQS=true
        break
    elif  [[ "$arg" == "--nosudo" ]]; then
        USE_SUDO=false
        break
    fi
done

# Create virtual environment if not exists
if [ ! -d $VENV ]; then
    echo "🐍 Creating virtual environment ($VENV)..."
    virtualenv $VENV
    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        echo "Oops, need to install virtualenv first. Installing..."
        pip install virtualenv
        virtualenv $VENV
    fi
fi

# Activate the virtual environment
source $VENV/bin/activate
echo "✅ Activated $VENV"

# Install requirements if requested
if $INSTALL_REQS; then
    echo "📦 Installing requirements..."
    pip install -r requirements.txt
fi

# Create log folder if needed
if [ ! -d "../logs" ]; then
    echo "📁 Creating log folder..."
    mkdir ../logs
fi

# Create data folder if needed
if [ ! -d "./data" ]; then
    echo "📁 Creating data folder..."
    mkdir ./data
fi

# Create screenshots folder if needed
if [ ! -d "./webstatic/images/screenshots" ]; then
    echo "📁 Creating screenshots folder..."
    mkdir ./webstatic/images/screenshots
fi

if $USE_SUDO; then
    echo "🚀 Launching Sherloc with sudo..."
    sudo python3 main.py
    EXIT_CODE=$?
    echo "=================================================="
else
    echo "🚀 Launching Sherloc..."
    echo "=================================================="
    python3 main.py
    EXIT_CODE=$?
fi

# If it failed due to missing packages, try installing requirements
if [ $EXIT_CODE -ne 0 ]; then
    echo "=================================================="
    echo "⚠️ Sherloc failed to launch. Attempting to install missing requirements..."
    pip install -r requirements.txt
    echo "🔁 Retrying launch..."
    if $USE_SUDO; then
        sudo python3 main.py
        EXIT_CODE=$?
        echo "=================================================="
    else
        python3 main.py
        EXIT_CODE=$?
        echo "=================================================="
    fi
fi

echo "=================================================="

deactivate
echo "👋 Deactivated $VENV"

