from sqlalchemy.orm import Session
from models import Ticket, Telemetry, Pole
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


async def verify_restoration(ticket: Ticket, db: Session) -> bool:
    """
    Verify that power has been restored for a ticket.
    Returns True if affected poles are energized, False otherwise.
    """
    # Get poles in the affected area
    # This is simplified - in production would track exact affected poles per ticket
    
    # Try to extract DT ID from fault location
    dt_id = None
    if "DT" in ticket.fault_location:
        parts = ticket.fault_location.split()
        for part in parts:
            if part.startswith("D-"):
                dt_id = part
                break
    
    if dt_id:
        poles = db.query(Pole).filter(Pole.dt_id == dt_id).all()
    else:
        # Fallback: get poles within 500m
        from geopy.distance import geodesic
        all_poles = db.query(Pole).all()
        poles = []
        for pole in all_poles:
            distance = geodesic((pole.lat, pole.lon), (ticket.lat, ticket.lon)).meters
            if distance < 500:
                poles.append(pole)
    
    # Check if poles are energized
    cutoff = datetime.utcnow() - timedelta(minutes=5)
    
    for pole in poles:
        if pole.device_id:
            recent = db.query(Telemetry).filter(
                Telemetry.pole_id == pole.pole_id,
                Telemetry.ts >= cutoff
            ).order_by(Telemetry.ts.desc()).first()
            
            if recent and not recent.energized:
                logger.warning(f"Pole {pole.pole_id} still dark, cannot verify restoration")
                return False
    
    logger.info(f"All affected poles energized for ticket {ticket.ticket_id}")
    return True
