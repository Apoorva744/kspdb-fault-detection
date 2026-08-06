from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from schemas import FaultInjection, NoiseInjection
from services.simulator import FaultSimulator
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
simulator = FaultSimulator()


@router.post("/inject-fault")
async def inject_fault(
    fault: FaultInjection,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Inject a fault into the system for testing.
    Generates realistic telemetry and triggers fault detection.
    """
    result = await simulator.inject_fault(fault, db)
    logger.info(f"Fault injected: {fault.fault_type} on {fault.target_id}")
    return result


@router.post("/inject-noise")
async def inject_noise(
    noise: NoiseInjection,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Inject noise (dead sensor, duplicate, etc.) for testing."""
    result = await simulator.inject_noise(noise, db)
    logger.info(f"Noise injected: {noise.noise_type} on {noise.device_id}")
    return result


@router.post("/repair-fault")
async def repair_fault(
    fault_id: str,
    db: Session = Depends(get_db)
):
    """Repair a fault and generate restoration telemetry."""
    result = await simulator.repair_fault(fault_id, db)
    logger.info(f"Fault repaired: {fault_id}")
    return result


@router.post("/generate-network")
async def generate_network(
    num_transformers: int = 20,
    poles_per_dt: int = 70,
    db: Session = Depends(get_db)
):
    """Generate a synthetic network of poles and transformers for testing."""
    result = await simulator.generate_network(num_transformers, poles_per_dt, db)
    logger.info(f"Network generated: {result['transformers']} transformers, {result['poles']} poles")
    return result


@router.post("/reset")
async def reset_simulator(db: Session = Depends(get_db)):
    """Reset the simulator state."""
    result = await simulator.reset(db)
    logger.info("Simulator reset")
    return result


@router.get("/valid-poles")
async def get_valid_poles(db: Session = Depends(get_db)):
    """Get a sample of valid pole IDs for fault injection."""
    poles = db.query(Pole).limit(20).all()
    return {
        "sample_pole_ids": [pole.pole_id for pole in poles],
        "total_poles": db.query(Pole).count(),
        "message": "Use these pole IDs for fault injection"
    }
