from sqlalchemy.orm import Session
from models import Pole, Transformer, Telemetry, Ticket
from schemas import FaultInjection, NoiseInjection
from datetime import datetime, timedelta
import random
import uuid
import logging
from typing import Dict, List
import math

logger = logging.getLogger(__name__)


class FaultSimulator:
    def __init__(self):
        self.active_faults: Dict[str, dict] = {}
        self.device_seq: Dict[str, int] = {}
    
    async def generate_network(
        self,
        num_transformers: int = 20,
        poles_per_dt: int = 70,
        db: Session = None
    ) -> dict:
        """Generate a synthetic network matching the assignment specifications."""
        logger.info(f"Generating network: {num_transformers} DTs, ~{poles_per_dt} poles per DT")
        
        # Clear existing data
        db.query(Telemetry).delete()
        db.query(Pole).delete()
        db.query(Transformer).delete()
        db.commit()
        
        # Base coordinates (Bangalore area)
        base_lat = 12.9716
        base_lon = 77.5946
        
        transformers_created = 0
        poles_created = 0
        devices_created = 0
        
        for i in range(num_transformers):
            dt_id = f"D-{i:04d}"
            feeder_id = f"F-{(i % 4):02d}-{(i // 4):02d}"
            
            # Random location near base
            lat_offset = random.uniform(-0.05, 0.05)
            lon_offset = random.uniform(-0.05, 0.05)
            dt_lat = base_lat + lat_offset
            dt_lon = base_lon + lon_offset
            
            transformer = Transformer(
                dt_id=dt_id,
                feeder_id=feeder_id,
                lat=dt_lat,
                lon=dt_lon,
                capacity_kva=random.choice([100, 160, 250, 315, 400]),
                households_served=random.randint(200, 500)
            )
            db.add(transformer)
            transformers_created += 1
            
            # Generate poles for this DT
            # 60% of DTs have missing topology (no seq_on_line or parent_pole_id)
            has_topology = random.random() < 0.4
            
            # Generate main line with branches
            num_main_poles = random.randint(20, 50)
            num_branches = random.randint(1, 4)
            
            # Main line poles
            prev_pole_id = None
            for j in range(num_main_poles):
                pole_id = f"P-{transformers_created:04d}{j:03d}"
                
                # Calculate pole position along line
                distance = j * 0.0002  # ~20m per pole
                angle = random.uniform(0, 2 * math.pi)
                pole_lat = dt_lat + distance * math.cos(angle)
                pole_lon = dt_lon + distance * math.sin(angle)
                
                # ~9% of poles have no device
                has_device = random.random() < 0.91
                device_id = f"KSPDB-{feeder_id}-{dt_id}-{j:04d}" if has_device else None
                
                # Ward and pincode
                ward = f"W-{random.randint(1, 200):03d}"
                pincode = random.choice(["560001", "560002", "560003", "560004", "560078"])
                
                pole = Pole(
                    pole_id=pole_id,
                    lat=pole_lat,
                    lon=pole_lon,
                    feeder_id=feeder_id,
                    dt_id=dt_id,
                    seq_on_line=j + 1 if has_topology else None,
                    parent_pole_id=prev_pole_id if has_topology else None,
                    pole_type=random.choice(["LT-9m-PCC", "LT-8m-Steel", "LT-9m-RCC"]),
                    ward=ward,
                    pincode=pincode,
                    device_id=device_id
                )
                db.add(pole)
                poles_created += 1
                if has_device:
                    devices_created += 1
                    self.device_seq[device_id] = 0
                
                prev_pole_id = pole_id
            
            # Branch poles
            for branch_idx in range(num_branches):
                branch_start_idx = random.randint(5, num_main_poles - 10)
                branch_start_pole_id = f"P-{transformers_created:04d}{branch_start_idx:03d}"
                
                branch_length = random.randint(5, 15)
                branch_angle = random.uniform(0, 2 * math.pi)
                
                prev_branch_pole = branch_start_pole_id
                for k in range(branch_length):
                    pole_id = f"P-{transformers_created:04d}B{branch_idx}{k:02d}"
                    
                    distance = (branch_start_idx + k + 1) * 0.0002
                    pole_lat = dt_lat + distance * math.cos(branch_angle)
                    pole_lon = dt_lon + distance * math.sin(branch_angle)
                    
                    has_device = random.random() < 0.91
                    device_id = f"KSPDB-{feeder_id}-{dt_id}-B{branch_idx}{k:04d}" if has_device else None
                    
                    pole = Pole(
                        pole_id=pole_id,
                        lat=pole_lat,
                        lon=pole_lon,
                        feeder_id=feeder_id,
                        dt_id=dt_id,
                        seq_on_line=None,  # Branches rarely have topology
                        parent_pole_id=prev_branch_pole if has_topology else None,
                        pole_type=random.choice(["LT-9m-PCC", "LT-8m-Steel"]),
                        ward=f"W-{random.randint(1, 200):03d}",
                        pincode=random.choice(["560001", "560002", "560003", "560004", "560078"]),
                        device_id=device_id
                    )
                    db.add(pole)
                    poles_created += 1
                    if has_device:
                        devices_created += 1
                        self.device_seq[device_id] = 0
                    
                    prev_branch_pole = pole_id
        
        db.commit()
        
        # Generate initial heartbeats
        await self._generate_initial_heartbeats(db)
        
        logger.info(f"Network generated: {transformers_created} DTs, {poles_created} poles, {devices_created} devices")
        
        return {
            "transformers": transformers_created,
            "poles": poles_created,
            "devices": devices_created,
            "coverage": f"{(devices_created/poles_created)*100:.1f}%"
        }
    
    async def _generate_initial_heartbeats(self, db: Session):
        """Generate initial heartbeat telemetry for all devices."""
        poles = db.query(Pole).filter(Pole.device_id.isnot(None)).all()
        
        for pole in poles:
            telemetry = Telemetry(
                device_id=pole.device_id,
                pole_id=pole.pole_id,
                event="heartbeat",
                energized=True,
                ts=datetime.utcnow() - timedelta(minutes=random.randint(0, 15)),
                seq=self.device_seq.get(pole.device_id, 0),
                battery_mv=random.randint(3400, 3600),
                rssi=random.randint(-70, -50),
                fw=random.choice(["1.4.2", "1.4.1", "1.3.0", "1.2.5"])
            )
            db.add(telemetry)
            self.device_seq[pole.device_id] = self.device_seq.get(pole.device_id, 0) + 1
        
        db.commit()
    
    async def inject_fault(self, fault: FaultInjection, db: Session) -> dict:
        """Inject a fault and generate realistic telemetry."""
        fault_id = str(uuid.uuid4())
        
        if fault.fault_type == "span":
            return await self._inject_span_fault(fault, fault_id, db)
        elif fault.fault_type == "distribution_transformer":
            return await self._inject_dt_fault(fault, fault_id, db)
        elif fault.fault_type == "feeder":
            return await self._inject_feeder_fault(fault, fault_id, db)
    
    async def _inject_span_fault(
        self,
        fault: FaultInjection,
        fault_id: str,
        db: Session
    ) -> dict:
        """Inject a span fault between two poles."""
        start_pole = db.query(Pole).filter(Pole.pole_id == fault.start_pole_id).first()
        end_pole = db.query(Pole).filter(Pole.pole_id == fault.end_pole_id).first()
        
        # If poles don't exist, auto-select valid ones for demo
        if not start_pole or not end_pole:
            logger.warning(f"Provided pole IDs not found, auto-selecting valid poles")
            poles = db.query(Pole).limit(2).all()
            if len(poles) >= 2:
                start_pole = poles[0]
                end_pole = poles[1]
                logger.info(f"Auto-selected poles: {start_pole.pole_id} to {end_pole.pole_id}")
            else:
                raise ValueError("No poles found in database. Please generate network first.")
        
        # Find all downstream poles (simplified - in real system would use topology)
        downstream_poles = db.query(Pole).filter(
            Pole.dt_id == start_pole.dt_id,
            Pole.seq_on_line > start_pole.seq_on_line if start_pole.seq_on_line else True
        ).all()
        
        affected_poles = []
        now = datetime.utcnow()
        
        for pole in downstream_poles:
            if pole.device_id:
                # 70% of devices send power_lost message
                if random.random() < 0.7:
                    telemetry = Telemetry(
                        device_id=pole.device_id,
                        pole_id=pole.pole_id,
                        event="power_lost",
                        energized=False,
                        ts=now + timedelta(milliseconds=random.randint(0, 5000)),
                        seq=self.device_seq.get(pole.device_id, 0),
                        battery_mv=random.randint(3200, 3500),
                        rssi=random.randint(-90, -70),
                        fw=random.choice(["1.4.2", "1.4.1", "1.3.0"])
                    )
                    db.add(telemetry)
                    self.device_seq[pole.device_id] = self.device_seq.get(pole.device_id, 0) + 1
                    affected_poles.append(pole.pole_id)
        
        # Firmware 1.2 devices just go silent (no power_lost)
        for pole in downstream_poles:
            if pole.device_id:
                if random.random() < 0.08:  # 8% on old firmware
                    # These devices won't send power_lost, they'll just stop heartbeats
                    pass
        
        db.commit()
        
        self.active_faults[fault_id] = {
            "type": "span",
            "start_pole": fault.start_pole_id,
            "end_pole": fault.end_pole_id,
            "affected_poles": affected_poles,
            "injected_at": now
        }
        
        return {
            "fault_id": fault_id,
            "type": "span",
            "affected_poles": len(affected_poles),
            "message": f"Span fault injected between {fault.start_pole_id} and {fault.end_pole_id}"
        }
    
    async def _inject_dt_fault(
        self,
        fault: FaultInjection,
        fault_id: str,
        db: Session
    ) -> dict:
        """Inject a distribution transformer fault."""
        poles = db.query(Pole).filter(Pole.dt_id == fault.target_id).all()
        
        affected_poles = []
        now = datetime.utcnow()
        
        for pole in poles:
            if pole.device_id:
                if random.random() < 0.7:
                    telemetry = Telemetry(
                        device_id=pole.device_id,
                        pole_id=pole.pole_id,
                        event="power_lost",
                        energized=False,
                        ts=now + timedelta(milliseconds=random.randint(0, 3000)),
                        seq=self.device_seq.get(pole.device_id, 0),
                        battery_mv=random.randint(3200, 3500),
                        rssi=random.randint(-90, -70),
                        fw=random.choice(["1.4.2", "1.4.1", "1.3.0"])
                    )
                    db.add(telemetry)
                    self.device_seq[pole.device_id] = self.device_seq.get(pole.device_id, 0) + 1
                    affected_poles.append(pole.pole_id)
        
        db.commit()
        
        self.active_faults[fault_id] = {
            "type": "distribution_transformer",
            "dt_id": fault.target_id,
            "affected_poles": affected_poles,
            "injected_at": now
        }
        
        return {
            "fault_id": fault_id,
            "type": "distribution_transformer",
            "affected_poles": len(affected_poles),
            "message": f"DT fault injected on {fault.target_id}"
        }
    
    async def _inject_feeder_fault(
        self,
        fault: FaultInjection,
        fault_id: str,
        db: Session
    ) -> dict:
        """Inject a feeder-level fault."""
        poles = db.query(Pole).filter(Pole.feeder_id == fault.target_id).all()
        
        affected_poles = []
        now = datetime.utcnow()
        
        for pole in poles:
            if pole.device_id:
                if random.random() < 0.7:
                    telemetry = Telemetry(
                        device_id=pole.device_id,
                        pole_id=pole.pole_id,
                        event="power_lost",
                        energized=False,
                        ts=now + timedelta(milliseconds=random.randint(0, 5000)),
                        seq=self.device_seq.get(pole.device_id, 0),
                        battery_mv=random.randint(3200, 3500),
                        rssi=random.randint(-90, -70),
                        fw=random.choice(["1.4.2", "1.4.1", "1.3.0"])
                    )
                    db.add(telemetry)
                    self.device_seq[pole.device_id] = self.device_seq.get(pole.device_id, 0) + 1
                    affected_poles.append(pole.pole_id)
        
        db.commit()
        
        self.active_faults[fault_id] = {
            "type": "feeder",
            "feeder_id": fault.target_id,
            "affected_poles": affected_poles,
            "injected_at": now
        }
        
        return {
            "fault_id": fault_id,
            "type": "feeder",
            "affected_poles": len(affected_poles),
            "message": f"Feeder fault injected on {fault.target_id}"
        }
    
    async def inject_noise(self, noise: NoiseInjection, db: Session) -> dict:
        """Inject noise for testing."""
        pole = db.query(Pole).filter(Pole.device_id == noise.device_id).first()
        if not pole:
            raise ValueError("Device not found")
        
        now = datetime.utcnow()
        
        if noise.noise_type == "dead_sensor":
            # Device stops reporting while power is still on
            # Simulate by not sending any telemetry (silence)
            return {
                "device_id": noise.device_id,
                "noise_type": "dead_sensor",
                "message": f"Device {noise.device_id} will stop reporting (dead sensor simulation)"
            }
        
        elif noise.noise_type == "duplicate":
            # Send duplicate telemetry
            telemetry = Telemetry(
                device_id=noise.device_id,
                pole_id=pole.pole_id,
                event="heartbeat",
                energized=True,
                ts=now,
                seq=self.device_seq.get(noise.device_id, 0) - 1,  # Duplicate seq
                battery_mv=3500,
                rssi=-60,
                fw="1.4.2"
            )
            db.add(telemetry)
            db.commit()
            
            return {
                "device_id": noise.device_id,
                "noise_type": "duplicate",
                "message": f"Duplicate telemetry sent for {noise.device_id}"
            }
        
        elif noise.noise_type == "out_of_order":
            # Send telemetry with old timestamp
            telemetry = Telemetry(
                device_id=noise.device_id,
                pole_id=pole.pole_id,
                event="heartbeat",
                energized=True,
                ts=now - timedelta(minutes=30),  # Old timestamp
                seq=self.device_seq.get(noise.device_id, 0),
                battery_mv=3500,
                rssi=-60,
                fw="1.4.2"
            )
            db.add(telemetry)
            db.commit()
            
            return {
                "device_id": noise.device_id,
                "noise_type": "out_of_order",
                "message": f"Out-of-order telemetry sent for {noise.device_id}"
            }
    
    async def repair_fault(self, fault_id: str, db: Session) -> dict:
        """Repair a fault and generate restoration telemetry."""
        if fault_id not in self.active_faults:
            raise ValueError("Fault not found")
        
        fault = self.active_faults[fault_id]
        now = datetime.utcnow()
        
        for pole_id in fault["affected_poles"]:
            pole = db.query(Pole).filter(Pole.pole_id == pole_id).first()
            if pole and pole.device_id:
                # Send boot and power_restored
                boot_telemetry = Telemetry(
                    device_id=pole.device_id,
                    pole_id=pole.pole_id,
                    event="boot",
                    energized=True,
                    ts=now + timedelta(milliseconds=random.randint(0, 2000)),
                    seq=self.device_seq.get(pole.device_id, 0),
                    battery_mv=random.randint(3400, 3600),
                    rssi=random.randint(-70, -50),
                    fw=random.choice(["1.4.2", "1.4.1", "1.3.0"])
                )
                db.add(boot_telemetry)
                self.device_seq[pole.device_id] = self.device_seq.get(pole.device_id, 0) + 1
                
                restored_telemetry = Telemetry(
                    device_id=pole.device_id,
                    pole_id=pole.pole_id,
                    event="power_restored",
                    energized=True,
                    ts=now + timedelta(seconds=random.randint(1, 20)),
                    seq=self.device_seq.get(pole.device_id, 0),
                    battery_mv=random.randint(3400, 3600),
                    rssi=random.randint(-70, -50),
                    fw=random.choice(["1.4.2", "1.4.1", "1.3.0"])
                )
                db.add(restored_telemetry)
                self.device_seq[pole.device_id] = self.device_seq.get(pole.device_id, 0) + 1
        
        db.commit()
        
        del self.active_faults[fault_id]
        
        return {
            "fault_id": fault_id,
            "message": f"Fault {fault_id} repaired, restoration telemetry generated"
        }
    
    async def reset(self, db: Session) -> dict:
        """Reset simulator state."""
        self.active_faults.clear()
        self.device_seq.clear()
        
        # Clear telemetry and tickets
        db.query(Telemetry).delete()
        db.query(Ticket).delete()
        db.commit()
        
        return {"message": "Simulator reset complete"}
