from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base
from routers import telemetry, poles, tickets, simulator, scheduled_outages
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Seed database with initial data
    logger.info("Seeding database...")
    from seed import seed_database
    await seed_database()
    logger.info("Database seeding complete")
    
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="KSPDB Fault Detection System",
    description="Real-time fault detection and localization for power distribution network",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry"])
app.include_router(poles.router, prefix="/api/poles", tags=["poles"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["tickets"])
app.include_router(simulator.router, prefix="/api/simulator", tags=["simulator"])
app.include_router(scheduled_outages.router, prefix="/api/scheduled-outages", tags=["scheduled-outages"])


@app.get("/")
async def root():
    return {
        "message": "KSPDB Fault Detection System API",
        "status": "operational",
        "endpoints": {
            "telemetry": "/api/telemetry",
            "poles": "/api/poles",
            "tickets": "/api/tickets",
            "simulator": "/api/simulator",
            "scheduled-outages": "/api/scheduled-outages"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
