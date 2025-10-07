#!/bin/bash
set -e  # Exit on error

# Initialize the database
python db_init.py

# Start the application
exec gunicorn --bind 0.0.0.0:$PORT app:app