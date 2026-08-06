# KSPDB Fault Detection System

Real-time fault detection and localization system for Karnataka State Power Distribution Board.

## Overview

This system detects and localizes power line faults in low-tension distribution networks using IoT pole devices. It ingests telemetry, identifies fault boundaries, creates tickets, and verifies restoration automatically.

## Quick Start

```bash
git clone <repo-url>
cd kspdb-fault-detection
docker compose up
```

The system will:
- Start PostgreSQL database
- Start FastAPI backend (port 8000)
- Start React frontend (port 3000)
- Seed database with synthetic network (20 DTs, ~1400 poles)
- Be available at http://localhost:3000

## Live Demo

**Frontend URL:** https://kspdb-frontend-1gj3.onrender.com

**Backend URL:** https://kspdb-backend1.onrender.com

**GitHub Repository:** https://github.com/Apoorva744/kspdb-fault-detection

**Demo Video:** [To be added before submission]

## Features

- **Telemetry Ingestion**: Handles device heartbeats, power_lost, power_restored events with deduplication
- **Fault Localization**: Identifies fault boundaries using topology data or geographic inference
- **Missing Topology Handling**: Falls back to geographic inference when pole ordering is unavailable (60% of DTs)
- **Ticket Workflow**: Full lifecycle from detection to closure with telemetry-based verification
- **Noise Filtering**: Distinguishes real faults from dead sensors, scheduled outages, and device failures
- **Operator Console**: Non-technical UI for control room operators
- **Fault Simulator**: Inject faults and noise for testing

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical design, algorithms, and data flow
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment instructions and troubleshooting
- [DECISIONS.md](DECISIONS.md) - Design decisions and assumptions
- [AI-WORKFLOW.md](AI-WORKFLOW.md) - AI tooling usage and workflow

## API Endpoints

- `POST /api/telemetry/` - Ingest telemetry from devices
- `GET /api/poles/` - Query poles and transformers
- `GET /api/tickets/` - List and manage fault tickets
- `POST /api/simulator/inject-fault` - Inject test faults
- `GET /api/scheduled-outages/` - Query scheduled outages

## Tech Stack

**Backend:**
- FastAPI (Python 3.11)
- PostgreSQL
- SQLAlchemy ORM
- NetworkX (graph operations)
- Geopy (geographic calculations)

**Frontend:**
- React 18
- Vite
- TailwindCSS
- Lucide Icons
- React Router

## Testing the System

1. Navigate to http://localhost:3000
2. Go to Simulator tab
3. Click "Generate Synthetic Network" (auto-seeded on startup)
4. Inject a fault:
   - Select fault type (span/DT/feeder)
   - Enter target ID (e.g., D-0001 for DT fault)
   - Click "Inject Fault"
5. Go to Console tab to see the detected ticket
6. Repair the fault from Simulator to see auto-verification

## Key Design Decisions

- **Topology Inference**: When pole ordering is missing (60% of DTs), system uses geographic distance to infer fault location with reduced confidence
- **Grouping Logic**: Dark poles within 2 minutes on same DT/feeder are grouped as one fault
- **Verification**: Tickets can only be marked resolved when telemetry confirms restoration
- **AI Feature**: Natural language incident summaries help operators quickly understand situations (optional, falls back to templates)

## Known Limitations

- Geographic inference has ~70% accuracy vs 95% with topology data
- System assumes radial network (no loops)
- PIN code geocoding uses pole data; missing for ~3% of poles
- No real-time WebSocket updates (uses 10-second polling)

## License

MIT License - see LICENSE file for details
