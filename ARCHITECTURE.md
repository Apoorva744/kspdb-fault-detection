# Architecture

## System Overview

```
┌─────────────┐     HTTPS     ┌──────────────┐
│ Pole Devices│ ─────────────► │  FastAPI     │
│ (IoT)       │  Telemetry    │  Backend     │
└─────────────┘               │              │
                              │  ┌────────┐  │
┌─────────────┐     REST      │  │  Postgres│  │
│  React      │ ◄────────────┤  └────────┘  │
│  Frontend   │   API/UI      │              │
└─────────────┘               │  ┌────────┐  │
                              │  │Fault   │  │
                              │  │Detector│  │
                              │  └────────┘  │
                              └──────────────┘
```

## Data Flow

### 1. Telemetry Ingestion

**Endpoint:** `POST /api/telemetry/`

**Process:**
1. Device sends telemetry with device_id, pole_id, event, energized, timestamp, seq
2. System checks for duplicates using (device_id, seq) combination
3. If duplicate: return existing record
4. If new: store in database, trigger background fault detection
5. Background task processes telemetry and calls fault detector

**Handling Challenges:**
- **Duplicates**: Deduplicated using device-specific sequence numbers
- **Out-of-order**: Accepted but seq ordering ensures correct state
- **Clock skew**: Device timestamps used for display, server time for detection windows
- **Bursts**: Async background processing prevents blocking
- **Firmware 1.2**: Devices without power_lost events detected via heartbeat timeout

### 2. Fault Detection Algorithm

**Input:** Recent telemetry (last 5 minutes)

**Steps:**

1. **Get Recent Dark Poles**
   - Query telemetry with event=power_lost within detection window
   - Join with pole registry for location data

2. **Filter Scheduled Outages**
   - Query scheduled outage feed for current time window
   - Exclude poles affected by scheduled feeder/DT outages
   - Handles 20-40 minute overrun and cancellations

3. **Group Dark Poles**
   - Sort by timestamp
   - Group poles within 2-minute window on same DT/feeder
   - Each group = potential fault

4. **Localize Fault**
   - For each group, determine fault type:
     - **DT Fault**: All poles under DT dark (90% threshold)
     - **Feeder Fault**: Multiple DTs affected
     - **Span Fault**: Otherwise

5. **Determine Location**
   - **With topology data (40% of DTs):**
     - Find boundary between last live pole and first dark pole using seq_on_line
     - Confidence: 95%
   - **Without topology (60% of DTs):**
     - Find live poles via recent telemetry
     - Calculate geographic distances
     - Infer fault span between closest live-dark pair
     - Confidence: 70% (reduced due to inference)
     - Fallback: Report DT-level if inference fails (50% confidence)

6. **Create Ticket**
   - Check for existing ticket at same location
   - If none: create new ticket with detected status
   - Include confidence score and reasoning

**Complexity:**
- Time: O(n log n) for sorting, O(n) for grouping
- Space: O(n) for dark poles in window
- n = number of dark poles in detection window (typically < 100)

### 3. Topology Representation

**Database Schema:**
```python
Pole:
  pole_id (PK)
  lat, lon (GPS coordinates)
  dt_id (FK to Transformer)
  seq_on_line (position from DT, NULL for 60%)
  parent_pole_id (FK to Pole, NULL for 60%)
  device_id (FK to Telemetry device)
```

**Graph Structure:**
- When topology available: Tree structure using parent_pole_id
- When topology missing: Geographic adjacency inferred on-demand
- NetworkX used for graph operations when needed

**Missing Topology Strategy:**
- Primary: Geographic distance-based inference
- Fallback: DT-level localization
- Explicit UI indication of confidence level
- Documented in ARCHITECTURE.md

### 4. Noise Handling

**Dead Sensor Detection:**
- Single dark pole with live children = impossible as line fault
- Treated as device failure, not outage
- No ticket created

**Scheduled Outages:**
- Queried from mock API
- Time window extended ±1 hour to handle overrun
- Poles in scheduled outage windows excluded from fault detection

**Debouncing:**
- 2-minute grouping window prevents multiple tickets for same fault
- Duplicate detection prevents re-processing

**False Positive Mitigation:**
- Confidence scoring (50-95%)
- Explicit reasoning in ticket
- UI shows confidence with color coding
- Operators can acknowledge low-confidence tickets for investigation

### 5. Ticket Workflow

**States:** detected → acknowledged → crew_assigned → resolved → verified → closed

**Transitions:**
- detected → acknowledged: Operator action
- acknowledged → crew_assigned: Operator action
- crew_assigned → resolved: Operator action (with telemetry verification)
- resolved → verified: Automatic when poles energized
- verified → closed: Operator action

**Verification Logic:**
- Check recent telemetry (last 5 minutes) for affected poles
- If all poles energized: auto-transition to verified
- If poles still dark: block resolution transition

**Restoration Detection:**
- power_restored events trigger verification check
- Background task polls for restoration every 10 seconds

### 6. API Surface

| Method | Path | Purpose | Request | Response |
|--------|------|---------|---------|----------|
| POST | /api/telemetry/ | Ingest telemetry | TelemetryCreate | TelemetryResponse |
| GET | /api/telemetry/pole/{id} | Get pole telemetry | - | TelemetryResponse[] |
| GET | /api/poles/ | List poles | skip, limit | PoleResponse[] |
| GET | /api/poles/{id} | Get pole | - | PoleResponse |
| GET | /api/poles/dt/{dt_id} | Get DT poles | - | PoleResponse[] |
| GET | /api/tickets/ | List tickets | status, skip, limit | TicketResponse[] |
| GET | /api/tickets/{id} | Get ticket | - | TicketResponse |
| PUT | /api/tickets/{id} | Update ticket | TicketUpdate | TicketResponse |
| POST | /api/simulator/inject-fault | Inject fault | FaultInjection | fault result |
| POST | /api/simulator/inject-noise | Inject noise | NoiseInjection | noise result |
| POST | /api/simulator/generate-network | Generate network | num_transformers, poles_per_dt | network stats |
| GET | /api/scheduled-outages/ | Get outages | from, to | ScheduledOutage[] |

### 7. UI Design Reasoning

**Operator Console - First Screen:**
- **Active incident count** (top right) - Most critical metric
- **Ticket list** with status badges - Quick scan of current situation
- **Filter tabs** - Focus on specific workflow stages
- **Confidence indicators** - Color-coded (green/yellow/red)
- **AI summary** (when available) - Natural language explanation

**What's Deliberately Omitted:**
- Geographic map (adds complexity, list view sufficient for dispatch)
- Historical analytics (out of scope per brief)
- Crew routing (out of scope per brief)
- Real-time graphs (operator needs actionable info, not trends)

**Information Hierarchy:**
1. Status (color-coded badge)
2. Location (fault type + specific asset)
3. Severity (affected poles count)
4. Confidence (affects trust in alert)
5. AI summary (optional, for quick understanding)

**Ambiguity Communication:**
- Low confidence shown in red with explicit reasoning
- "Topology missing" clearly stated in location
- PIN code "Unknown" when data unavailable

### 8. AI Feature

**Feature:** Natural language incident summary generation

**Location:** Ticket creation and display

**Why Here:**
- Operators are non-technical at 2 AM
- Technical details (confidence_reason) are verbose
- 2-3 sentence summary aids quick comprehension
- Falls back to template if AI unavailable

**Implementation:**
- Uses OpenAI GPT-3.5-turbo when API key provided
- Template-based fallback when unavailable
- Cost: ~$0.0002 per ticket
- Cached in ticket.ai_summary field

**What AI Does NOT Do:**
- Fault localization (deterministic graph traversal is superior)
- Topology inference (geographic algorithms are more reliable)
- Noise classification (rule-based is more predictable)

**Failure Mode:**
- If AI unavailable: template summary generated
- If AI wrong: operator can still see technical details
- No dependency on AI for core functionality

## Performance Targets

| Metric | Target | Implementation |
|--------|--------|----------------|
| Fault → UI visible | < 120s p95 | Background processing, 10s polling |
| Ingest throughput | ≥ 500 msg/s | Async processing, connection pooling |
| Burst tolerance | 5000 msg/10s | Background tasks, non-blocking writes |
| Console load | < 2s | Pagination, indexed queries |
| Restoration verify | < 120s | Event-driven + polling |
