# NexusBank Python Full-Stack Banking Demo

Flask REST API + React/Vite frontend. Local SQLite; PostgreSQL-ready via DATABASE_URL. JWT authentication, password hashing, account balance, transactions and demo transfers.

## Run backend
`cd backend` then `python -m venv .venv`, activate it, `pip install -r requirements.txt`, and `python app.py`.

## Run frontend
`cd frontend`, `npm install`, `npm run dev`. Set `VITE_API_URL` to the backend API when deployed.

## Azure App Service
Deploy backend to a Linux Python App Service. Startup: `gunicorn --bind=0.0.0.0:8000 app:app`. Set SECRET_KEY, DATABASE_URL and FRONTEND_ORIGIN in App Service environment variables. Deploy frontend separately and set VITE_API_URL to the backend URL. Enable HTTPS-only, monitoring and production database/network security.

This is a portfolio/demo banking application, not a production financial system. Real banking systems need MFA, strong authorization, audit logging, rate limiting, fraud controls, transaction idempotency/locking, encryption, compliance and extensive security testing.
