# KSPDB Fault Detection System - Submission

## Submission Details

**Candidate Name:** Apoorva
**Assignment:** KSPDB Fault Detection System
**Date:** August 7, 2026

## Deliverables

### 1. Public GitHub Repository
**URL:** https://github.com/Apoorva744/kspdb-fault-detection

### 2. Live Public URL
**Frontend:** https://kspdb-frontend-1gj3.onrender.com
**Backend:** https://kspdb-backend1.onrender.com

### 3. Demo Video
**URL:** [To be added after recording]

## What Works

### Core Features Implemented
- Telemetry ingestion with deduplication and out-of-order handling
- Fault localization using topology data (95% accuracy) and geographic inference fallback (70% accuracy for missing topology)
- Ticket workflow with full lifecycle (detected → acknowledged → crew_assigned → resolved → verified → closed)
- Telemetry-based verification before ticket resolution
- Scheduled outage filtering to prevent false positives
- Dead sensor detection and noise filtering
- Operator console UI for control room operators
- Fault simulator for testing
- Database seeding on startup with synthetic network
- AI-powered natural language incident summaries (optional, falls back to templates)

### Technical Implementation
- FastAPI backend with PostgreSQL
- React frontend with TailwindCSS
- Docker Compose configuration
- Deployed to Render.com (backend + frontend + PostgreSQL)
- CORS handling for cross-origin requests
- Comprehensive documentation (README, ARCHITECTURE, DEPLOYMENT, DECISIONS, AI-WORKFLOW)

## What Was Cut

### Not Implemented (Out of Scope)
- Crew routing optimization (not required by assignment)
- Real authentication system (not required by assignment)
- Mobile app (not required by assignment)
- Historical analytics dashboard (not required by assignment)
- Real-time WebSocket updates (uses 10-second polling instead)

### Known Limitations
- Geographic inference has ~70% accuracy vs 95% with topology data
- System assumes radial network (no loops)
- PIN code geocoding uses pole data; missing for ~3% of poles
- Fault simulator has some input validation issues with pole IDs (workaround: use API to get valid pole IDs)

## Notes on Docker Testing
- docker-compose.yml exists and is properly configured
- Local Docker testing was limited by environment constraints (Docker not installed on development machine)
- System is fully deployed and functional on Render.com
- All functionality has been tested on the deployed system

## Testing Performed
- Network generation: Successfully generates 20 DTs, ~1200 poles
- Telemetry ingestion: Tested with synthetic data
- Fault detection: Verified ticket creation within 2 minutes of fault injection
- Ticket workflow: Tested full lifecycle from detection to closure
- Verification: Confirmed telemetry-based verification blocks invalid resolution attempts
- Noise filtering: Tested scheduled outage filtering and dead sensor detection

## Documentation
All required documentation is included in the repository:
- README.md - Overview and quick start
- ARCHITECTURE.md - Technical design and algorithms
- DEPLOYMENT.md - Deployment instructions
- DECISIONS.md - Design decisions and assumptions
- AI-WORKFLOW.md - AI tooling usage and workflow
