from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Pole, Transformer, Telemetry
from schemas import PoleResponse, TransformerResponse
from typing import List, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[PoleResponse])
async def get_all_poles(
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """Get all poles with pagination."""
    poles = db.query(Pole).offset(skip).limit(limit).all()
    return [PoleResponse.from_orm(p) for p in poles]


@router.get("/{pole_id}", response_model=PoleResponse)
async def get_pole(pole_id: str, db: Session = Depends(get_db)):
    """Get a specific pole by ID."""
    pole = db.query(Pole).filter(Pole.pole_id == pole_id).first()
    if not pole:
        raise HTTPException(status_code=404, detail="Pole not found")
    
    # Add current energized status
    latest_telemetry = db.query(Telemetry).filter(
        Telemetry.pole_id == pole_id
    ).order_by(Telemetry.ts.desc()).first()
    
    if latest_telemetry:
        pole.energized = latest_telemetry.energized
        pole.last_heartbeat = latest_telemetry.ts
    
    return PoleResponse.from_orm(pole)


@router.get("/dt/{dt_id}", response_model=List[PoleResponse])
async def get_poles_by_transformer(dt_id: str, db: Session = Depends(get_db)):
    """Get all poles under a specific distribution transformer."""
    poles = db.query(Pole).filter(Pole.dt_id == dt_id).all()
    return [PoleResponse.from_orm(p) for p in poles]


@router.get("/feeder/{feeder_id}", response_model=List[PoleResponse])
async def get_poles_by_feeder(feeder_id: str, db: Session = Depends(get_db)):
    """Get all poles on a specific feeder."""
    poles = db.query(Pole).filter(Pole.feeder_id == feeder_id).all()
    return [PoleResponse.from_orm(p) for p in poles]


@router.get("/transformers/all", response_model=List[TransformerResponse])
async def get_all_transformers(db: Session = Depends(get_db)):
    """Get all distribution transformers."""
    transformers = db.query(Transformer).all()
    return [TransformerResponse.from_orm(t) for t in transformers]


@router.get("/transformers/{dt_id}", response_model=TransformerResponse)
async def get_transformer(dt_id: str, db: Session = Depends(get_db)):
    """Get a specific transformer by ID."""
    transformer = db.query(Transformer).filter(Transformer.dt_id == dt_id).first()
    if not transformer:
        raise HTTPException(status_code=404, detail="Transformer not found")
    return TransformerResponse.from_orm(transformer)
