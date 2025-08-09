# #!/bin/bash

# DOMAIN_NAME="lead.workbrook.us"
# APP_DIRECTORY="workbrook_Client_Candidate_Leads/"

# # Step 1: Change directory
# cd "/root/$APP_DIRECTORY"

# # Step 2: Git Pull
# sudo git pull
# # Step 3: Activate virtual environment
# source venv/bin/activate

# # Step 4: Install Python dependencies
# pip install -r requirements.txt

# # Step 5: Start the app
# uvicorn main:app --host 0.0.0.0 --port 8005

# # Step 6: Deployment Complete
# echo "$DOMAIN_NAME redeployment completed" 


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

# Step 5: Restart app with PM2
# If first time, use 'start', otherwise 'restart'
pm2 describe workbrook-leads >/dev/null
RUNNING=$?

if [ $RUNNING -ne 0 ]; then
    pm2 start "venv/bin/uvicorn main:app --host 0.0.0.0 --port 8005" \
    --name workbrook-leads \
    --interpreter bash
else
    pm2 restart workbrook-leads
fi

# Step 6: Save PM2 state
pm2 save

# Step 7: Deployment Complete
echo "$DOMAIN_NAME redeployment completed"
