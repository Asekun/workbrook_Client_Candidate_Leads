#!/bin/bash

DOMAIN_NAME="lead.workbrook.us"
APP_DIRECTORY="workbrook_Client_Candidate_Leads/"

# Step 1: Change directory
cd "/root/$APP_DIRECTORY" || exit

# Step 2: Git Pull
sudo git pull

# Step 3: Activate virtual environment
source venv/bin/activate

# Step 4: Install Python dependencies
pip install -r requirements.txt

# Step 5: Get the full path to the virtual environment's Python and uvicorn
VENV_PYTHON=$(which python3)
VENV_UVICORN=$(which uvicorn)

echo "Using Python: $VENV_PYTHON"
echo "Using uvicorn: $VENV_UVICORN"

# Step 6: Restart app with PM2
# If first time, use 'start', otherwise 'restart'
pm2 describe workbrook-leads >/dev/null 2>&1
RUNNING=$?

if [ $RUNNING -ne 0 ]; then
    # First time deployment
    pm2 start "$VENV_UVICORN" \
        --name workbrook-leads \
        --interpreter "$VENV_PYTHON" \
        -- main:app --host 0.0.0.0 --port 8005
else
    # Restart existing process
    pm2 restart workbrook-leads
fi

# Step 7: Save PM2 state
pm2 save

# Step 8: Show status
pm2 show workbrook-leads

# Step 9: Deployment Complete
echo "$DOMAIN_NAME redeployment completed"