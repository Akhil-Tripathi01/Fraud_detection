# Fraud Detection Platform

A full-stack financial fraud monitoring system built with FastAPI and React. The
project models payments, customers, merchants, and devices as a transaction
network so investigators can identify suspicious behavior, review alerts, and
analyze risk patterns from one dashboard.

## Project Overview

This application demonstrates a predictive fraud detection workflow for digital
financial transactions. The backend ingests seeded transaction data, evaluates
each transaction with a hybrid fraud scoring engine, and exposes APIs for
dashboards, alerts, graph analysis, and investigation workflows.

The frontend provides role-based views for administrators and investigators. It
includes dashboard summaries, transaction tables, fraud alerts, network graph
visualization, and transaction analysis screens.

## Key Features

- JWT-based authentication with admin and investigator demo users
- Transaction monitoring with customer, merchant, and device relationships
- Fraud risk scoring on a 0 to 100 scale
- Rule-based and behavioral fraud analysis
- Graph-based network modeling for connected fraud pattern discovery
- Real-time style fraud alert records from seeded demo transactions
- Investigator dashboard for reviewing suspicious activity
- Interactive React interface powered by a FastAPI backend

## How Fraud Detection Works

The system checks each transaction against behavioral and network signals such
as transaction amount, suspicious merchants, risky devices, unusual activity,
and connected customer behavior. These signals are converted into a fraud score
and risk category, helping investigators prioritize high-risk transactions.

The graph layer connects customers, merchants, devices, and transactions. This
makes it easier to detect patterns that are harder to see in a flat table, such
as multiple customers using the same flagged device or repeated payments to a
risky merchant.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite
- Frontend: React, Vite, React Router, Axios
- Graph analysis: NetworkX
- Styling: Tailwind CSS
- Authentication: JWT-based login flow

## Project Structure

```text
fraud_backend/
|-- main.py                    # FastAPI application entry point
|-- models.py                  # Database models
|-- schemas.py                 # API schemas
|-- fraud_engine.py            # Fraud scoring logic
|-- graph_builder.py           # Transaction graph utilities
|-- seed.py                    # Demo data seeding
|-- routes/                    # API route modules
|-- App.jsx                    # React app shell
|-- Dashboard.jsx              # Admin dashboard
|-- InvestigatorDashboard.jsx  # Investigator dashboard
|-- FraudAlerts.jsx            # Alert review screen
|-- Transactions.jsx           # Transaction list
`-- GraphNetwork.jsx           # Network graph view
```

## Run Locally

Install backend dependencies:

```powershell
pip install -r requirements.txt
```

Start the FastAPI server:

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

Install frontend dependencies and start Vite:

```powershell
npm install
npm run dev
```

Frontend: http://localhost:5173

Backend API docs: http://localhost:8001/docs

## Demo Login

```text
admin / admin123
investigator / password123
```

## API Areas

- `/auth` - login and authentication
- `/transactions` - transaction data and filtering
- `/fraud` - fraud scoring and alert APIs
- `/graph` - graph/network analysis
- `/dashboard` - dashboard summary data
- `/investigation` - investigator workflow endpoints

## Notes

The project includes local seed data for demo purposes. Runtime files such as
the SQLite database, logs, build output, Python cache files, and `node_modules`
are ignored by Git.
