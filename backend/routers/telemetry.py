from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import Telemetry, Pole
from schemas import TelemetryCreate, TelemetryResponse
from services.fault_detector import FaultDetector
from services.telemetry_processor import TelemetryProcessor
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
fault_detector = FaultDetector()
telemetry_processor = TelemetryProcessor()


@router.post("/", response_model=TelemetryResponse)
async def ingest_telemetry(
    telemetry: TelemetryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Ingest telemetry from pole devices.
    Handles duplicates, out-of-order messages, and triggers fault detection.
    """
    # Check for duplicates using device_id and seq
    existing = db.query(Telemetry).filter(
        Telemetry.device_id == telemetry.device_id,
        Telemetry.seq == telemetry.seq
    ).first()
    
    if existing:
        logger.info(f"Duplicate telemetry ignored: device={telemetry.device_id}, seq={telemetry.seq}")
        return TelemetryResponse.from_orm(existing)
    
    # Create new telemetry record
    db_telemetry = Telemetry(
        device_id=telemetry.device_id,
        pole_id=telemetry.pole_id,
        event=telemetry.event,
        energized=telemetry.energized,
        ts=telemetry.ts,
        seq=telemetry.seq,
        battery_mv=telemetry.battery_mv,
        rssi=telemetry.rssi,
        fw=telemetry.fw
    )
    
    db.add(db_telemetry)
    db.commit()
    db.refresh(db_telemetry)
    
    # Schedule fault detection in background
    background_tasks.add_task(
        telemetry_processor.process_telemetry,
        db_telemetry.pole_id,
        db
    )
    
    logger.info(f"Telemetry ingested: device={telemetry.device_id}, event={telemetry.event}")
    return TelemetryResponse.from_orm(db_telemetry)


@router.get("/pole/{pole_id}", response_model=list[TelemetryResponse])
async def get_pole_telemetry(
    pole_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get recent telemetry for a specific pole."""
    telemetry = db.query(Telemetry).filter(
        Telemetry.pole_id == pole_id
    ).order_by(Telemetry.ts.desc()).limit(limit).all()
    
    return [TelemetryResponse.from_orm(t) for t in telemetry]


@router.get("/device/{device_id}", response_model=list[TelemetryResponse])
async def get_device_telemetry(
    device_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get recent telemetry for a specific device."""
    telemetry = db.query(Telemetry).filter(
        Telemetry.device_id == device_id
    ).order_by(Telemetry.ts.desc()).limit(limit).all()
    
    return [TelemetryResponse.from_orm(t) for t in telemetry]
