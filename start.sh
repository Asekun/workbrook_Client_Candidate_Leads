#!/bin/bash
cd /root/workbrook_Client_Candidate_Leads/
source venv/bin/activate
exec uvicorn main:app --host 0.0.0.0 --port 8005