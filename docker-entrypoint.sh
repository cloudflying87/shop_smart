#!/bin/bash
set -e

# Create required media directories with appropriate permissions
mkdir -p /app/media/store_logos
chmod -R 777 /app/media

# Start Gunicorn
exec gunicorn --bind 0.0.0.0:8000 --workers 3 shop_smart.wsgi:application