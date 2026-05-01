"""
Predictive Financial Fraud Detection Using Behavioral Graph Learning
Main FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from database import engine, Base
from routes import auth, transactions, fraud, graph, dashboard, investigation
from seed import seed_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("🚀 Starting Fraud Detection Platform...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created.")
    seed_database()
    logger.info("✅ Seed data loaded.")
    yield
    logger.info("🛑 Shutting down Fraud Detection Platform...")


app = FastAPI(
    title="Predictive Financial Fraud Detection API",
    description="""
## Behavioral Graph Learning for Financial Fraud Detection

This platform models financial transactions as **dynamic graphs** and detects 
suspicious fraud patterns using behavioral graph learning techniques.

### Key Features
- 🔐 JWT-based authentication
- 📊 Transaction graph modeling (NetworkX)
- 🤖 Hybrid fraud scoring engine (Rule-based + ML anomaly detection)
- 🔍 Graph-based pattern detection
- 📈 Risk scoring (0–100 scale)
- 🚨 Real-time fraud alerts
- 🧑‍💼 Investigator dashboard APIs

### Risk Categories
| Score | Category |
|-------|----------|
| 0–30  | 🟢 Low Risk |
| 31–70 | 🟡 Medium Risk |
| 71–100| 🔴 High Risk |
    """,
    version="1.0.0",
    contact={"name": "FinTech Fraud Detection Team"},
    lifespan=lifespan,
)

# CORS Middleware — allows frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ────────────────────────────────────────────────────────
app.include_router(auth.router,          prefix="/auth",          tags=["Authentication"])
app.include_router(transactions.router,  prefix="/transactions",  tags=["Transactions"])
app.include_router(fraud.router,         prefix="/fraud",         tags=["Fraud Detection"])
app.include_router(graph.router,         prefix="/graph",         tags=["Graph Analysis"])
app.include_router(dashboard.router,     prefix="/dashboard",     tags=["Dashboard"])
app.include_router(investigation.router, prefix="/investigation", tags=["Investigation"])


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "status": "operational",
        "platform": "Predictive Financial Fraud Detection",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "database": "up",
            "graph_engine": "up",
            "fraud_engine": "up",
        },
    }
