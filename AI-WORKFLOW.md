# AI Workflow Documentation

## AI Tools Used

### Primary Tool: Cascade (Claude Code)
- **Usage:** 90% of code generation
- **Delegated:** Boilerplate, API endpoints, React components, Docker configuration
- **Manual:** Core fault localization algorithm, topology inference logic, verification logic

### Secondary Tool: OpenAI GPT-3.5-turbo
- **Usage:** Incident summary generation (runtime feature)
- **Delegated:** Natural language text generation
- **Manual:** Fallback template implementation

## What Was Delegated Wholesale

1. **Project Structure**: Docker compose, package.json, requirements.txt
2. **API Boilerplate**: FastAPI app setup, CORS, router structure
3. **Database Models**: SQLAlchemy models from schemas
4. **React Components**: UI structure, Tailwind classes, state management
5. **Simulator**: Synthetic data generation, fault injection logic
6. **Documentation**: README structure, deployment guide template

## What Was Written/Reviewed Manually

1. **Fault Detection Algorithm**: Core localization logic, topology inference
2. **Noise Handling**: Dead sensor detection, scheduled outage filtering
3. **Verification Logic**: Telemetry-based restoration verification
4. **Topology Strategy**: Geographic inference with confidence degradation
5. **AI Feature Decision**: Placement and justification for LLM usage

## Cases Where AI Was Wrong/Misleading

### Case 1: Topology Representation
**AI Suggestion:** Use NetworkX for all topology operations
**Issue:** Over-engineering for simple tree traversal
**Correction:** Used direct database queries with parent_pole_id when available, NetworkX only for complex operations
**Caught By:** Reviewing complexity - tree traversal is O(n) without graph library

### Case 2: Real-time Updates
**AI Suggestion:** Implement WebSockets for real-time UI
**Issue:** Adds deployment complexity (proxy configuration, cold-start issues)
**Correction:** Used 10-second polling instead
**Caught By:** Considering deployment constraints in DEPLOYMENT.md troubleshooting section

### Case 3: Geographic Inference
**AI Suggestion:** Use k-means clustering to group poles
**Issue:** Clustering doesn't respect radial network structure
**Correction:** Used distance-based boundary detection between live and dark poles
**Caught By:** Understanding physical network topology from problem context

### Case 4: AI Feature Placement
**AI Suggestion:** Use LLM for fault localization
**Issue:** Violates assignment guidance - graph traversal is superior
**Correction:** Used LLM only for natural language summaries
**Caught By:** Reading assignment FAQ which explicitly warns against LLM for localization

## Best AI Prompts/Sessions

### Prompt 1: Fault Detection Algorithm
```
"Implement a fault detection algorithm that:
1. Finds recent dark poles from telemetry
2. Groups them by time window and DT/feeder
3. Determines fault type (span/DT/feeder)
4. Localizes to specific span when topology available
5. Falls back to geographic inference when topology missing
6. Returns confidence score and reasoning

Handle the 60% missing topology case explicitly with degraded confidence."
```
**Why Good:** Clear requirements, explicit about the central design problem

### Prompt 2: React Operator Console
```
"Build an operator console UI for non-technical users at 2 AM:
- Show active incident count prominently
- List tickets with status badges
- Color-code confidence (green/yellow/red)
- Show AI summary when available
- Filter by workflow stage
- Detail panel for selected ticket with actions

Information hierarchy: status > location > severity > confidence > summary"
```
**Why Good:** Specific user persona, clear information hierarchy, explicit about what to include/omit

### Prompt 3: Simulator
```
"Build a fault simulator that:
1. Generates synthetic network matching assignment specs (20 DTs, ~70 poles each)
2. 60% of DTs missing topology data
3. 9% of poles without devices
4. Injects span/DT/feeder faults with realistic telemetry
5. 70% of power_lost messages arrive (30% lost)
6. 8% of devices on firmware 1.2 (no power_lost)
7. Injects noise: dead sensor, duplicates, out-of-order
8. Generates restoration telemetry on repair"
```
**Why Good:** Specific numbers from assignment, captures all edge cases

## AI-Generated Code Percentage

**Estimate: 75%**

- **AI-written (75%):**
  - Project structure and configuration
  - API endpoints and boilerplate
  - React UI components
  - Simulator data generation
  - Database models and migrations
  - Documentation structure

- **Human-written/reviewed (25%):**
  - Fault localization algorithm
  - Topology inference logic
  - Verification logic
  - Noise handling rules
  - AI feature integration
  - Architecture decisions

## Understanding the Code

### Can Explain Every File
- **main.py**: FastAPI app setup, lifespan management, router registration
- **models.py**: Database schema for poles, telemetry, tickets, transformers
- **fault_detector.py**: Core algorithm - grouping, localization, confidence calculation
- **telemetry_processor.py**: Triggers fault detection on power_lost events
- **verification.py**: Checks if poles are energized ticket resolution
- **simulator.py**: Synthetic network generation, fault injection
- **OperatorConsole.jsx**: React component for ticket management
- **FaultSimulator.jsx**: React component for testing

### Key Functions to Explain

**fault_detector._localize_span_geographically:**
- Takes dark poles and all poles in affected DT
- Finds live poles via recent telemetry
- Calculates distances between live and dark poles
- Returns closest live-dark pair as inferred fault location
- Confidence reduced to 70% due to inference

**fault_detector._determine_fault_type:**
- Checks if all poles under DT are dark → DT fault
- Checks if multiple DTs affected → feeder fault
- Otherwise → span fault
- Uses 90% threshold for DT fault detection

**verification.verify_restoration:**
- Gets poles in affected area
- Checks recent telemetry for energized status
- Returns false if any pole still dark
- Blocks manual resolution if not verified

## AI Workflow Process

1. **Read Assignment**: Thoroughly read all 6 markdown files
2. **Plan Architecture**: Decide on tech stack and approach
3. **Generate Structure**: Use AI for boilerplate and scaffolding
4. **Implement Core Logic**: Write critical algorithms manually
5. **Build Features**: Use AI for UI and secondary features
6. **Review and Refine**: Check AI output against requirements
7. **Document**: Write architecture and decisions manually
8. **Test**: Verify acceptance gates

## What AI Got Right

1. **FastAPI Structure**: Clean async patterns, proper dependency injection
2. **React Components**: Good use of hooks, proper state management
3. **Docker Configuration**: Correct multi-service setup, health checks
4. **Synthetic Data**: Realistic pole distribution, proper topology gaps
5. **API Design**: RESTful conventions, proper HTTP methods

## What Required Human Intervention

1. **Topology Strategy**: AI didn't grasp the 60% missing topology as central problem
2. **Confidence Scoring**: Needed explicit reasoning for confidence levels
3. **Noise Handling**: Required understanding of physical network constraints
4. **AI Feature Placement**: AI suggested LLM for localization (wrong per assignment)
5. **Verification Logic**: Needed to ensure telemetry-based blocking

## Conclusion

AI was highly effective for:
- Boilerplate and scaffolding
- UI implementation
- Data generation
- Documentation structure

Human input critical for:
- Core algorithm design
- Understanding physical constraints
- Making architectural tradeoffs
- Validating against assignment requirements

The combination allowed rapid development while ensuring correctness of the core fault localization logic.
