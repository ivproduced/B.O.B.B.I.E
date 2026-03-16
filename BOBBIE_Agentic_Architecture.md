# B.O.B.B.I.E. Agentic Architecture
### Bedrock-Orchestrated Baseline & Behavior Intelligence Engine
## Multi-Agent System Design for Federal Security Control Automation

**Last Updated:** February 14, 2026  
**Hackathon Deadline:** March 16, 2026 (~30 days remaining)  
**Project:** Amazon Nova Hackathon Submission  
**AI Model:** Amazon Nova Pro (128K context window)  
**Framework:** LangChain + AWS Bedrock

---

## Executive Summary

BOBBIE employs a **hierarchical multi-agent architecture** with 1 orchestrator agent coordinating **20 family agents** (1 per NIST control family). Each family agent evaluates one or more controls in its family using dedicated tools and data sources, enabling parallel execution for sub-30-minute full assessments.

**Key Design Principles:**
- **Autonomy:** Each family agent independently assesses controls in its assigned family
- **Specialization:** Agents tailored to specific data sources (OSCAL, AWS APIs, EVTX logs, mock data)
- **Parallelization:** Family agents execute simultaneously to minimize assessment time
- **Determinism:** Hybrid approach combining deterministic logic with Nova Pro reasoning
- **Modularity:** Family agents are plug-and-play for easy extension to 48+ controls

**Control Atomicity:** NIST controls are atomic and must be assessed by a single owning family agent. Individual control identifiers (e.g., `AC-2`) must not be split across multiple agents or families; any sub-requirement rollups happen inside the owning family agent. The orchestrator validates control assignment at run-time and agents verify routing to ensure auditability.
**Hackathon Scope Note:** The current demo activates 8 family agents (AC, AU, CM, IA, PL, PM, RA, SI) covering 10 controls.

---

## System Architecture Overview

```
╔═══════════════════════════════════════════════════════════════════════╗
║                        LAYER 0 · User Interface                       ║
║                                                                       ║
║   ┌─────────────────────────────┐   ┌─────────────────────────────┐   ║
║   │  CLI  ·  run_assessment.py  │   │  Web UI  ·  React + Express │   ║
║   └─────────────────────────────┘   └─────────────────────────────┘   ║
╚═══════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                    LAYER 1 · Master Orchestrator                      ║
║                                                                       ║
║   ┌───────────────────────────────────────────────────────────────┐   ║
║   │  BOBBIEOrchestrator                                           │   ║
║   │                                                               │   ║
║   │  · Validates control-to-family routing (atomicity enforced)   │   ║
║   │  · Dispatches family agents in parallel with timeout guard    │   ║
║   │  · Isolates agent failures — assessment never crashes         │   ║
║   │  · Aggregates findings → compliance score + POA&M             │   ║
║   │  · Nova Pro: cross-control synthesis & remediation narrative  │   ║
║   └───────────────────────────────────────────────────────────────┘   ║
╚═══════════════════════════════════════════════════════════════════════╝
                                     │
                         ┌───────────┴───────────┐
                         │   Parallel Dispatch   │
                         │   (8 active families) │
                         └───────────┬───────────┘
                                     │
                                     ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                  LAYER 2 · Family Assessment Agents                   ║
║                  (8 active · 20 target architecture)                  ║
╠═══════════════════════╦═══════════════════════╦═══════════════════════╣
║  OSCAL Documents      ║  AWS-Native           ║  Windows Event Logs   ║
║  ─────────────────    ║  ─────────────────    ║  ─────────────────    ║
║  PL2Agent             ║  SI4Agent             ║  AC2Agent             ║
║  · SSP validation     ║  · Monitoring gaps    ║  · Account mgmt       ║
║                       ║                       ║                       ║
║  PM9Agent             ║  CM8Agent             ║  AC7Agent             ║
║  · Risk register      ║  · Asset inventory    ║  · Failed logons      ║
║                       ║                       ║                       ║
║                       ║  SI2Agent             ║  AU3Agent             ║
║                       ║  · Patch / CVE SLA    ║  · Audit records      ║
╠═══════════════════════╩═══════════════════════╩═══════════════════════╣
║  Mock Data Validation                                                 ║
║  ───────────────────────────────────────────────────────────────────  ║
║  IA5Agent  ·  Password policy (NIST 800-63B)                          ║
║  RA5Agent  ·  Vulnerability scan SLA + CISA KEV matching              ║
╚═══════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                        LAYER 3 · Tool Layer                           ║
╠═══════════════════════════════════════════════════════════════════════╣
║  OSCALValidatorTool   → parse & validate OSCAL JSON                   ║
║  CloudWatchLogTool    → AWS CloudWatch Logs API                       ║
║  SSMInventoryTool     → AWS Systems Manager inventory                 ║
║  SSMPatchTool         → AWS Patch Manager compliance                  ║
║  EVTXParser           → Windows Event Log binary parser               ║
║  PasswordPolicyTool   → JSON schema validator (800-63B rules)         ║
║  VulnerabilityTool    → CVSS scoring + SLA enforcement                ║
║  NVDAPIClient         → NIST NVD CVE database                         ║
║  CISAKEVLoader        → Known Exploited Vulnerabilities catalog       ║
║  MockDataLoader       → CSV / JSON file parsers                       ║
╚═══════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                       LAYER 4 · Data Sources                          ║
╠═══════════════════════════════════════════════════════════════════════╣
║  NIST OSCAL Samples          · SSPs, risk registers (JSON)            ║
║  AWS CloudWatch Logs         · live log streams                       ║
║  AWS Systems Manager         · inventory + patch status               ║
║  Windows EVTX Files          · Security.evtx, System.evtx             ║
║  NIST NVD API                · nvd.nist.gov CVE data                  ║
║  CISA KEV Catalog            · known_exploited_vulnerabilities.json   ║
║  Mock Data Files             · systems.csv, password_policy.json      ║
╚═══════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                      LAYER 5 · Output Artifacts                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║  assessment_report.json  · machine-readable findings per control      ║
║  poam.json               · auto-generated POA&M with remediation      ║
║  assessment_summary.txt  · human-readable compliance scorecard        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## Agent Inventory

### **Layer 1: Master Orchestrator (1 Agent)**

#### **BOBBIEOrchestrator**
- **Role:** System coordinator and compliance report generator
- **Responsibilities:**
  - Dispatch assessment requests to active family agents
  - Manage parallel execution with timeout handling
  - Aggregate individual control results
  - Calculate overall compliance score
  - Generate POA&M entries for failures
  - Produce executive summary with remediation priorities
- **Tools Used:** Family agents wrapped as LangChain Tools (8 active in hackathon demo)
- **Nova Pro Usage:** 
  - Synthesize findings across controls
  - Generate context-aware remediation recommendations
  - Prioritize POA&M items by risk level
  - Create natural language compliance narrative
- **Implementation:** `src/agents/orchestrator.py`

---

### **Layer 2: Control Assessment Agents (10 Agents)**

#### **1. PL2Agent - SSP Validation**
- **Control:** PL-2 (System Security Plan)
- **Data Source:** NIST OSCAL sample SSPs (JSON)
- **Tools:** OSCALValidatorTool
- **Logic:**
  - Validate JSON schema compliance
  - Check all required sections present (system-characteristics, control-implementation, metadata)
  - Verify baseline controls have implementation statements
  - Cross-reference components mentioned in controls exist in inventory
  - Validate approval signatures and dates (<365 days)
  - Check for orphaned controls (no implementation)
- **Nova Pro Usage:** 
  - Semantic validation of implementation statement quality
  - Detect inconsistencies between control descriptions and implementations
- **Output:** ControlAssessment with findings + orphaned controls list
- **Implementation:** `src/agents/pl2_agent.py`

#### **2. PM9Agent - Risk Register Analysis**
- **Control:** PM-9 (Risk Management Strategy)
- **Data Source:** Mock OSCAL risk register (risk_register.json)
- **Tools:** OSCALValidatorTool, MockDataLoader
- **Logic:**
  - Validate risk score calculation (Likelihood × Impact)
  - Check all systems have risk assessments (<365 days)
  - Verify HIGH risks have mitigation plans
  - Validate AO approval for MODERATE+ risk acceptances
  - Cross-reference mitigations → POA&M items
- **Nova Pro Usage:**
  - Identify missing threat modeling methodologies
  - Assess quality of risk mitigation plans
- **Output:** ControlAssessment with risk coverage gaps
- **Implementation:** `src/agents/pm9_agent.py`

#### **3. SI4Agent - System Monitoring**
- **Control:** SI-4 (Information System Monitoring)
- **Data Source:** AWS CloudWatch Logs
- **Tools:** CloudWatchLogTool
- **Logic:**
  - Query log streams for 24-hour period
  - Bin events into 1-hour intervals
  - Flag gaps where event count = 0
  - Detect volume anomalies (>50% drop from baseline)
- **Nova Pro Usage:**
  - Distinguish legitimate gaps (maintenance windows) from monitoring failures
  - Recommend alerting thresholds
- **Output:** ControlAssessment with gap timestamps
- **Implementation:** `src/agents/si4_agent.py`

#### **4. CM8Agent - Asset Inventory**
- **Control:** CM-8 (Information System Component Inventory)
- **Data Source:** AWS Systems Manager Inventory + Mock CSV (systems.csv)
- **Tools:** SSMInventoryTool, MockDataLoader
- **Logic:**
  - Retrieve SSM managed instances
  - Load CSV asset inventory
  - Perform set operations: CSV ∩ SSM, CSV - SSM (orphans), SSM - CSV (shadow IT)
  - Validate required attributes (owner, boundary, classification)
- **Nova Pro Usage:**
  - Classify discrepancies (decommissioned vs. misconfigured vs. shadow IT)
  - Recommend inventory reconciliation actions
- **Output:** ControlAssessment with inventory delta report
- **Implementation:** `src/agents/cm8_agent.py`

#### **5. SI2Agent - Flaw Remediation**
- **Control:** SI-2 (Flaw Remediation)
- **Data Source:** AWS SSM Patch Manager + NIST NVD API
- **Tools:** SSMPatchTool, NVDAPIClient, CISAKEVLoader
- **Logic:**
  - Query SSM patch compliance status
  - Retrieve missing patches with CVE IDs
  - Query NVD for CVE severity scores and publish dates
  - Calculate days since publication
  - Apply SLA: CRITICAL (15d), HIGH (30d), MODERATE (90d), LOW (180d)
  - Cross-check against CISA KEV for known exploits
  - Check for compensating controls documentation
- **Nova Pro Usage:**
  - Assess compensating control adequacy
  - Recommend patch prioritization strategy
- **Output:** ControlAssessment with SLA violations + KEV flags
- **Implementation:** `src/agents/si2_agent.py`

#### **6. AC2Agent - Account Management**
- **Control:** AC-2 (Account Management)
- **Data Source:** Local Windows Event Logs (EVTX) + Mock approval tickets (JSON)
- **Tools:** EVTXParser, MockDataLoader
- **Logic:**
  - Parse Security.evtx for Event IDs: 4720 (created), 4722 (enabled), 4738 (modified)
  - Extract account details (username, timestamp, attributes)
  - Load mock approval tickets (JSON)
  - Match each account event to ticket within 24-hour window
  - Verify ticket has "ISSO_Approved": true
  - Validate account attributes match ticket specifications
- **Nova Pro Usage:**
  - Detect suspicious account patterns (bulk creation, privilege escalation)
  - Recommend approval workflow improvements
- **Output:** ControlAssessment with unauthorized accounts list
- **Implementation:** `src/agents/ac2_agent.py`

#### **7. AC7Agent - Failed Logon Attempts**
- **Control:** AC-7 (Unsuccessful Logon Attempts)
- **Data Source:** Local Windows Event Logs (EVTX)
- **Tools:** EVTXParser
- **Logic:**
  - Parse Security.evtx for Event IDs: 4625 (failed logon), 4740 (lockout)
  - Group failed logons by username + 15-minute time windows
  - Detect sequences of >3 failed logons
  - Verify lockout event (4740) follows within threshold
  - Calculate lockout enforcement rate
- **Nova Pro Usage:**
  - Identify potential brute-force attack patterns
  - Distinguish legitimate lockouts from policy violations
- **Output:** ControlAssessment with lockout enforcement statistics
- **Implementation:** `src/agents/ac7_agent.py`

#### **8. AU3Agent - Audit Record Content**
- **Control:** AU-3 (Content of Audit Records)
- **Data Source:** Local Windows Event Logs (EVTX) + AWS CloudWatch Logs
- **Tools:** EVTXParser, CloudWatchLogTool
- **Logic:**
  - Sample random logs (n=100)
  - Validate required fields: timestamp, event type, subject identity, outcome, source IP
  - Check for PII in logs (SSN/CCN regex patterns)
  - Calculate field completeness percentage
- **Nova Pro Usage:**
  - Detect sensitive data leakage patterns
  - Recommend log schema improvements
- **Output:** ControlAssessment with field completeness rate + PII detections
- **Implementation:** `src/agents/au3_agent.py`

#### **9. IA5Agent - Password Policy**
- **Control:** IA-5 (Authenticator Management)
- **Data Source:** Mock JSON config (password_policy.json)
- **Tools:** PasswordPolicyTool
- **Logic:**
  - Load password policy JSON
  - Validate NIST 800-63B compliance:
    - MinimumLength ≥ 14 characters
    - ComplexityEnabled = true
    - PasswordHistory ≥ 24
    - MaximumAge ≤ 60 days
  - Check for weak algorithms (DES, MD5)
- **Nova Pro Usage:**
  - Assess policy strength relative to threat landscape
  - Recommend modern authentication alternatives (MFA, passkeys)
- **Output:** ControlAssessment with policy violations
- **Implementation:** `src/agents/ia5_agent.py`

#### **10. RA5Agent - Vulnerability Scanning**
- **Control:** RA-5 (Vulnerability Monitoring and Scanning)
- **Data Source:** Mock vulnerability scan results (JSON) + CISA KEV
- **Tools:** VulnerabilityTool, CISAKEVLoader
- **Logic:**
  - Load mock_vulns.json
  - Calculate days_open for each vulnerability
  - Apply CVSS-based SLA (9.0+ → 15d, 7.0+ → 30d, 4.0+ → 90d, <4.0 → 180d)
  - Flag SLA violations
  - Cross-check CVE IDs against CISA KEV
  - Validate scan age ≤ 72 hours
  - Check asset coverage (all systems.csv entries scanned)
- **Nova Pro Usage:**
  - Prioritize vulnerabilities by exploitability + business impact
  - Recommend scanning frequency adjustments
- **Output:** ControlAssessment with SLA violations + KEV matches
- **Implementation:** `src/agents/ra5_agent.py`

---

## Agent Communication Patterns

### **1. Orchestrator → Control Agents (Fan-Out Pattern)**

```python
# Orchestrator dispatches to all agents in parallel
async def run_full_assessment(self, system_name: str) -> dict:
    # Create tasks for parallel execution
    tasks = [
        asyncio.create_task(self.control_agents["PL-2"].assess()),
        asyncio.create_task(self.control_agents["PM-9"].assess()),
        asyncio.create_task(self.control_agents["SI-4"].assess()),
        asyncio.create_task(self.control_agents["CM-8"].assess()),
        asyncio.create_task(self.control_agents["SI-2"].assess()),
        asyncio.create_task(self.control_agents["AC-2"].assess()),
        asyncio.create_task(self.control_agents["AC-7"].assess()),
        asyncio.create_task(self.control_agents["AU-3"].assess()),
        asyncio.create_task(self.control_agents["IA-5"].assess()),
        asyncio.create_task(self.control_agents["RA-5"].assess())
    ]
    
    # Wait for all agents to complete (with timeout)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return self._aggregate_results(results)
```

**Characteristics:**
- **Asynchronous:** All 10 agents execute simultaneously
- **Non-blocking:** No agent waits for another
- **Timeout handling:** 5-minute per-agent timeout to prevent hangs
- **Exception isolation:** Failed agent doesn't crash entire assessment

### **2. Control Agents → Tools (Direct Invocation)**

```python
# Each agent directly calls its tools
class PL2Agent:
    def __init__(self):
        self.oscal_tool = OSCALValidatorTool()
        self.llm = ChatBedrock(model_id="amazon.nova-pro-v1:0")
    
    def assess(self) -> ControlAssessment:
        # Step 1: Tool gathers evidence
        ssp_data = self.oscal_tool.validate_ssp("data/oscal_samples/ssp.json")
        
        # Step 2: Nova Pro reasons over evidence
        assessment = self.llm.invoke(
            f"Analyze SSP validation results: {ssp_data}. "
            f"Determine PASS/FAIL status and provide recommendations."
        )
        
        return ControlAssessment(
            control_id="PL-2",
            status=assessment.status,
            findings=assessment.findings,
            recommendations=assessment.recommendations
        )
```

**Characteristics:**
- **Synchronous tool calls:** Tools block until data retrieved
- **Sequential reasoning:** Tool → Nova Pro → Output
- **No inter-agent communication:** Agents don't share state

### **3. Agent Results → Orchestrator (Fan-In Pattern)**

```python
# Orchestrator aggregates all agent results
def _aggregate_results(self, results: list) -> dict:
    # Process individual assessments
    passed = [r for r in results if r.status == "PASS"]
    failed = [r for r in results if r.status == "FAIL"]
    
    # Generate compliance report
    report = {
        "system": self.system_name,
        "timestamp": datetime.utcnow().isoformat(),
        "total_controls": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "compliance_score": round((len(passed) / len(results)) * 100, 1),
        "control_results": {r.control_id: r.dict() for r in results},
        "executive_summary": self._generate_summary(results),
        "poam_entries": self._generate_poam(failed)
    }
    
    return report
```

**Characteristics:**
- **Synchronous aggregation:** Waits for all agents before reporting
- **Centralized scoring:** Orchestrator calculates compliance percentage
- **POA&M generation:** Only failed controls trigger remediation plans

---

## Execution Strategies

### **Strategy 1: Parallel Execution (Default - Hackathon Demo)**

**When to Use:** All agents assess independent controls with no shared state

```python
# Parallel execution for maximum speed
orchestrator = BOBBIEOrchestrator()
results = await orchestrator.run_full_assessment("Demo-System-001")
# Expected time: 15-30 minutes (all 10 agents simultaneously)
```

**Advantages:**
- **Fastest:** All agents run simultaneously
- **Scalable:** Adding agents doesn't increase wall-clock time (within reason)
- **Fault-tolerant:** Failed agent doesn't block others

**Disadvantages:**
- **Resource intensive:** 10 concurrent Nova Pro invocations
- **No inter-agent dependencies:** Can't have Agent B use Agent A's results

**Best For:** Hackathon demo, production continuous monitoring

---

### **Strategy 2: Sequential Execution (Fallback)**

**When to Use:** Resource-constrained environments, debugging

```python
# Sequential execution for lower resource usage
for control_id, agent in orchestrator.control_agents.items():
    result = agent.assess()
    print(f"{control_id}: {result.status}")
# Expected time: 30-45 minutes (agents run one-by-one)
```

**Advantages:**
- **Lower resource usage:** 1 Nova Pro invocation at a time
- **Easier debugging:** Clear sequential logs
- **Deterministic ordering:** Predictable execution sequence

**Disadvantages:**
- **Slower:** Linear time increase with agent count
- **Less impressive:** Doesn't showcase scalability

**Best For:** Development/testing, low-cost AWS accounts

---

### **Strategy 3: Grouped Execution (Future Production)**

**When to Use:** Phased assessments with dependencies

```python
# Execute in phases: Documents → Tech → Logs
async def run_phased_assessment(self):
    # Phase 1: Document analysis (fast, no external deps)
    doc_results = await asyncio.gather(
        self.agents["PL-2"].assess(),
        self.agents["PM-9"].assess()
    )
    
    # Phase 2: AWS controls (moderate speed, API rate limits)
    aws_results = await asyncio.gather(
        self.agents["SI-4"].assess(),
        self.agents["CM-8"].assess(),
        self.agents["SI-2"].assess()
    )
    
    # Phase 3: Log analysis (slow, large file parsing)
    log_results = await asyncio.gather(
        self.agents["AC-2"].assess(),
        self.agents["AC-7"].assess(),
        self.agents["AU-3"].assess()
    )
    
    # Phase 4: Mock data (fast, local files)
    mock_results = await asyncio.gather(
        self.agents["IA-5"].assess(),
        self.agents["RA-5"].assess()
    )
    
    return self._aggregate_all(doc_results + aws_results + log_results + mock_results)
```

**Advantages:**
- **Optimized resource usage:** Balance speed vs. cost
- **Dependency support:** Later phases can use earlier results
- **Graceful degradation:** If AWS fails, still get doc/log results

**Best For:** Production with 48+ controls, enterprise deployments

---

## State Management

### **Agent State (Stateless by Default)**

Each agent execution is **stateless** - no persistent memory between assessments.

```python
# Every assess() call is independent
agent = PL2Agent()
result1 = agent.assess()  # Fresh assessment
result2 = agent.assess()  # Another fresh assessment (no memory of result1)
```

**Rationale:**
- **Reproducibility:** Same input → same output
- **Parallelization:** No race conditions
- **Auditability:** Each assessment is self-contained

### **Orchestrator State (Transient Session)**

Orchestrator maintains **session state** during a single assessment run.

```python
class BOBBIEOrchestrator:
    def __init__(self):
        self.system_name = None
        self.start_time = None
        self.agent_results = {}
        self.errors = []
    
    def run_full_assessment(self, system_name: str):
        # Session state
        self.system_name = system_name
        self.start_time = datetime.utcnow()
        
        # ... run agents ...
        
        # Clear session state after report generation
        self._reset_session()
```

**Stored in Session:**
- System name being assessed
- Start timestamp
- Intermediate agent results
- Errors encountered

**Not Persisted:** Session state cleared after report generation

### **Persistence Layer (External to Agents)**

For production deployments, assessment history stored externally:

```python
# Future production feature
class AssessmentRepository:
    def save_assessment(self, report: dict):
        # Store in PostgreSQL, DynamoDB, or S3
        db.save({
            "system_id": report["system"],
            "timestamp": report["timestamp"],
            "compliance_score": report["compliance_score"],
            "results": json.dumps(report["control_results"])
        })
    
    def get_assessment_history(self, system_id: str, days: int = 30):
        # Retrieve historical assessments for trend analysis
        return db.query(system_id, days)
```

**Use Cases:**
- Compliance trend analysis over time
- Detect regression (control passed last month, fails today)
- Generate executive dashboards

---

## Error Handling & Resilience

### **Agent-Level Error Handling**

```python
class ControlAgentBase:
    def assess(self) -> ControlAssessment:
        try:
            # Normal assessment logic
            evidence = self.tool.gather_evidence()
            assessment = self.llm.analyze(evidence)
            return assessment
        
        except ToolExecutionError as e:
            # Tool failed (e.g., AWS API error, file not found)
            return ControlAssessment(
                control_id=self.control_id,
                status="ERROR",
                findings=[f"Data collection failed: {str(e)}"],
                recommendations=["Verify data source connectivity", "Check permissions"],
                confidence_score=0.0
            )
        
        except LLMInvocationError as e:
            # Nova Pro failed (rate limit, timeout, etc.)
            return ControlAssessment(
                control_id=self.control_id,
                status="ERROR",
                findings=[f"AI reasoning failed: {str(e)}"],
                recommendations=["Retry assessment", "Check AWS Bedrock quota"],
                confidence_score=0.0
            )
        
        except Exception as e:
            # Unexpected error
            logger.error(f"{self.control_id} assessment failed: {e}")
            return ControlAssessment(
                control_id=self.control_id,
                status="ERROR",
                findings=[f"Unexpected error: {str(e)}"],
                recommendations=["Review agent logs", "Contact support"],
                confidence_score=0.0
            )
```

**Error Types Handled:**
- **Data source errors:** API failures, file not found, permission denied
- **LLM errors:** Rate limits, timeouts, invalid model responses
- **Logic errors:** Unexpected data formats, null pointers

**Error Responses:**
- Return ERROR status instead of throwing exception
- Provide diagnostic findings
- Suggest remediation steps
- Set confidence_score = 0.0

### **Orchestrator-Level Error Handling**

```python
class BOBBIEOrchestrator:
    async def run_full_assessment(self, system_name: str) -> dict:
        results = []
        errors = []
        
        # Execute all agents with timeout
        tasks = [asyncio.create_task(agent.assess()) for agent in self.agents.values()]
        
        for task in asyncio.as_completed(tasks, timeout=300):  # 5-minute per-agent timeout
            try:
                result = await task
                results.append(result)
            except asyncio.TimeoutError:
                errors.append("Agent timeout - exceeded 5 minutes")
            except Exception as e:
                errors.append(f"Unexpected error: {str(e)}")
        
        # Generate report even with partial results
        if len(results) == 0:
            raise AssessmentFailedError("All agents failed - cannot generate report")
        
        report = self._aggregate_results(results)
        report["errors"] = errors
        report["partial_assessment"] = len(errors) > 0
        
        return report
```

**Resilience Features:**
- **Timeout protection:** 5-minute per-agent timeout prevents hangs
- **Partial results:** Generate report even if some agents fail
- **Error transparency:** Report includes error list for debugging
- **Graceful degradation:** System functional with 7/10 agents

---

## Scalability & Extensibility

### **Adding New Agents (Production: 10 → 48 Controls)**

**Step 1: Implement Agent Class**
```python
# src/agents/ac3_agent.py (Access Enforcement)
class AC3Agent(ControlAgentBase):
    control_id = "AC-3"
    
    def __init__(self):
        super().__init__()
        self.splunk_tool = SplunkQueryTool()  # New tool
    
    def assess(self) -> ControlAssessment:
        # Query Splunk for access denial events (Event 4656)
        denials = self.splunk_tool.query(
            "search index=windows EventCode=4656 | stats count by ObjectName"
        )
        
        # Nova Pro analyzes denial patterns
        assessment = self.llm.invoke(f"Analyze access denials: {denials}")
        return assessment
```

**Step 2: Register Agent in Orchestrator**
```python
# src/agents/orchestrator.py
class BOBBIEOrchestrator:
    def __init__(self):
        self.control_agents = {
            # Existing 10 agents...
            "AC-3": AC3Agent(),  # Add new agent
        }
```

**Step 3: No Other Changes Required**
- Orchestrator automatically includes in parallel execution
- Results automatically aggregated
- POA&M generation works for new control

**Scalability Analysis:**
- **Current:** 10 agents, 15-30 min assessment time
- **Production:** 48 agents, estimated 20-40 min assessment time (minimal increase due to parallelization)
- **AWS Bedrock limits:** 50 concurrent requests per account (sufficient for 48 agents)

### **Adding New Tools**

```python
# src/tools/servicenow_tool.py (Future production)
from langchain.tools import BaseTool

class ServiceNowCMDBTool(BaseTool):
    name = "servicenow_cmdb"
    description = "Queries ServiceNow CMDB for asset inventory"
    
    def __init__(self):
        self.client = ServiceNowClient(
            instance=os.getenv("SNOW_INSTANCE"),
            username=os.getenv("SNOW_USER"),
            password=os.getenv("SNOW_PASS")
        )
    
    def _run(self, table: str = "cmdb_ci_server") -> list:
        response = self.client.query(table, query="operational_status=1")
        return response.json()["result"]
```

**Integration into Agent:**
```python
# Agent can now use new tool
class CM8AgentProduction(CM8Agent):
    def __init__(self):
        super().__init__()
        self.servicenow_tool = ServiceNowCMDBTool()  # Replace mock CSV
```

### **Alternative Architectures Considered**

#### **Option A: Single Mega-Agent (Rejected)**
```
One agent with all 10 control logic
├─ Pros: Simpler code structure
└─ Cons: 
   • No parallelization
   • 128K context window insufficient for all data
   • Hard to maintain
   • Single point of failure
```

#### **Option B: Hierarchical Multi-Tier (Future Consideration)**
```
Orchestrator
├─ DocumentAgentSupervisor
│  ├─ PL2Agent
│  └─ PM9Agent
├─ AWSAgentSupervisor
│  ├─ SI4Agent
│  ├─ CM8Agent
│  └─ SI2Agent
└─ LogAgentSupervisor
   ├─ AC2Agent
   ├─ AC7Agent
   └─ AU3Agent
```
**When to Use:** 100+ controls requiring grouped coordination

#### **Option C: Event-Driven Agent Mesh (Future Research)**
```
Agents publish events to message queue
├─ PL2Agent publishes: "SSP validated, component list available"
├─ CM8Agent subscribes: "Use PL2's component list for cross-validation"
└─ Pros: True autonomy, agents discover each other
└─ Cons: Complex architecture, overkill for 48 controls
```

---

## Performance Benchmarks

### **Hackathon Demo Target (10 Controls)**

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Total Assessment Time** | 15-30 minutes | Parallel execution of all 10 agents |
| **Per-Agent Time** | 1-3 minutes | Nova Pro inference + tool execution |
| **Nova Pro Latency** | <2 seconds per invocation | 128K context, <500 tokens output |
| **Tool Execution** | <1 minute per tool | AWS API ~1s, EVTX parsing ~30s |
| **Orchestration Overhead** | <30 seconds | Result aggregation + POA&M generation |

### **Expected Production Performance (48 Controls)**

| Metric | Estimate | Scaling Factor |
|--------|----------|----------------|
| **Total Assessment Time** | 20-40 minutes | Minimal increase (parallel execution) |
| **AWS Bedrock Cost** | $1.50-3.00 per assessment | 48 agents × $0.03-0.06 per agent |
| **Throughput** | 25-50 assessments/day | Assumes 8-hour workday, sequential assessments |

### **Optimization Strategies**

1. **Agent Batching:** Group fast agents (IA-5, RA-5) to share Nova Pro session
2. **Tool Caching:** Cache NIST NVD queries for 24 hours (CVEs rarely change)
3. **Incremental Assessment:** Only re-assess controls with changed evidence
4. **Spot Instances:** Run orchestrator on AWS Lambda for cost efficiency

---

## Security & Compliance Considerations

### **Agent Security**

**Principle of Least Privilege:**
```python
# Each agent only has permissions for its required data sources
PL2Agent → Read-only OSCAL files (local filesystem)
SI4Agent → cloudwatch:DescribeLogStreams, cloudwatch:FilterLogEvents
CM8Agent → ssm:DescribeInstanceInformation
SI2Agent → ssm:DescribeInstancePatches, ssm:ListComplianceItems
```

**Credential Management:**
```bash
# AWS credentials via IAM roles (no hardcoded keys)
export AWS_PROFILE=bobbie-assessment-role

# Secrets in environment variables (not in code)
export NIST_NVD_API_KEY=<key>
```

### **Data Privacy**

**PII Redaction:**
```python
# AU3Agent redacts PII before sending to Nova Pro
def sanitize_logs(self, log_text: str) -> str:
    # Remove SSNs, credit card numbers
    log_text = re.sub(r'\d{3}-\d{2}-\d{4}', '[SSN-REDACTED]', log_text)
    log_text = re.sub(r'\d{4}-\d{4}-\d{4}-\d{4}', '[CCN-REDACTED]', log_text)
    return log_text
```

**Local Processing:**
- EVTX parsing happens locally (no logs sent to Nova Pro)
- Only analysis results sent to LLM, not raw log data

### **Auditability**

**Assessment Logging:**
```python
# Every agent logs inputs, outputs, decisions
logger.info(f"PL2Agent: Assessing SSP at {ssp_path}")
logger.info(f"PL2Agent: Found {len(missing_controls)} missing controls")
logger.info(f"PL2Agent: Status=FAIL, Confidence=0.95")
```

**Reproducibility:**
- All assessment inputs stored with results
- Re-running assessment with same inputs produces same output (deterministic)

---

## Development Roadmap

### **Phase 1: Hackathon Demo (~30 Days Remaining)**
- ✅ 1 orchestrator + 8 active family agents (covering 10 controls)
- ✅ Parallel execution
- ✅ Basic error handling
- ✅ CLI + Streamlit UI

### **Phase 2: Production MVP (Post-Hackathon Months 1-3)**
- Expand to 20 total family agents (1 per NIST family)
- Implement grouped execution strategy
- Add Splunk, ServiceNow integration
- Database persistence for assessment history

### **Phase 3: Enterprise (Months 4-6)**
- Scale to 33 agents (Tier 1 + Tier 2 controls)
- Hierarchical agent supervisors
- Real-time continuous monitoring
- API for external integrations

### **Phase 4: Advanced (Months 7-9)**
- 48+ agents (all automatable controls)
- Event-driven agent communication
- Machine learning for anomaly detection
- Multi-tenant support

---

## Production Readiness Addendum (Solutions Engineering)

### 1) Service-Level Objectives (SLOs)

| SLO Domain | Target | Measurement Window | Alert Threshold |
|-----------|--------|--------------------|-----------------|
| Assessment completion success | ≥99% | 7 days | <98% |
| Full assessment duration (10 controls) | P95 ≤ 30 min | 24 hours | P95 > 35 min |
| Agent timeout rate | <1% of agent runs | 24 hours | >2% |
| Evidence freshness compliance | ≥95% controls use fresh data | 24 hours | <90% |
| False positive rate (validated sample) | ≤10% | monthly QA set | >15% |

**Error Budget Policy:** If weekly success drops below 99% or timeout rate exceeds 2%, freeze feature work and run a reliability sprint.

### 2) Reliability Patterns to Implement

- **Queue-backed orchestration:** Place each control run on SQS (or equivalent) to decouple ingestion from execution.
- **Idempotency keys:** Use `assessment_id + control_id + evidence_hash` to prevent duplicate findings on retries.
- **Retry policy:** Exponential backoff for transient failures (AWS APIs, Bedrock throttling), max 3 attempts.
- **Circuit breaker:** Temporarily disable failing downstreams (e.g., NVD API) and mark control result as `DEGRADED`.
- **Graceful degradation:** Always produce report if ≥70% controls complete; include explicit partial-assessment banner.

### 3) Data Contracts & Schema Versioning

Define strict versioned schemas for:
- `ControlAssessment` output payloads
- Tool response payloads (CloudWatch, SSM, EVTX parser, NVD client)
- Final report + POA&M output

Use semantic versioning:
- `MAJOR`: breaking field change
- `MINOR`: additive field change
- `PATCH`: non-structural fix

**Release rule:** orchestrator only accepts agent payload versions in an allowlist.

### 4) Release Gates (CI/CD)

Promote to production only if all gates pass:
- **Contract tests:** 100% pass for all agent/tool schemas
- **Golden dataset regression:** no drop >2% in precision/recall vs baseline
- **Latency gate:** P95 assessment runtime ≤ SLO target
- **Cost gate:** average token cost per assessment within budget envelope
- **Security gate:** no high/critical IaC or dependency findings

### 5) Runbook (Operations)

#### Severity Definitions
- **SEV-1:** System unavailable, no report generation
- **SEV-2:** Partial results only, >30% agents failing
- **SEV-3:** Single integration degraded (e.g., NVD API outage)

#### First 15 Minutes Checklist
1. Confirm impacted scope (all tenants/systems vs single run)
2. Check Bedrock quotas, throttling, and recent deployment changes
3. Validate queue depth and worker health
4. Verify external dependency status (NVD, CISA, AWS APIs)
5. Trigger controlled rollback if release-correlated

#### Recovery Actions
- Restart failed workers and clear poisoned messages
- Enable fallback mode (cached evidence, grouped execution)
- Re-run failed controls using same idempotency key set
- Publish incident note with root-cause hypothesis and ETA

### 6) Observability Baseline

Capture and correlate:
- **Trace IDs:** one per assessment propagated across orchestrator/agents/tools
- **Metrics:** per-agent latency, error rate, retry count, token usage, cost
- **Logs:** structured JSON with `assessment_id`, `control_id`, `status`, `evidence_age`
- **Dashboards:** SLO board, control drift trends, top recurring failures, cost per run

### 7) Governance & Human-in-the-Loop

- Require human approval before publishing POA&M items for HIGH/CRITICAL findings
- Record decision provenance: evidence hash, model version, prompt version, approver identity
- Enforce retention and redaction policy for sensitive logs (PII/CUI)
- Maintain AO/ISSO audit export with immutable timestamps

### 8) Cost Management Controls

- Set per-agent token budget and hard fail-safe caps
- Cache stable lookups (NVD, KEV) with explicit TTL
- Route low-complexity controls to deterministic-only path when confidence is high
- Emit per-assessment cost report to finance/ops dashboard

---

## MVP vs Production Implementation Checklist

### MVP (Hackathon-Ready)

| Domain | Must Have | Exit Criteria |
|-------|-----------|---------------|
| Core orchestration | 1 orchestrator + family-agent routing (8 active families in demo) | All 10 controls execute and aggregate in one report |
| Execution mode | Parallel dispatch | Full run completes in ≤30 minutes (P95 target) |
| Error handling | Per-agent try/except + timeout | Failed agents return `ERROR` without crashing full run |
| Output | Standardized `ControlAssessment` + summary + POA&M | Report includes status for every control |
| Security | IAM least privilege + no hardcoded secrets | Secrets only from environment/role-based credentials |
| Logging | Structured logs with `assessment_id` and `control_id` | Every control run traceable end-to-end |
| Cost controls | Basic token and API call monitoring | Per-assessment cost visible in logs/report |
| Quality | Golden sample run for 10 controls | Manual review confirms acceptable findings quality |

### Production (Enterprise-Ready)

| Domain | Must Have | Exit Criteria |
|-------|-----------|---------------|
| Reliability | Queue-backed workers + retries + circuit breaker | Weekly success ≥99%, timeout rate <1% |
| Contracts | Versioned schemas with allowlist enforcement | 100% contract tests pass in CI/CD |
| Observability | Dashboards for SLOs, drift, cost, and failures | On-call can detect and triage in <15 minutes |
| Governance | Human approval for HIGH/CRITICAL POA&M publication | Approval trail captured with immutable timestamps |
| Data lifecycle | Retention, redaction, provenance policy | Audit export available for AO/ISSO review |
| Deployment safety | Release gates (latency, cost, quality, security) | No production deploy without gate pass |
| Scale path | 10 → 19 → 33 → 48 agents with staged rollout | Each stage meets SLO before next expansion |
| Resilience testing | Chaos/failure drills for dependencies and workers | Graceful degradation validated quarterly |

### 30/60/90 Day Execution Plan

#### Days 0-30 (Stabilize MVP)
- Lock schema for `ControlAssessment` and report output
- Add trace IDs and structured logging across orchestrator/tools
- Implement timeout and retry policy with bounded backoff
- Publish weekly quality/cost scorecard

#### Days 31-60 (Operationalize)
- Add queue-backed execution and idempotency keys
- Introduce CI/CD release gates (contract, latency, security)
- Implement runbook workflows and incident severity handling
- Add first production integration (e.g., ServiceNow or Splunk)

#### Days 61-90 (Scale Safely)
- Expand to next control tier (10 → 19 agents)
- Enable human approval flow for HIGH/CRITICAL outputs
- Add drift detection and regression evaluation pipeline
- Validate SLO compliance for 4 continuous weeks

### Go/No-Go Criteria for Production Pilot

- **GO** when all are true:
  - P95 runtime ≤30 minutes for pilot scope
  - Assessment success ≥99% over trailing 7 days
  - False positive rate ≤10% on validated dataset
  - Security and release gates pass without exceptions
  - On-call runbook tested with at least one incident simulation

- **NO-GO** if any are true:
  - Unknown schema/version mismatches in payloads
  - Unbounded retries or missing idempotency protections
  - No auditable approval trail for critical findings
  - Cost per assessment exceeds agreed budget envelope

---

## Conclusion

BOBBIE's **hierarchical multi-agent architecture** enables:
- **Autonomy:** Each agent specializes in one control type
- **Scalability:** Add agents without changing orchestrator
- **Speed:** Parallel execution achieves 15-30 minute assessments
- **Reliability:** Agent failures don't crash entire system
- **Extensibility:** 10 → 48 agents with minimal code changes

This architecture positions BOBBIE as a **production-ready** federal compliance automation platform, demonstrated through the hackathon's 10-control demo with a clear path to 48+ controls.

---

**Document Classification:** CUI // SP-CTI  
**Last Updated:** February 14, 2026  
**Owner:** euCann LLC — AI Security Architecture Division
