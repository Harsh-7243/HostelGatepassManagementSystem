#!/bin/bash
set -e  # Exit on error

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python db_init.py

# Start the application
exec gunicorn --bind 0.0.0.0:$PORT app:app