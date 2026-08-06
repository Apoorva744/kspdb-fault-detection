from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class EventType(str, Enum):
    HEARTBEAT = "heartbeat"
    POWER_LOST = "power_lost"
    POWER_RESTORED = "power_restored"
    BOOT = "boot"


class TelemetryCreate(BaseModel):
    device_id: str
    pole_id: str
    event: EventType
    energized: bool
    ts: datetime
    seq: int
    battery_mv: Optional[int] = None
    rssi: Optional[int] = None
    fw: Optional[str] = None


class TelemetryResponse(BaseModel):
    id: int
    device_id: str
    pole_id: str
    event: str
    energized: bool
    ts: datetime
    seq: int
    battery_mv: Optional[int]
    rssi: Optional[int]
    fw: Optional[str]
    
    class Config:
        from_attributes = True


class PoleResponse(BaseModel):
    pole_id: str
    lat: float
    lon: float
    feeder_id: str
    dt_id: str
    seq_on_line: Optional[int]
    parent_pole_id: Optional[str]
    pole_type: Optional[str]
    ward: Optional[str]
    pincode: Optional[str]
    device_id: Optional[str]
    energized: Optional[bool] = None
    last_heartbeat: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransformerResponse(BaseModel):
    dt_id: str
    feeder_id: str
    lat: float
    lon: float
    capacity_kva: Optional[int]
    households_served: Optional[int]
    
    class Config:
        from_attributes = True


class TicketStatus(str, Enum):
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    CREW_ASSIGNED = "crew_assigned"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"


class FaultType(str, Enum):
    SPAN = "span"
    DISTRIBUTION_TRANSFORMER = "distribution_transformer"
    FEEDER = "feeder"


class TicketCreate(BaseModel):
    fault_type: FaultType
    fault_location: str
    lat: float
    lon: float
    pincode: Optional[str]
    affected_poles_count: int
    confidence: float
    confidence_reason: str


class TicketUpdate(BaseModel):
    status: TicketStatus
    notes: Optional[str] = None


class TicketResponse(BaseModel):
    id: int
    ticket_id: str
    fault_type: str
    fault_location: str
    lat: float
    lon: float
    pincode: Optional[str]
    affected_poles_count: int
    confidence: float
    confidence_reason: str
    status: str
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    crew_assigned_at: Optional[datetime]
    resolved_at: Optional[datetime]
    verified_at: Optional[datetime]
    closed_at: Optional[datetime]
    ai_summary: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class FaultInjection(BaseModel):
    fault_type: FaultType
    target_id: str  # pole_id for span, dt_id for DT, feeder_id for feeder
    start_pole_id: Optional[str] = None  # for span faults
    end_pole_id: Optional[str] = None  # for span faults


class NoiseInjection(BaseModel):
    device_id: str
    noise_type: str  # "dead_sensor", "duplicate", "out_of_order"
