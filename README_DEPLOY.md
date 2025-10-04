# Spero Estimate - Users (Deploy Guide)

This document explains how to deploy the Spero Estimate app with user management on GitHub and Render.

1. Extract the project folder.
2. Initialize git and push to your GitHub (see scripts provided).
3. On Render create a new Web Service from the repository.
4. Use build command: pip install -r requirements.txt
5. Use start command: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
6. Add custom domain speroestimate.com via Render UI and follow DNS instructions in config/domain.txt
