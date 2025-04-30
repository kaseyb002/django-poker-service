#!/bin/bash

# Set working directory
cd ~/django-poker-service/ || exit

# Pull latest code from Git
echo "Pulling latest code..."
git pull origin main

# Remove and recreate virtual environment
echo "Recreating virtual environment..."
rm -rf env/
python3 -m venv env

# Activate virtual environment
echo "Activating virtual environment..."
source env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install firebase-admin django-allauth dj-rest-auth # Manual install
pip install "uvicorn[standard]"  # Manual install

# Run migrations
echo "Running migrations..."
python poker/manage.py migrate

# Restart services
echo "Restarting services..."
sudo systemctl restart gunicorn
sudo systemctl restart uvicorn

# Deactivate virtual environment
echo "Deactivating virtual environment..."
deactivate

echo "Deployment complete!"
