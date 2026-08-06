from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Ticket, TicketStatus
from schemas import TicketResponse, TicketUpdate
from typing import List
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[TicketResponse])
async def get_all_tickets(
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all tickets with optional status filter."""
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    tickets = query.order_by(Ticket.detected_at.desc()).offset(skip).limit(limit).all()
    return [TicketResponse.from_orm(t) for t in tickets]


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Get a specific ticket by ID."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketResponse.from_orm(ticket)


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    update: TicketUpdate,
    db: Session = Depends(get_db)
):
    """Update ticket status and notes."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Validate status transitions
    valid_transitions = {
        TicketStatus.DETECTED: [TicketStatus.ACKNOWLEDGED],
        TicketStatus.ACKNOWLEDGED: [TicketStatus.CREW_ASSIGNED],
        TicketStatus.CREW_ASSIGNED: [TicketStatus.RESOLVED],
        TicketStatus.RESOLVED: [TicketStatus.VERIFIED, TicketStatus.CREW_ASSIGNED],
        TicketStatus.VERIFIED: [TicketStatus.CLOSED],
        TicketStatus.CLOSED: []
    }
    
    if update.status not in valid_transitions.get(ticket.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {ticket.status} to {update.status}"
        )
    
    # Special validation: cannot mark resolved if poles are still dark
    if update.status == TicketStatus.RESOLVED:
        from services.verification import verify_restoration
        is_restored = await verify_restoration(ticket, db)
        if not is_restored:
            raise HTTPException(
                status_code=400,
                detail="Cannot mark as resolved - affected poles are still dark. System requires telemetry verification."
            )
    
    ticket.status = update.status
    ticket.notes = update.notes
    
    # Update timestamps
    if update.status == TicketStatus.ACKNOWLEDGED:
        ticket.acknowledged_at = datetime.utcnow()
    elif update.status == TicketStatus.CREW_ASSIGNED:
        ticket.crew_assigned_at = datetime.utcnow()
    elif update.status == TicketStatus.RESOLVED:
        ticket.resolved_at = datetime.utcnow()
    elif update.status == TicketStatus.VERIFIED:
        ticket.verified_at = datetime.utcnow()
    elif update.status == TicketStatus.CLOSED:
        ticket.closed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ticket)
    
    logger.info(f"Ticket {ticket_id} updated to status {update.status}")
    return TicketResponse.from_orm(ticket)
