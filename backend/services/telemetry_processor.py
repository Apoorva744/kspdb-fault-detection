from sqlalchemy.orm import Session
from models import Telemetry, Pole
from services.fault_detector import FaultDetector
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TelemetryProcessor:
    def __init__(self):
        self.fault_detector = FaultDetector()
    
    async def process_telemetry(self, pole_id: str, db: Session):
        """
        Process incoming telemetry and trigger fault detection if needed.
        """
        # Check if this is a power_lost event
        recent_telemetry = db.query(Telemetry).filter(
            Telemetry.pole_id == pole_id
        ).order_by(Telemetry.ts.desc()).first()
        
        if recent_telemetry and recent_telemetry.event == "power_lost":
            logger.info(f"Power lost detected on pole {pole_id}, triggering fault detection")
            await self._trigger_fault_detection(db)
        
        # Also check for power_restored events for ticket verification
        elif recent_telemetry and recent_telemetry.event == "power_restored":
            logger.info(f"Power restored on pole {pole_id}, checking ticket verification")
            await self._check_restoration_verification(pole_id, db)
    
    async def _trigger_fault_detection(self, db: Session):
        """Trigger fault detection analysis."""
        try:
            faults = await self.fault_detector.detect_faults(db)
            
            for fault in faults:
                # Check if a ticket already exists for this fault
                from models import Ticket
                existing = db.query(Ticket).filter(
                    Ticket.fault_location == fault["fault_location"],
                    Ticket.status.in_(["detected", "acknowledged", "crew_assigned", "resolved"])
                ).first()
                
                if not existing:
                    ticket = await self.fault_detector.create_ticket(fault, db)
                    logger.info(f"New ticket created: {ticket.ticket_id}")
                else:
                    logger.info(f"Ticket already exists for fault at {fault['fault_location']}")
        
        except Exception as e:
            logger.error(f"Error in fault detection: {e}")
    
    async def _check_restoration_verification(self, pole_id: str, db: Session):
        """Check if any tickets can be verified as restored."""
        from models import Ticket
        
        # Find tickets that are in RESOLVED state and involve this pole
        # This is simplified - in production would track which poles are affected by which ticket
        tickets = db.query(Ticket).filter(
            Ticket.status == "resolved"
        ).all()
        
        for ticket in tickets:
            # Check if affected poles are now energized
            is_restored = await self._verify_ticket_restoration(ticket, db)
            if is_restored:
                ticket.status = "verified"
                ticket.verified_at = datetime.utcnow()
                db.commit()
                logger.info(f"Ticket {ticket.ticket_id} verified as restored")
    
    async def _verify_ticket_restoration(self, ticket, db: Session) -> bool:
        """
        Verify that the poles affected by a ticket are now energized.
        """
        # Get poles in the area of the fault
        # This is simplified - would need to track affected poles per ticket
        cutoff = datetime.utcnow() - timedelta(minutes=10)
        
        # Check recent telemetry in the area
        nearby_poles = db.query(Pole).filter(
            Pole.dt_id == ticket.fault_location.split()[-1].replace("DT-", "") if "DT" in ticket.fault_location else True
        ).all()
        
        for pole in nearby_poles:
            if pole.device_id:
                recent = db.query(Telemetry).filter(
                    Telemetry.pole_id == pole.pole_id,
                    Telemetry.ts >= cutoff
                ).order_by(Telemetry.ts.desc()).first()
                
                if recent and not recent.energized:
                    # Pole is still dark
                    return False
        
        return True
