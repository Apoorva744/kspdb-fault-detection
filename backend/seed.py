from database import SessionLocal, Base, engine
from models import Transformer, Pole, Telemetry, ScheduledOutage
from services.simulator import FaultSimulator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_database():
    """Seed the database with initial data."""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_poles = db.query(Pole).first()
        if existing_poles:
            logger.info("Database already seeded, skipping...")
            return
        
        logger.info("Seeding database with synthetic network...")
        
        simulator = FaultSimulator()
        import asyncio
        
        # Generate network
        result = asyncio.run(simulator.generate_network(num_transformers=20, poles_per_dt=70, db=db))
        logger.info(f"Generated network: {result}")
        
        # Seed scheduled outages
        sample_outages = [
            ScheduledOutage(
                outage_id="SO-2026-08-06-001",
                scope="feeder",
                target_id="F-00-00",
                start=None,  # Will be set dynamically
                end=None,
                reason="Planned maintenance - jumper replacement"
            ),
            ScheduledOutage(
                outage_id="SO-2026-08-06-002",
                scope="dt",
                target_id="D-0000",
                start=None,
                end=None,
                reason="Load shedding"
            )
        ]
        
        # Set dates to future to avoid interfering with initial testing
        from datetime import datetime, timedelta
        future_start = datetime.utcnow() + timedelta(days=1)
        future_end = future_start + timedelta(hours=2)
        
        for outage in sample_outages:
            outage.start = future_start
            outage.end = future_end
            db.add(outage)
        
        db.commit()
        logger.info("Database seeding completed successfully")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
