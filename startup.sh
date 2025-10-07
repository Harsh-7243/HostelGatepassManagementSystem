#!/bin/bash

# Initialize the database
python db_init.py

# Start the application
gunicorn --bind 0.0.0.0:$PORT app:app
