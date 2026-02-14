# BOBBIE Build Plan
## Amazon Nova Pro + LangChain Implementation
## Hackathon Timeline: ~30 Days Remaining (Original 36-Day Sprint: Feb 8 - Mar 16, 2026)

**Last Updated:** February 14, 2026  
**Tech Stack:** AWS Bedrock (Nova Pro, 128K context), LangChain, Python 3.10+, AWS SDK  
**Target:** Working demo with 10 control assessments + 3-minute video

---

## Technical Architecture

### Core Technology Stack

```
┌─────────────────────────────────────────────────────┐
│                 BOBBIE Application                  │
├─────────────────────────────────────────────────────┤
│  Frontend (Optional)                                │
│  └─ Streamlit/Gradio Web UI                        │
├─────────────────────────────────────────────────────┤
│  LangChain Orchestration Layer                      │
│  ├─ Agent Executor (10 control agents)             │
│  ├─ Tool Integration (AWS APIs, EVTX parser)       │
│  ├─ Memory (Conversation buffer for multi-step)    │
│  └─ Output Parsers (Structured remediation)        │
├─────────────────────────────────────────────────────┤
│  Amazon Nova Pro (via AWS Bedrock)                  │
│  ├─ Model: amazon.nova-pro-v1:0                    │
│  ├─ Context: 128K tokens                            │
│  └─ Output: 8192 tokens max                        │
│  ├─ Temperature: 0.0 (deterministic)                │
│  └─ Max tokens: 4096                                │
├─────────────────────────────────────────────────────┤
│  Data Integration Layer                             │
│  ├─ AWS CloudWatch Logs API                         │
│  ├─ AWS Systems Manager API                         │
│  ├─ EVTX Parser (python-evtx)                      │
│  ├─ NIST NVD API Client                            │
│  ├─ CISA KEV JSON Parser                           │
│  ├─ OSCAL Validator (custom)                       │
│  └─ Mock Data Loaders (CSV/JSON)                   │
└─────────────────────────────────────────────────────┘
```

---

## Development Phases

### **Phase 1: Foundation (Days 1-5) — Core Setup**
**Goal:** Get Nova Pro + LangChain working with basic control logic

#### Day 1-2: Environment Setup
- [ ] AWS Bedrock setup & Nova Pro access verification
- [ ] Python virtual environment (`python -m venv bobbie-env`)
- [ ] Install dependencies:
  ```bash
  pip install langchain langchain-aws boto3 python-evtx pydantic
  pip install streamlit pandas python-dateutil requests
  ```
- [ ] GitHub repository initialization
- [ ] Project structure:
  ```
  bobbie/
  ├── src/
  │   ├── agents/           # LangChain agents for each control
  │   ├── tools/            # Custom tools (AWS, EVTX, OSCAL)
  │   ├── models/           # Pydantic data models
  │   ├── parsers/          # Log/config parsers
  │   └── utils/            # Helper functions
  ├── data/
  │   ├── mock/             # Mock CSV/JSON data
  │   ├── oscal_samples/    # NIST OSCAL SSPs
  │   └── evtx_samples/     # Sample Windows event logs
  ├── tests/                # Unit tests
  ├── app.py                # Streamlit UI
  └── run_assessment.py     # CLI entrypoint
  ```

#### Day 3-4: Nova Pro Integration via LangChain
**File: `src/models/nova_client.py`**
```python
from langchain_aws import ChatBedrock
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class ControlAssessment(BaseModel):
    control_id: str = Field(description="NIST 800-53 control ID (e.g., AC-2)")
    status: str = Field(description="PASS, FAIL, or NOT_APPLICABLE")
    findings: list[str] = Field(description="Specific issues found")
    recommendations: list[str] = Field(description="Remediation steps")
    risk_level: str = Field(description="LOW, MEDIUM, HIGH, CRITICAL")
    confidence_score: float = Field(description="Assessment confidence (0.0-1.0)")

class NovaAssessor:
    def __init__(self):
        self.llm = ChatBedrock(
            model_id="amazon.nova-pro-v1:0",
            model_kwargs={
                "temperature": 0.0,  # Deterministic for compliance
                "max_tokens": 8192,  # Nova Pro supports larger outputs
                "top_p": 0.9
            }
        )
        self.parser = PydanticOutputParser(pydantic_object=ControlAssessment)
        
    def assess_control(self, control_id: str, evidence: dict) -> ControlAssessment:
        prompt = ChatPromptTemplate.from_template("""
        You are BOBBIE, a federal security compliance assessor.
        
        Control: {control_id}
        Control Description: {description}
        
        Evidence Collected:
        {evidence}
        
        Assess this control according to NIST SP 800-53 Rev 5 requirements.
        
        {format_instructions}
        """)
        
        chain = prompt | self.llm | self.parser
        result = chain.invoke({
            "control_id": control_id,
            "description": self.get_control_description(control_id),
            "evidence": self.format_evidence(evidence),
            "format_instructions": self.parser.get_format_instructions()
        })
        return result
```

#### Day 5: First Control Prototype (PL-2: SSP Validation)
**File: `src/agents/pl2_agent.py`**
```python
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from src.tools.oscal_tool import OSCALValidatorTool
from src.models.nova_client import NovaAssessor

class PL2Agent:
    def __init__(self):
        self.assessor = NovaAssessor()
        self.tools = [
            OSCALValidatorTool(),
            Tool(
                name="CheckSections",
                func=self.check_required_sections,
                description="Validates SSP has all required OSCAL sections"
            ),
            Tool(
                name="ValidateControls",
                func=self.validate_control_coverage,
                description="Checks that all baseline controls have implementations"
            )
        ]
        
    def assess(self, ssp_path: str) -> ControlAssessment:
        # Load OSCAL SSP
        with open(ssp_path) as f:
            ssp_data = json.load(f)
        
        # Gather evidence using tools
        evidence = {
            "sections": self.check_required_sections(ssp_data),
            "control_coverage": self.validate_control_coverage(ssp_data),
            "metadata": self.extract_metadata(ssp_data)
        }
        
        # Use Nova to assess
        return self.assessor.assess_control("PL-2", evidence)
```

**Milestone 1 (Day 5):** Successfully assess PL-2 control with complete NIST sample SSP (5000+ lines in single invocation)

---

### **Phase 2: Core Controls (Days 6-18) — Build 10 Demo Controls**
**Goal:** Implement all 10 demo controls with deterministic logic + Nova reasoning

#### Day 6-8: OSCAL Document Analysis Controls
- [ ] **PL-2:** SSP Validation (already started)
  - Validate JSON schema
  - Check control implementation completeness
  - Cross-reference components
- [ ] **PM-9:** Risk Register Analysis
  - Parse OSCAL risk register
  - Validate risk scoring (L × I)
  - Check approval signatures

**File: `src/tools/oscal_tool.py`**
```python
from langchain.tools import BaseTool
import json
from typing import Dict, Any

class OSCALValidatorTool(BaseTool):
    name = "oscal_validator"
    description = "Validates OSCAL SSP structure and completeness"
    
    def _run(self, ssp_path: str) -> Dict[str, Any]:
        with open(ssp_path) as f:
            ssp = json.load(f)
        
        findings = []
        
        # Check required sections
        required = ['system-characteristics', 'control-implementation', 
                   'system-implementation', 'metadata']
        for section in required:
            if section not in ssp:
                findings.append(f"Missing required section: {section}")
        
        # Validate control coverage
        if 'control-implementation' in ssp:
            baseline = self._get_baseline_controls(ssp)
            implemented = [c['control-id'] for c in 
                          ssp['control-implementation']['implemented-requirements']]
            missing = set(baseline) - set(implemented)
            if missing:
                findings.append(f"Missing {len(missing)} baseline controls")
        
        return {"valid": len(findings) == 0, "findings": findings}
```

#### Day 9-12: AWS-Native Controls
- [ ] **SI-4:** System Monitoring (CloudWatch)
  - Query log streams for gaps
  - Detect volume anomalies
- [ ] **CM-8:** Asset Inventory (Systems Manager)
  - List managed instances
  - Cross-check with CSV
- [ ] **SI-2:** Flaw Remediation (SSM Patch Manager)
  - Query patch compliance
  - Cross-reference NIST NVD

**File: `src/tools/aws_tools.py`**
```python
import boto3
from langchain.tools import BaseTool
from datetime import datetime, timedelta

class CloudWatchLogTool(BaseTool):
    name = "cloudwatch_logs"
    description = "Queries AWS CloudWatch Logs for monitoring gaps"
    
    def __init__(self):
        self.client = boto3.client('logs')
    
    def _run(self, log_group: str, hours: int = 24) -> dict:
        # Check for log gaps
        start = int((datetime.utcnow() - timedelta(hours=hours)).timestamp() * 1000)
        end = int(datetime.utcnow().timestamp() * 1000)
        
        response = self.client.filter_log_events(
            logGroupName=log_group,
            startTime=start,
            endTime=end
        )
        
        # Bin into hourly buckets
        events_by_hour = {}
        for event in response['events']:
            hour = datetime.fromtimestamp(event['timestamp'] / 1000).hour
            events_by_hour[hour] = events_by_hour.get(hour, 0) + 1
        
        gaps = [h for h in range(24) if h not in events_by_hour]
        
        return {
            "total_events": len(response['events']),
            "gaps": gaps,
            "has_gaps": len(gaps) > 0
        }

class SSMInventoryTool(BaseTool):
    name = "ssm_inventory"
    description = "Queries AWS Systems Manager for instance inventory"
    
    def __init__(self):
        self.client = boto3.client('ssm')
    
    def _run(self, **kwargs) -> dict:
        response = self.client.describe_instance_information()
        instances = response['InstanceInformationList']
        
        return {
            "total_instances": len(instances),
            "instance_ids": [i['InstanceId'] for i in instances],
            "platform_types": [i['PlatformType'] for i in instances]
        }
```

#### Day 13-15: Local Log Analysis (EVTX)
- [ ] **AC-2:** Account Management
  - Parse Event 4720 (account created)
  - Match with mock tickets
- [ ] **AC-7:** Failed Logon Attempts
  - Parse Event 4625 (failed logon)
  - Detect lockout sequences
- [ ] **AU-3:** Audit Record Content
  - Validate required fields

**File: `src/parsers/evtx_parser.py`**
```python
import Evtx.Evtx as evtx
from datetime import datetime
from typing import List, Dict

class EVTXParser:
    def parse_security_log(self, evtx_path: str, event_ids: List[int]) -> List[Dict]:
        events = []
        with evtx.Evtx(evtx_path) as log:
            for record in log.records():
                xml = record.xml()
                event_id = self._extract_event_id(xml)
                if event_id in event_ids:
                    events.append({
                        "event_id": event_id,
                        "timestamp": record.timestamp(),
                        "data": self._parse_event_data(xml)
                    })
        return events
    
    def detect_failed_logon_sequences(self, evtx_path: str) -> List[Dict]:
        failed_logons = self.parse_security_log(evtx_path, [4625])
        lockouts = self.parse_security_log(evtx_path, [4740])
        
        # Group by username and time window
        sequences = []
        for username in set(e['data']['TargetUserName'] for e in failed_logons):
            user_fails = [e for e in failed_logons if e['data']['TargetUserName'] == username]
            # Check for >3 fails within 15min
            # ... (windowing logic)
        
        return sequences
```

#### Day 16-18: Mock Data Controls
- [ ] **IA-5:** Password Policy (JSON config)
  - Validate NIST 800-63B compliance
- [ ] **RA-5:** Vulnerability Scanning (mock scan results)
  - Check CVSS scores vs SLAs
  - Flag CISA KEV matches

**File: `src/tools/mock_data_tools.py`**
```python
import json
from langchain.tools import BaseTool
from datetime import datetime, timedelta

class PasswordPolicyTool(BaseTool):
    name = "password_policy_validator"
    description = "Validates password policy against NIST 800-63B"
    
    def _run(self, policy_path: str) -> dict:
        with open(policy_path) as f:
            policy = json.load(f)
        
        findings = []
        if policy.get('MinimumLength', 0) < 14:
            findings.append("Minimum length must be ≥14 characters")
        if not policy.get('ComplexityEnabled', False):
            findings.append("Complexity requirements must be enabled")
        if policy.get('MaximumAge', 365) > 60:
            findings.append("Maximum password age must be ≤60 days")
        if policy.get('PasswordHistory', 0) < 24:
            findings.append("Password history must track ≥24 passwords")
        
        return {"compliant": len(findings) == 0, "findings": findings}

class VulnerabilityTool(BaseTool):
    name = "vulnerability_scanner"
    description = "Checks vulnerability scan results against SLA thresholds"
    
    def _run(self, scan_results_path: str, cisa_kev_path: str) -> dict:
        with open(scan_results_path) as f:
            vulns = json.load(f)
        with open(cisa_kev_path) as f:
            kev = json.load(f)['vulnerabilities']
        
        kev_ids = {v['cveID'] for v in kev}
        
        sla_violations = []
        for vuln in vulns:
            days_open = (datetime.utcnow() - datetime.fromisoformat(vuln['discovered_date'])).days
            severity = vuln['cvss_score']
            
            sla = self._get_sla(severity)
            if days_open > sla:
                sla_violations.append({
                    "cve": vuln['cve'],
                    "days_open": days_open,
                    "sla": sla,
                    "in_kev": vuln['cve'] in kev_ids
                })
        
        return {"violations": sla_violations, "total_vulns": len(vulns)}
    
    def _get_sla(self, cvss):
        if cvss >= 9.0: return 15  # CRITICAL
        if cvss >= 7.0: return 30  # HIGH
        if cvss >= 4.0: return 90  # MODERATE
        return 180  # LOW
```

**Milestone 2 (Day 18):** All 10 controls implemented, tested individually, and parallel execution validated

---

### **Phase 3: Integration (Days 19-25) — Orchestration**
**Goal:** LangChain agent orchestration + unified assessment workflow

#### Day 19-21: Multi-Agent Orchestration
**File: `src/agents/orchestrator.py`**
```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.agents import *  # Import all control agents

class BOBBIEOrchestrator:
    def __init__(self):
        self.control_agents = {
            "PL-2": PL2Agent(),
            "PM-9": PM9Agent(),
            "SI-4": SI4Agent(),
            "CM-8": CM8Agent(),
            "SI-2": SI2Agent(),
            "AC-2": AC2Agent(),
            "AC-7": AC7Agent(),
            "AU-3": AU3Agent(),
            "IA-5": IA5Agent(),
            "RA-5": RA5Agent()
        }
        
        self.tools = self._create_tools()
        self.agent = self._create_master_agent()
    
    def _create_tools(self):
        # Wrap each control agent as a LangChain tool
        tools = []
        for control_id, agent in self.control_agents.items():
            tools.append(Tool(
                name=f"assess_{control_id}",
                func=agent.assess,
                description=f"Assesses {control_id} control compliance"
            ))
        return tools
    
    def _create_master_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are BOBBIE, coordinating security control assessments.
            You have access to 10 control assessment tools. Run all assessments and compile results."""),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def run_full_assessment(self, system_name: str) -> dict:
        results = {}
        for control_id, agent in self.control_agents.items():
            try:
                results[control_id] = agent.assess()
            except Exception as e:
                results[control_id] = {"error": str(e)}
        
        # Aggregate results
        summary = self._generate_summary(results)
        return {"system": system_name, "results": results, "summary": summary}
    
    def _generate_summary(self, results: dict) -> dict:
        total = len(results)
        passed = sum(1 for r in results.values() if r.get('status') == 'PASS')
        
        return {
            "total_controls": total,
            "passed": passed,
            "failed": total - passed,
            "compliance_score": round((passed / total) * 100, 1)
        }
```

#### Day 22-23: Output Generation
**File: `src/utils/report_generator.py`**
```python
import json
from datetime import datetime
from jinja2 import Template

class ReportGenerator:
    def generate_json_report(self, assessment: dict, output_path: str):
        """Generate JSON assessment report"""
        report = {
            "assessment_date": datetime.utcnow().isoformat(),
            "system_name": assessment['system'],
            "bobbie_version": "1.0-NOVA",
            "summary": assessment['summary'],
            "control_results": assessment['results']
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    def generate_poam(self, assessment: dict, output_path: str):
        """Generate POA&M from failed controls"""
        poam_items = []
        for control_id, result in assessment['results'].items():
            if result.get('status') == 'FAIL':
                poam_items.append({
                    "control_id": control_id,
                    "weakness": "; ".join(result['findings']),
                    "recommendations": result['recommendations'],
                    "risk_level": result['risk_level'],
                    "scheduled_completion": self._calculate_sla(result['risk_level'])
                })
        
        # Generate OSCAL POA&M JSON
        oscal_poam = {
            "plan-of-action-and-milestones": {
                "uuid": str(uuid.uuid4()),
                "metadata": {"title": f"POA&M for {assessment['system']}"},
                "poam-items": poam_items
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(oscal_poam, f, indent=2)
```

#### Day 24-25: Streamlit UI
**File: `app.py`**
```python
import streamlit as st
from src.agents.orchestrator import BOBBIEOrchestrator
from src.utils.report_generator import ReportGenerator

st.set_page_config(page_title="BOBBIE Assessment Engine", layout="wide")
st.title("🤖 BOBBIE: Federal Compliance Assessment")

# Sidebar for configuration
st.sidebar.header("Assessment Configuration")
system_name = st.sidebar.text_input("System Name", "Sample Federal System")

# Data source selection
st.sidebar.subheader("Data Sources")
oscal_ssp = st.sidebar.file_uploader("OSCAL SSP (JSON)", type="json")
evtx_file = st.sidebar.file_uploader("Windows Event Log (EVTX)", type="evtx")
mock_assets = st.sidebar.file_uploader("Asset Inventory (CSV)", type="csv")

# Run assessment
if st.sidebar.button("🚀 Run Assessment"):
    with st.spinner("BOBBIE is analyzing your system..."):
        orchestrator = BOBBIEOrchestrator()
        results = orchestrator.run_full_assessment(system_name)
    
    # Display summary
    st.header("Assessment Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Controls", results['summary']['total_controls'])
    col2.metric("Passed", results['summary']['passed'])
    col3.metric("Compliance Score", f"{results['summary']['compliance_score']}%")
    
    # Control-by-control results
    st.header("Control Results")
    for control_id, result in results['results'].items():
        with st.expander(f"{control_id}: {result.get('status', 'ERROR')}"):
            st.write("**Findings:**")
            for finding in result.get('findings', []):
                st.write(f"- {finding}")
            st.write("**Recommendations:**")
            for rec in result.get('recommendations', []):
                st.write(f"✓ {rec}")
    
    # Download reports
    st.header("Download Reports")
    report_gen = ReportGenerator()
    
    json_report = report_gen.generate_json_report(results, "bobbie_report.json")
    poam = report_gen.generate_poam(results, "bobbie_poam.json")
    
    st.download_button("📥 Download JSON Report", json_report, "bobbie_report.json")
    st.download_button("📥 Download POA&M", poam, "bobbie_poam.json")
```

**Milestone 3 (Day 25):** Functional end-to-end assessment with web UI

---

### **Phase 4: Demo Prep (Days 26-32) — Polish & Video**
**Goal:** Prepare demo video, polish UI, write documentation

#### Day 26-27: Testing & Validation
- [ ] Test with NIST sample SSPs
- [ ] Validate against manual assessments
- [ ] Fix bugs and edge cases
- [ ] Add error handling

**File: `tests/test_controls.py`**
```python
import pytest
from src.agents import *

def test_pl2_valid_ssp():
    agent = PL2Agent()
    result = agent.assess("data/oscal_samples/sample_ssp.json")
    assert result.status == "PASS"

def test_ac2_unauthorized_account():
    agent = AC2Agent()
    result = agent.assess("data/evtx_samples/security_unauthorized.evtx")
    assert result.status == "FAIL"
    assert any("unauthorized" in f.lower() for f in result.findings)
```

#### Day 28-29: Sample Data Generation
**File: `scripts/generate_mock_data.py`**
```python
import csv
import json
from datetime import datetime, timedelta
import random

def generate_asset_inventory(num_systems=50):
    systems = []
    for i in range(num_systems):
        systems.append({
            "hostname": f"fed-sys-{i:03d}.gov",
            "ip": f"10.0.{i//256}.{i%256}",
            "owner": random.choice(["ISSO", "SysAdmin", "DevOps"]),
            "classification": random.choice(["CUI", "PUBLIC", "CONFIDENTIAL"]),
            "os": random.choice(["Windows Server 2022", "RHEL 8", "Ubuntu 22.04"])
        })
    
    with open("data/mock/systems.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=systems[0].keys())
        writer.writeheader()
        writer.writerows(systems)

def generate_vulnerability_scan():
    vulns = []
    for i in range(100):
        discovered = datetime.utcnow() - timedelta(days=random.randint(1, 180))
        vulns.append({
            "cve": f"CVE-2025-{10000+i}",
            "cvss_score": round(random.uniform(2.0, 10.0), 1),
            "discovered_date": discovered.isoformat(),
            "affected_systems": [f"fed-sys-{random.randint(0,49):03d}.gov"]
        })
    
    with open("data/mock/mock_vulns.json", 'w') as f:
        json.dump(vulns, f, indent=2)

if __name__ == "__main__":
    generate_asset_inventory()
    generate_vulnerability_scan()
    print("✅ Mock data generated")
```

#### Day 30-32: Demo Video Production
**Script Outline:**
1. **Intro (0:00-0:30):** Problem statement — manual assessments take 2-4 weeks
2. **Solution (0:30-1:00):** Introduce BOBBIE + Amazon Nova Pro (128K context)
3. **Demo (1:00-2:30):** 
   - Load sample SSP → PL-2 validation
   - Upload EVTX → AC-2 account check
   - Show vulnerability scan → RA-5 SLA check
   - Generate POA&M
4. **Impact (2:30-3:00):** 70-85% cost reduction, continuous authorization

**Recording Steps:**
- [ ] Screen recording with OBS Studio
- [ ] Voiceover explaining each step
- [ ] Add captions
- [ ] Include #AmazonNova hashtag overlay
- [ ] Upload to YouTube (unlisted) for Devpost submission

**Milestone 4 (Day 32):** Demo video complete

---

### **Phase 5: Submission (Days 33-36) — Final Polish**
**Goal:** GitHub repo, blog post, Devpost submission

#### Day 33-34: GitHub Repository
- [ ] Clean up code
- [ ] Write comprehensive README.md
- [ ] Add installation instructions
- [ ] Include sample data files
- [ ] Add LICENSE (Apache 2.0 or MIT)
- [ ] Create demo walkthrough documentation

**README.md Structure:**
```markdown
# BOBBIE: Bot Oversight & Boundary Benchmarking Inference Engine

Amazon Nova Hackathon Submission | Agentic AI Category

## Overview
BOBBIE automates NIST SP 800-53 Rev 5 security control assessments...

## Demo Video
[3-minute walkthrough](https://youtu.be/...)

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure

# Run assessment
python run_assessment.py --system "My System"

# Launch web UI
streamlit run app.py
```

## Architecture
[Architecture diagram]

## Control Coverage
- PL-2: SSP Validation
- AC-2: Account Management
... (list all 10)

## Data Sources
- NIST OSCAL samples
- AWS CloudWatch/Systems Manager
- Local Windows Event Logs
- Mock CSV/JSON data

## Cost
- AWS: ~$5-10 (free tier eligible)
- Bedrock Nova Pro: ~$10-20 (128K context)
- Total: $15-30 for demo

```

#### Day 35: Blog Post for builder.aws.com
**Title:** "How BOBBIE Transforms Federal Compliance: From 4-Week Audits to 4-Hour Assessments"

**Outline:**
1. **The Problem:** Federal agencies struggle with manual NIST 800-53 assessments
2. **The Solution:** Agentic AI with Amazon Nova Pro (128K context) + LangChain
3. **Technical Deep Dive:** 
   - OSCAL document parsing
   - AWS CloudWatch log analysis
   - Deterministic + AI hybrid approach
4. **Results:** 70-85% cost reduction, continuous authorization enablement
5. **Future Work:** Scale to 48 controls, enterprise integrations
6. **Call to Action:** Try BOBBIE, contribute on GitHub

#### Day 36: Devpost Submission
- [ ] Complete all submission fields:
  - Project name: BOBBIE
  - Category: Agentic AI
  - Description: 250-word summary
  - Video URL: YouTube link
  - GitHub repo: Public link
  - Blog post: builder.aws.com link (if published)
- [ ] Test all links
- [ ] Final proofreading
- [ ] Submit by March 16, 2026 8:00 PM EDT

**Milestone 5 (Day 36):** Submission complete! 🎉

---

## Key Files Checklist

### Core Implementation
- [ ] `src/models/nova_client.py` — Nova Pro integration (128K context)
- [ ] `src/agents/orchestrator.py` — Multi-agent coordination
- [ ] `src/agents/pl2_agent.py` — SSP validation agent
- [ ] `src/agents/ac2_agent.py` — Account management agent
- [ ] `src/agents/ra5_agent.py` — Vulnerability assessment agent
- [ ] (7 more control agents)

### Tools & Parsers
- [ ] `src/tools/oscal_tool.py` — OSCAL validator
- [ ] `src/tools/aws_tools.py` — CloudWatch/SSM clients
- [ ] `src/parsers/evtx_parser.py` — Windows event log parser
- [ ] `src/tools/mock_data_tools.py` — CSV/JSON data loaders

### Data Generation
- [ ] `scripts/generate_mock_assets.py` — Asset CSV generator
- [ ] `scripts/generate_mock_tickets.py` — Approval tickets JSON
- [ ] `scripts/generate_mock_vulns.py` — Vulnerability scan results

### UI & Reporting
- [ ] `app.py` — Streamlit web interface
- [ ] `run_assessment.py` — CLI entrypoint
- [ ] `src/utils/report_generator.py` — JSON + POA&M output

### Documentation
- [ ] `README.md` — Installation & usage guide
- [ ] `ARCHITECTURE.md` — Technical architecture doc
- [ ] `DEMO.md` — Demo walkthrough steps
- [ ] `requirements.txt` — Python dependencies
- [ ] `LICENSE` — Open source license

---

## Dependencies (requirements.txt)

```
# Core LangChain + AWS
langchain==0.1.12
langchain-aws==0.1.3
boto3==1.34.59
botocore==1.34.59

# Data Processing
pydantic==2.6.3
pandas==2.2.1
python-dateutil==2.9.0

# Log Parsing
python-evtx==0.7.4

# API Clients
requests==2.31.0

# UI
streamlit==1.31.1

# Testing
pytest==8.1.1
pytest-cov==4.1.0

# Utilities
python-dotenv==1.0.1
```

---

## AWS Bedrock Configuration

**Model ID:** `amazon.nova-pro-v1:0` (or latest)

**Model Capabilities:**
- **Context Window:** 128K tokens (handles entire SSPs, multiple log files)
- **Output Tokens:** 8192 max (comprehensive assessment reports)
- **Temperature:** 0.0 for deterministic compliance assessments

**IAM Permissions Required:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "logs:DescribeLogStreams",
        "logs:FilterLogEvents",
        "ssm:DescribeInstanceInformation",
        "ssm:GetInventory",
        "ssm:DescribeInstancePatchStates"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Testing Strategy

### Unit Tests
- Each control agent has dedicated test
- Mock AWS API responses with `moto`
- EVTX test fixtures

### Integration Tests
- End-to-end assessment with sample data
- Validate JSON output format
- POA&M generation accuracy

### Manual Testing
- Run against real NIST OSCAL samples
- Compare results with manual assessment
- UI usability testing

---

## Risk Mitigation

### Risk: Nova Pro Context Management
**Mitigation:** 
- 128K context handles most SSPs complete
- Implement smart chunking only for extremely large documents (>100 pages)
- Use structured output parsing for consistent formatting

### Risk: AWS API Rate Limiting
**Mitigation:**
- Implement exponential backoff
- Cache repeated queriesNova Pro responses
- Budget buffer ($30 vs $20 target) for retry/testing
- Use batch operations where possible

### Risk: Demo Day Technical Issues
**Mitigation:**
- Pre-record video backup
- Test on clean AWS account
- Have offline demo with cached data

---

## Success Criteria

### Minimum Viable Demo (Must Have)
- [ ] 10 controls implemented
- [ ] Working Streamlit UI
- [ ] 3-minute demo video
- [ ] GitHub repo with README
- [ ] Devpost submission complete

### Strong Demo (Should Have)
- [ ] Sub-30 second assessment time (parallel execution)
- [ ] Clean, professional UI with real-time progress
- [ ] Comprehensive error handling
- [ ] Confidence scoring for each assessment
- [ ] Blog post published

### Exceptional Demo (Nice to Have)
- [ ] Live AWS integration demo
- [ ] Real-time assessment streaming
- [ ] Comparison with manual assessment time
- [ ] Testimonial from federal ISSO

---

## Timeline Summary

| Phase | Days | Milestone |
|-------|------|-----------|
| Foundation | 1-5 | Nova + LangChain working |
| Core Controls | 6-18 | 10 controls implemented |
| Integration | 19-25 | End-to-end orchestration |
| Demo Prep | 26-32 | Video & polish |
| Submission | 33-36 | GitHub + Devpost |

**Total Sprint:** 36 days (**~30 days remaining**)  
**Deadline:** March 16, 2026 8:00 PM EDT

---

## Next Steps (Start Today!)

1. **Set up AWS Bedrock access** → Request Nova Pro model access
2. **Create project structure** → Initialize Python project + GitHub repo
3. **Test Nova Pro** → Run simple prompt to verify access and test 128K context window
4. **Download NIST OSCAL samples** → Clone oscal-content repo

# Test Nova Pro access
python -c "
from langchain_aws import ChatBedrock
llm = ChatBedrock(model_id='amazon.nova-pro-v1:0')
print('✅ Nova Pro ready! 128K context available.')
on

**First Command to Run:**
```bash
mkdir bobbie && cd bobbie
python -m venv venv
source venv/bin/activate
pip install langchain langchain-aws boto3

# Test Nova Pro access
python -c "
from langchain_aws import ChatBedrock
llm = ChatBedrock(model_id='amazon.nova-pro-v1:0')
print('✅ Nova Pro ready! 128K context available.')
"
```

---

**Document Owner:** euCann LLC AI Security Architecture Division  
**Hackathon:** Amazon Nova AI Hackathon 2026  
**Category:** Agentic AI  
**Last Updated:** February 8, 2026
