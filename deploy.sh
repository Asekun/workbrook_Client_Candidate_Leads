#!/bin/bash

DOMAIN_NAME="scraper.yourdomain.com"
APP_DIRECTORY="workbrook_Client_Candidate_Leads/"

# Step 1: Change directory
cd "/root/$APP_DIRECTORY"

# Step 2: Git Pull
sudo git pull

# Step 3: Activate virtual environment
source venv/bin/activate

# Step 4: Install Python dependencies
pip install -r requirements.txt

# Step 5: Start the app
uvicorn main:app --host 0.0.0.0 --port 8005

# Step 6: Deployment Complete
echo "$DOMAIN_NAME redeployment completed" 