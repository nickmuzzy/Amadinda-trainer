#!/bin/bash
# Simple script to run the Amadinda Trainer

# Activate the virtual environment and run the Python script directly
# This avoids all packaging issues and works reliably

echo "Starting Amadinda Trainer..."
cd "$(dirname "$0")"
source amadinda_env/bin/activate
python3 amadinda_trainer.py 