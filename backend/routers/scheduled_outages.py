from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import ScheduledOutage
from datetime import datetime
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_scheduled_outages(
    from_date: datetime,
    to_date: datetime,
    db: Session = Depends(get_db)
):
    """
    Get scheduled outages for a time range.
    This mocks the department's scheduled outage feed.
    """
    outages = db.query(ScheduledOutage).filter(
        ScheduledOutage.start >= from_date,
        ScheduledOutage.end <= to_date
    ).all()
    
    return [
        {
            "id": outage.outage_id,
            "scope": outage.scope,
            "target_id": outage.target_id,
            "start": outage.start,
            "end": outage.end,
            "reason": outage.reason
        }
        for outage in outages
    ]


@router.post("/seed")
async def seed_scheduled_outages(db: Session = Depends(get_db)):
    """Seed sample scheduled outages for testing."""
    sample_outages = [
        ScheduledOutage(
            outage_id="SO-2026-08-06-001",
            scope="feeder",
            target_id="F-07-03",
            start=datetime(2026, 8, 6, 10, 0, 0),
            end=datetime(2026, 8, 6, 12, 30, 0),
            reason="Planned maintenance - jumper replacement"
        ),
        ScheduledOutage(
            outage_id="SO-2026-08-06-002",
            scope="dt",
            target_id="D-0112",
            start=datetime(2026, 8, 6, 14, 0, 0),
            end=datetime(2026, 8, 6, 15, 0, 0),
            reason="Load shedding"
        )
    ]
    
    for outage in sample_outages:
        db.add(outage)
    
    db.commit()
    logger.info(f"Seeded {len(sample_outages)} scheduled outages")
    return {"message": f"Seeded {len(sample_outages)} scheduled outages"}
