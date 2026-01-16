#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
python -c "from db import get_conn; get_conn()" || exit 1

# Run database migrations if needed
# python migrate.py

# Start the application
gunicorn app_api:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
