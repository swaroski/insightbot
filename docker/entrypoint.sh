#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
python -c "
import time
import sys
from sqlalchemy import create_engine
from app.config import settings

max_retries = 30
for i in range(max_retries):
    try:
        engine = create_engine(settings.database_url)
        engine.connect()
        print('Database is ready!')
        break
    except Exception as e:
        print(f'Database not ready yet, retrying... ({i+1}/{max_retries})')
        time.sleep(2)
        if i == max_retries - 1:
            print('Could not connect to database')
            sys.exit(1)
"

# Create database tables
echo "Creating database tables..."
python -c "
from app.models.database import create_tables
create_tables()
print('Database tables created successfully!')
"

# Start supervisord
echo "Starting services..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf