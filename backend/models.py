from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum


class TicketStatus(str, enum.Enum):
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    CREW_ASSIGNED = "crew_assigned"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"


class FaultType(str, enum.Enum):
    SPAN = "span"
    DISTRIBUTION_TRANSFORMER = "distribution_transformer"
    FEEDER = "feeder"


class Transformer(Base):
    __tablename__ = "transformers"

    dt_id = Column(String, primary_key=True, index=True)
    feeder_id = Column(String, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    capacity_kva = Column(Integer)
    households_served = Column(Integer)
    
    poles = relationship("Pole", back_populates="transformer")


class Pole(Base):
    __tablename__ = "poles"

    pole_id = Column(String, primary_key=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    feeder_id = Column(String, index=True)
    dt_id = Column(String, ForeignKey("transformers.dt_id"), index=True)
    seq_on_line = Column(Integer, nullable=True)
    parent_pole_id = Column(String, ForeignKey("poles.pole_id"), nullable=True)
    pole_type = Column(String)
    ward = Column(String)
    pincode = Column(String, nullable=True)
    device_id = Column(String, nullable=True, unique=True)
    
    transformer = relationship("Transformer", back_populates="poles")
    parent = relationship("Pole", remote_side=[pole_id])
    children = relationship("Pole", back_populates="parent")
    telemetry_records = relationship("Telemetry", back_populates="pole")


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    pole_id = Column(String, ForeignKey("poles.pole_id"), index=True)
    event = Column(String, index=True)
    energized = Column(Boolean)
    ts = Column(DateTime, index=True)
    seq = Column(Integer)
    battery_mv = Column(Integer)
    rssi = Column(Integer)
    fw = Column(String)
    processed = Column(Boolean, default=False)
    
    pole = relationship("Pole", back_populates="telemetry_records")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String, unique=True, index=True)
    fault_type = Column(Enum(FaultType))
    fault_location = Column(String)  # pole_id or span description
    lat = Column(Float)
    lon = Column(Float)
    pincode = Column(String, nullable=True)
    affected_poles_count = Column(Integer)
    confidence = Column(Float)
    confidence_reason = Column(Text)
    status = Column(Enum(TicketStatus), default=TicketStatus.DETECTED)
    detected_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    crew_assigned_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    ai_summary = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class ScheduledOutage(Base):
    __tablename__ = "scheduled_outages"

    id = Column(Integer, primary_key=True, index=True)
    outage_id = Column(String, unique=True, index=True)
    scope = Column(String)  # "feeder" or "dt"
    target_id = Column(String, index=True)
    start = Column(DateTime, index=True)
    end = Column(DateTime, index=True)
    reason = Column(String)
