from sqlalchemy.orm import Session
from models import Pole, Telemetry, Ticket, FaultType, TicketStatus
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import networkx as nx
import logging
import uuid
from geopy.distance import geodesic

logger = logging.getLogger(__name__)


class FaultDetector:
    def __init__(self):
        self.detection_window = timedelta(minutes=5)
        self.grouping_window = timedelta(minutes=2)
    
    async def detect_faults(self, db: Session) -> List[dict]:
        """
        Main fault detection logic.
        Analyzes recent telemetry to detect and localize faults.
        """
        # Get recent dark poles
        recent_dark_poles = self._get_recent_dark_poles(db)
        
        if not recent_dark_poles:
            return []
        
        # Filter out scheduled outages
        recent_dark_poles = self._filter_scheduled_outages(recent_dark_poles, db)
        
        if not recent_dark_poles:
            return []
        
        # Group dark poles into potential faults
        fault_groups = self._group_dark_poles(recent_dark_poles, db)
        
        # Localize each fault group
        localized_faults = []
        for group in fault_groups:
            fault = await self._localize_fault(group, db)
            if fault:
                localized_faults.append(fault)
        
        return localized_faults
    
    def _get_recent_dark_poles(self, db: Session) -> List[dict]:
        """Get poles that have recently gone dark."""
        cutoff = datetime.utcnow() - self.detection_window
        
        # Find poles with recent power_lost events
        dark_poles = db.query(Telemetry, Pole).join(
            Pole, Telemetry.pole_id == Pole.pole_id
        ).filter(
            Telemetry.event == "power_lost",
            Telemetry.ts >= cutoff
        ).all()
        
        result = []
        for telemetry, pole in dark_poles:
            result.append({
                "pole_id": pole.pole_id,
                "dt_id": pole.dt_id,
                "feeder_id": pole.feeder_id,
                "lat": pole.lat,
                "lon": pole.lon,
                "device_id": pole.device_id,
                "ts": telemetry.ts,
                "seq": telemetry.seq
            })
        
        return result
    
    def _filter_scheduled_outages(self, dark_poles: List[dict], db: Session) -> List[dict]:
        """Filter out poles that are dark due to scheduled outages."""
        from models import ScheduledOutage
        
        now = datetime.utcnow()
        window_start = now - timedelta(hours=2)
        window_end = now + timedelta(hours=1)
        
        scheduled = db.query(ScheduledOutage).filter(
            ScheduledOutage.start <= window_end,
            ScheduledOutage.end >= window_start
        ).all()
        
        # Build set of affected pole IDs
        excluded_poles = set()
        for outage in scheduled:
            if outage.scope == "feeder":
                poles = db.query(Pole).filter(Pole.feeder_id == outage.target_id).all()
                excluded_poles.update(p.pole_id for p in poles)
            elif outage.scope == "dt":
                poles = db.query(Pole).filter(Pole.dt_id == outage.target_id).all()
                excluded_poles.update(p.pole_id for p in poles)
        
        return [p for p in dark_poles if p["pole_id"] not in excluded_poles]
    
    def _group_dark_poles(self, dark_poles: List[dict], db: Session) -> List[List[dict]]:
        """
        Group dark poles into fault groups.
        Poles that went dark within the grouping window and are on the same DT/feeder
        are likely part of the same fault.
        """
        if not dark_poles:
            return []
        
        # Sort by time
        dark_poles.sort(key=lambda x: x["ts"])
        
        groups = []
        current_group = [dark_poles[0]]
        
        for pole in dark_poles[1:]:
            # Check if this pole belongs to current group
            last_pole = current_group[-1]
            
            time_diff = pole["ts"] - last_pole["ts"]
            same_dt = pole["dt_id"] == last_pole["dt_id"]
            same_feeder = pole["feeder_id"] == last_pole["feeder_id"]
            
            if time_diff <= self.grouping_window and (same_dt or same_feeder):
                current_group.append(pole)
            else:
                groups.append(current_group)
                current_group = [pole]
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    async def _localize_fault(self, dark_poles: List[dict], db: Session) -> Optional[dict]:
        """
        Localize a fault from a group of dark poles.
        Determines the fault type and location.
        """
        if not dark_poles:
            return None
        
        # Get all poles in the affected DT(s)
        dt_ids = set(p["dt_id"] for p in dark_poles)
        all_poles = db.query(Pole).filter(Pole.dt_id.in_(dt_ids)).all()
        
        # Build topology if available
        has_topology = any(p.seq_on_line is not None for p in all_poles)
        
        # Determine fault type
        fault_type, location, confidence, reason = self._determine_fault_type(
            dark_poles, all_poles, has_topology, db
        )
        
        if not fault_type:
            return None
        
        # Calculate affected poles count
        affected_count = len(dark_poles)
        
        # Get PIN code
        pincode = dark_poles[0].get("pincode")
        if not pincode:
            # Try to get from pole data
            pole = db.query(Pole).filter(Pole.pole_id == dark_poles[0]["pole_id"]).first()
            if pole:
                pincode = pole.pincode
        
        return {
            "fault_type": fault_type,
            "fault_location": location,
            "lat": dark_poles[0]["lat"],
            "lon": dark_poles[0]["lon"],
            "pincode": pincode,
            "affected_poles_count": affected_count,
            "confidence": confidence,
            "confidence_reason": reason,
            "dark_poles": [p["pole_id"] for p in dark_poles]
        }
    
    def _determine_fault_type(
        self,
        dark_poles: List[dict],
        all_poles: List[Pole],
        has_topology: bool,
        db: Session
    ) -> Tuple[Optional[str], str, float, str]:
        """
        Determine the type and location of the fault.
        """
        # Check if all poles under DT(s) are dark
        dt_ids = set(p["dt_id"] for p in dark_poles)
        
        for dt_id in dt_ids:
            dt_poles = [p for p in all_poles if p.dt_id == dt_id]
            dark_pole_ids = set(p["pole_id"] for p in dark_poles if p["dt_id"] == dt_id)
            
            # If all poles under DT are dark, it's likely a DT fault
            if len(dark_pole_ids) >= len(dt_poles) * 0.9:  # 90% threshold
                dt = db.query(Pole).filter(Pole.pole_id == dark_poles[0]["pole_id"]).first()
                return (
                    FaultType.DISTRIBUTION_TRANSFORMER,
                    f"DT {dt_id}",
                    0.85,
                    f"All poles under DT {dt_id} are dark, indicating DT-level fault"
                )
        
        # Check if multiple DTs affected (feeder fault)
        if len(dt_ids) > 1:
            return (
                FaultType.FEEDER,
                f"Feeder {dark_poles[0]['feeder_id']}",
                0.90,
                f"Multiple DTs ({len(dt_ids)}) affected, indicating feeder-level fault"
            )
        
        # Otherwise, it's a span fault
        if has_topology:
            # Use topology to find exact span
            return self._localize_span_with_topology(dark_poles, all_poles, db)
        else:
            # Infer from geography
            return self._localize_span_geographically(dark_poles, all_poles, db)
    
    def _localize_span_with_topology(
        self,
        dark_poles: List[dict],
        all_poles: List[Pole],
        db: Session
    ) -> Tuple[str, str, float, str]:
        """
        Localize span fault when topology data is available.
        Find the boundary between live and dark poles.
        """
        # Sort dark poles by seq_on_line
        dark_poles_sorted = sorted(
            [p for p in dark_poles if p.get("seq_on_line")],
            key=lambda x: x["seq_on_line"]
        )
        
        if not dark_poles_sorted:
            return self._localize_span_geographically(dark_poles, all_poles, db)
        
        # Find the first dark pole
        first_dark = dark_poles_sorted[0]
        
        # Find the last live pole before it
        live_pole = db.query(Pole).filter(
            Pole.dt_id == first_dark["dt_id"],
            Pole.seq_on_line == first_dark["seq_on_line"] - 1
        ).first()
        
        if live_pole:
            return (
                FaultType.SPAN,
                f"Span between {live_pole.pole_id} and {first_dark['pole_id']}",
                0.95,
                f"Topology data available: fault on span between {live_pole.pole_id} (live) and {first_dark['pole_id']} (dark)"
            )
        else:
            # No live pole found, fault is near DT
            return (
                FaultType.SPAN,
                f"Near DT {first_dark['dt_id']}",
                0.80,
                f"First pole on line is dark, fault likely near DT {first_dark['dt_id']}"
            )
    
    def _localize_span_geographically(
        self,
        dark_poles: List[dict],
        all_poles: List[Pole],
        db: Session
    ) -> Tuple[str, str, float, str]:
        """
        Localize span fault when topology data is missing.
        Infer fault location from pole coordinates.
        """
        # Find poles that are still energized in the same DT
        dt_id = dark_poles[0]["dt_id"]
        dt_poles = db.query(Pole).filter(Pole.dt_id == dt_id).all()
        
        # Get recent telemetry to find live poles
        cutoff = datetime.utcnow() - timedelta(minutes=15)
        live_poles = db.query(Telemetry.pole_id).filter(
            Telemetry.pole_id.in_([p.pole_id for p in dt_poles]),
            Telemetry.energized == True,
            Telemetry.ts >= cutoff
        ).distinct().all()
        
        live_pole_ids = set(p[0] for p in live_poles)
        
        # Find the closest live pole to the dark poles
        dark_coords = [(p["lat"], p["lon"]) for p in dark_poles]
        avg_dark_lat = sum(c[0] for c in dark_coords) / len(dark_coords)
        avg_dark_lon = sum(c[1] for c in dark_coords) / len(dark_coords)
        
        closest_live = None
        min_distance = float("inf")
        
        for pole in dt_poles:
            if pole.pole_id in live_pole_ids:
                distance = geodesic((pole.lat, pole.lon), (avg_dark_lat, avg_dark_lon)).meters
                if distance < min_distance:
                    min_distance = distance
                    closest_live = pole
        
        if closest_live and min_distance < 500:  # Within 500m
            # Find the closest dark pole to the live pole
            closest_dark = min(
                dark_poles,
                key=lambda p: geodesic((p["lat"], p["lon"]), (closest_live.lat, closest_live.lon)).meters
            )
            
            return (
                FaultType.SPAN,
                f"Span near {closest_dark['pole_id']} (inferred from geography)",
                0.70,
                f"Topology unavailable: fault inferred from geography between {closest_live.pole_id} (live) and {closest_dark['pole_id']} (dark), confidence reduced due to missing topology"
            )
        else:
            # Cannot determine exact span, report DT-level
            return (
                FaultType.DISTRIBUTION_TRANSFORMER,
                f"DT {dt_id} (exact span unknown - topology missing)",
                0.50,
                f"Topology data missing for DT {dt_id}, cannot localize to exact span. Reporting DT-level location."
            )
    
    async def create_ticket(self, fault: dict, db: Session) -> Ticket:
        """Create a ticket for a detected fault."""
        ticket_id = f"TKT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        ticket = Ticket(
            ticket_id=ticket_id,
            fault_type=fault["fault_type"],
            fault_location=fault["fault_location"],
            lat=fault["lat"],
            lon=fault["lon"],
            pincode=fault["pincode"],
            affected_poles_count=fault["affected_poles_count"],
            confidence=fault["confidence"],
            confidence_reason=fault["confidence_reason"],
            status=TicketStatus.DETECTED,
            detected_at=datetime.utcnow()
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        logger.info(f"Ticket created: {ticket_id} for {fault['fault_type']} at {fault['fault_location']}")
        
        return ticket
