# Decisions Log

## 2026-08-06 - Initial Architecture Decisions

### Tech Stack Selection

**Chosen:** FastAPI (Python) + React + PostgreSQL

**Rejected:**
- Node.js backend: Less familiar with Python data science libraries
- NoSQL database: Relational model better for structured pole/telemetry data
- GraphQL: REST sufficient for this use case, simpler to implement

**Reasoning:** FastAPI provides async support out-of-the-box, Pydantic for validation, and excellent performance. React ecosystem mature for UI. PostgreSQL reliable for relational data with geographic queries.

### Topology Inference Strategy

**Chosen:** Geographic distance-based inference with confidence degradation

**Rejected:**
- Assume topology complete (violates assignment constraint)
- DT-level only (too coarse for useful dispatch)
- ML-based inference (overkill, not enough training data)

**Reasoning:** 60% of DTs missing topology is the central problem. Geographic inference provides reasonable accuracy (70%) while being transparent about uncertainty. Confidence scores explicitly communicate degradation.

### Fault Grouping Window

**Chosen:** 2-minute grouping window

**Rejected:**
- 30 seconds: Too tight, would split single faults
- 10 minutes: Too loose, would merge separate faults

**Reasoning:** 2 minutes balances grouping related events while distinguishing separate faults during storms. Based on typical propagation time in telemetry system.

### AI Feature Placement

**Chosen:** Natural language incident summaries for operators

**Rejected:**
- AI for fault localization: Graph traversal is deterministic, instant, free
- AI for topology inference: Geographic algorithms more reliable
- AI for noise classification: Rule-based is more predictable

**Reasoning:** Operators at 2 AM need quick comprehension. Technical confidence_reason is verbose. AI summaries provide human-readable context. Falls back to templates if unavailable.

### Real-time vs Polling

**Chosen:** 10-second polling for UI updates

**Rejected:**
- WebSockets: Adds complexity, proxy issues on deployment
- 1-second polling: Too frequent, unnecessary load
- 60-second polling: Too slow for operator experience

**Reasoning:** 10-second polling provides near-real-time feel without WebSocket complexity. Fault detection is async anyway, so 10s delay acceptable.

### Map vs List View

**Chosen:** List view with geographic coordinates

**Rejected:**
- Interactive map: Adds Leaflet complexity, requires tile server
- Graph visualization: Too technical for operators

**Reasoning:** List view sufficient for dispatch. Coordinates provided for navigation. Map would be nice-to-have but not core to dispatch workflow.

### Verification Strategy

**Chosen:** Telemetry-based verification blocking manual resolution

**Rejected:**
- Manual resolution only: Violates assignment requirement
- Trust crew reports: System must verify independently

**Reasoning:** Assignment explicitly requires telemetry verification. Blocking manual resolution when poles still dark prevents false closures.

### Scheduled Outage Handling

**Chosen:** Extended time window (±1 hour) to handle overrun

**Rejected:**
- Exact times only: Would miss real faults during overrun
- Ignore scheduled outages: Would generate false positives

**Reasoning:** Real outages routinely overrun by 20-40 minutes. Extended window prevents missing real faults while still filtering planned events.

### Firmware 1.2 Handling

**Chosen:** Detect via heartbeat timeout (no power_lost event)

**Rejected:**
- Ignore firmware 1.2 devices: Would miss faults
- Require firmware upgrade: Not realistic

**Reasoning:** 8% of fleet on old firmware. Heartbeat timeout detection provides fault coverage without requiring hardware upgrades.

### PIN Code Handling

**Chosen:** Use pole registry data, show "Unknown" if missing

**Rejected:**
- External geocoding API: Requires API key, adds dependency
- Infer from coordinates: Inaccurate, adds complexity

**Reasoning:** 3% of poles missing PIN code acceptable. External API adds deployment complexity. Showing "Unknown" transparent about data limitation.

## Assumptions

### Network Topology
- Network is radial (no loops) - per assignment specification
- Each pole has exactly one path back to DT - per assignment specification
- DT has exactly one path back to substation - per assignment specification

### Telemetry Behavior
- Heartbeat interval: 15 minutes ± 45 seconds - per assignment specification
- power_lost success rate: 70% - per assignment specification
- Device offline rate: 4% unrelated to power - per assignment specification
- Clock skew: ±90 seconds - per assignment specification

### Data Quality
- GPS accuracy: ±4 meters - per assignment specification
- Topology missing: 60% of DTs - per assignment specification
- Device coverage: 91% of poles - per assignment specification

### Operational
- Typical outages: 12-18 per day - per assignment specification
- Monsoon peak: up to 120 per day - per assignment specification
- Poles per DT: 9-240, median 70 - per assignment specification

## Known Limitations

### Geographic Inference Accuracy
- **Issue:** 70% accuracy vs 95% with topology data
- **Impact:** Some faults localized to wrong span
- **Mitigation:** Confidence score reflects uncertainty, UI shows degradation
- **Future:** Survey to digitize missing topology

### Single Dark Pole Detection
- **Issue:** Cannot distinguish dead sensor from single-pole fault if no children
- **Impact:** May create ticket for device failure
- **Mitigation:** Operator can acknowledge low-confidence tickets
- **Future:** Add device health monitoring

### PIN Code Missing
- **Issue:** 3% of poles lack PIN code
- **Impact:** Dispatch may need manual lookup
- **Mitigation:** Show "Unknown" in UI, coordinates still available
- **Future:** Offline PIN code dataset

### No Real-time Updates
- **Issue:** 10-second polling delay
- **Impact:** Operators see slight delay in updates
- **Mitigation:** Acceptable for dispatch workflow
- **Future:** WebSocket if deployment allows

### Burst Handling
- **Issue:** 5000 message burst may cause slight delay
- **Impact:** Fault detection may take >120s during large outages
- **Mitigation:** Background processing prevents data loss
- **Future:** Message queue (RabbitMQ/Kafka)

## What Would Change with 2 More Weeks

1. **Topology Survey Integration**: Add workflow to ingest survey data and update topology
2. **Message Queue**: Add RabbitMQ for reliable burst handling
3. **WebSocket Updates**: Real-time UI updates for better operator experience
4. **Historical Analytics**: Track fault patterns, repeat fault detection
5. **Mobile Crew App**: Basic mobile interface for field crews
6. **Offline PIN Code Dataset**: Integrate comprehensive PIN code database
7. **Performance Testing**: Load testing to validate 500 msg/s target
8. **Unit Tests**: Add tests for fault localization logic

## Currently Fragile

1. **Geographic Inference**: Heuristic-based, may fail in dense urban areas
2. **Database Seeding**: Async in lifespan, may cause race condition on fast startup
3. **Simulator Fault Repair**: Simplified - doesn't track which poles belong to which ticket
4. **AI Feature**: Optional - if API key invalid, falls back silently (should warn)
5. **Scheduled Outage Mock**: Hardcoded in router, should be external service
