# BOBBIE: Bot Oversight & Boundary Benchmarking Inference Engine
## Amazon Nova Hackathon Submission — Agentic AI Category
## Target: 48 High-Value Technical & Document Analysis Controls

**Last Updated:** February 14, 2026  
**Hackathon Deadline:** March 16, 2026 (~30 days remaining)  
**AI Model:** Amazon Nova Pro (production-grade reasoning with 128K context for security control assessment)  
**Scope:** Deterministic automation of NIST SP 800-53 Rev 5 controls via LangChain + OSCAL document analysis  
**Data Sources (Hackathon Demo):** AWS CloudWatch Logs, AWS Systems Manager, Local Windows Event Logs, NIST NVD, CISA KEV, OSCAL sample repositories, Mock JSON/CSV data

---

## Executive Summary

**BOBBIE** is an agentic AI system powered by **Amazon Nova Pro** that automates federal security control assessments, providing:
- **Automated compliance validation** for 48 NIST SP 800-53 Rev 5 controls (24% coverage)
- **Deterministic reasoning** over logs, configurations, and OSCAL documents
- **Actionable remediation recommendations** with implementation steps
- **70-85% cost reduction** in assessment labor (2-4 weeks → 4-8 hours)
- **Continuous authorization enablement** for federal systems (FedRAMP, FISMA compliance)

**Enterprise Impact:** Federal agencies spend $200M+ annually on security control assessments. BOBBIE transforms manual, error-prone audits into continuous, automated oversight—reducing certification costs while improving security posture.

**Amazon Nova Pro Integration:** Uses Nova Pro's production-grade reasoning capabilities for:
- **OSCAL document analysis:** Complete SSP validation with 128K context window (handle 5000+ line documents)
- **Multi-source data synthesis:** Parallel processing of AWS logs, vulnerability scans, local event logs, CSV asset inventories
- **Complex control logic:** Advanced reasoning for multi-step decision trees and cross-referencing requirements
- **Remediation generation:** Context-aware fix recommendations with implementation steps and priority ranking

---

## Amazon Nova Pro: Why It Powers BOBBIE

**Nova Pro** is ideal for BOBBIE's mission because:
1. **128K context window** — processes entire OSCAL SSPs (5000+ lines), multiple log files, and cross-references in single assessment
2. **Production-grade accuracy** — critical for zero-tolerance federal compliance assessments
3. **Advanced reasoning** — complex multi-step control logic with branching decision trees (e.g., "If patch missing AND compensating control absent AND CVE is CRITICAL AND no compensating control documented → FAIL with specific remediation")
4. **Superior document understanding** — OSCAL JSON parsing, policy validation, architecture diagram analysis at scale
5. **Tool orchestration** — LangChain integration for AWS APIs, EVTX parsing, NVD lookups, CISA KEV checks
6. **Structured output generation** — POA&M entries, remediation recommendations, compliance reports with consistent formatting

**Technical Architecture (Hackathon Demo):**
```
┌─────────────────────────────────────────────────────┐
│           BOBBIE Assessment Engine                  │
├─────────────────────────────────────────────────────┤
│  Amazon Nova Pro (128K Context Window)              │
│  ↓                                                  │
│  LangChain Orchestration Layer                      │
│  ├─ AWS CloudWatch Logs Tool                        │
│  ├─ AWS Systems Manager Tool                        │
│  ├─ EVTX Parser Tool (Local Windows Logs)           │
│  ├─ NIST NVD API Tool (CVE Data)                    │
│  ├─ CISA KEV Tool (Known Exploits)                  │
│  ├─ OSCAL Validator Tool (NIST Sample SSPs)         │
│  └─ Mock Data Loaders (CSV/JSON)                    │
│  ↓                                                  │
│  10 Control Assessment Agents (Parallel Execution)  │
│  ↓                                                  │
│  Remediation Recommendation Generator               │
└─────────────────────────────────────────────────────┘
         ↓
    Assessment Report + POA&M + Fix Guidance
```

**Note:** Production version will support enterprise tools (Splunk, ServiceNow, Tenable). Hackathon demo uses accessible AWS services and mock data.

---

## Implementation Strategy

### Hackathon Timeline (~30 Days Remaining: Deadline Mar 16, 2026)
Focus: **10 high-impact control demo** proving BOBBIE's core assessment capability

### Production Roadmap (Post-Hackathon: 9 Months)
- **Tier 1 (Months 1-3):** 15-20 core technical controls — prove concept at scale
- **Tier 2 (Months 4-6):** 12-15 configuration/vulnerability controls — expand coverage
- **Tier 3 (Months 7-9):** 8-12 incident response/monitoring controls — continuous monitoring

### Hackathon Deliverables (~30 Days Remaining to Deadline: Mar 16, 2026)
✅ **Demo System:** Working prototype assessing 10 high-impact controls (see Demo Control List below)  
✅ **Nova Pro Integration:** Live demonstration of parallel control assessment with 128K context window  
✅ **Video Demo:** 3-minute walkthrough showing BOBBIE assessing a sample federal system (PL-2, AC-2, RA-5)  
✅ **GitHub Repository:** Open-source codebase with LangChain + AWS integrations, control logic, remediation templates  
✅ **Blog Post (Bonus Prize):** "How BOBBIE Transforms Federal Compliance: From 4-Week Audits to 4-Hour Assessments" on builder.aws.com

### Demo Control List (Hackathon Realistic Scope)
**OSCAL Document Analysis (No external tools needed):**
1. **PL-2:** SSP Validation — Parse NIST sample OSCAL SSP, validate structure/completeness
2. **PM-9:** Risk Register Analysis — Validate risk assessment completeness in OSCAL format

**AWS-Native Controls (Using CloudWatch, Systems Manager):**
3. **SI-4:** System Monitoring — Check AWS CloudWatch log streams for gaps
4. **CM-8:** Asset Inventory — Validate AWS Systems Manager Inventory completeness
5. **SI-2:** Flaw Remediation — Cross-reference AWS SSM Patch Manager against NIST NVD

**Local Log Analysis (Windows Event Logs EVTX files):**
6. **AC-2:** Account Management — Parse Windows Security Events 4720/4722 from EVTX files
7. **AC-7:** Failed Logon Attempts — Detect failed logon sequences (Event 4625) and lockouts (4740)
8. **AU-3:** Audit Record Content — Validate required fields in sample event logs

**Mock Data Validation (CSV/JSON):**
9. **IA-5:** Password Policy — Validate policy settings from JSON config file
10. **RA-5:** Vulnerability Scanning — Check mock vuln scan data against CVSS SLA thresholds

### Automation Criteria (BOBBIE Scope)
✅ **BOBBIE DOES:** Assess control compliance via objective evidence (logs, configs, OSCAL documents) + Provide remediation recommendations  
❌ **BOBBIE DOES NOT:** Draft/generate documents, make authorization decisions, perform physical inspections  
📊 **Assessment Types:**
- **Technical Controls:** Validate configurations, logs, vulnerability data against benchmarks
- **Document Controls:** Validate structure, completeness, consistency of OSCAL SSPs/policies/architectures
- **Remediation Guidance:** Provide specific fix recommendations with implementation steps

---

## Tier 1: Core Technical Controls (15-20 controls)
**Priority:** Critical | **Timeline:** Production Months 1-3 (Post-Hackathon) | **Automation Level:** High  
**Note:** 10 of these controls demonstrated in the current ~30-day remaining hackathon window

### Access Control (AC) — 6 controls

#### AC-2: Account Management ✅ HACKATHON DEMO
- **Description:** Validates account creation/modification against authorization tickets
- **Data Sources (Demo):** Local Windows Security Event Logs (EVTX files: Events 4720, 4722, 4738), Mock approval tickets (JSON)
- **Logic:** 
  - Parse EVTX for account creation events
  - Every account creation must have mock ticket JSON within 24h
  - Ticket must have "ISSO_Approved": true
  - Account attributes match ticket specifications
- **Pass Criteria:** 100% account events have authorized tickets with ISSO approval
- **Remediation SLA:** 7 days
- **Demo Implementation:** Python EVTX parser + JSON ticket matching

#### AC-3: Access Enforcement
- **Description:** Validates discretionary/mandatory access controls are enforced
- **Data Sources:** Splunk (access denial events 4656), Active Directory GPOs, file system ACLs
- **Logic:**
  - Check for unauthorized access attempts resulting in denials
  - Validate ACL inheritance is not broken
  - Confirm SELinux/AppArmor enforcement mode (Linux systems)
- **Pass Criteria:** Access denial events present, no ACL bypass indicators
- **Remediation SLA:** 3 days

#### AC-6: Least Privilege
- **Description:** Validates users/processes operate with minimum necessary privileges
- **Data Sources:** Splunk (privileged command execution sudo/runas), AD group memberships
- **Logic:**
  - Identify accounts with admin rights via AD query
  - Cross-check against ServiceNow authorized privileged user list
  - Flag generic admin accounts (not tied to individual)
  - Check for stale privileged accounts (no logon >90 days)
- **Pass Criteria:** All privileged access mapped to authorized users, no stale accounts
- **Remediation SLA:** 14 days

#### AC-7: Unsuccessful Logon Attempts ✅ HACKATHON DEMO
- **Description:** Enforces account lockout after failed authentication threshold
- **Data Sources (Demo):** Local Windows Event Logs (EVTX: Events 4625 failed logon, 4740 lockout)
- **Logic:**
  - Parse EVTX to detect sequences of >3 failed logons within 15min window
  - Verify lockout event (4740) follows within threshold period
- **Pass Criteria:** 100% of threshold breaches result in account lockout
- **Remediation SLA:** 3 days
- **Demo Implementation:** Python EVTX parser with time-series windowing

#### AC-11: Session Lock
- **Description:** Validates automatic session lock after inactivity period
- **Data Sources:** Splunk (Windows Events 4800 workstation locked), GPO settings
- **Logic:**
  - Query GPO for `ScreenSaveTimeOut` and `ScreenSaverIsSecure` settings
  - Verify timeout ≤ 15 minutes
  - Check for lock events during work hours (indicates enforcement)
- **Pass Criteria:** GPO enforces ≤15min timeout, events confirm activation
- **Remediation SLA:** 7 days

#### AC-17: Remote Access
- **Description:** Validates remote access sessions use encrypted protocols with MFA
- **Data Sources:** Splunk (VPN logs, RDP events 4624 with remote IP), MFA service logs
- **Logic:**
  - Identify remote access sessions (non-RFC1918 source IPs)
  - Check for weak protocols (Telnet port 23, FTP port 21, HTTP RDP)
  - Validate MFA challenge/response for each session
  - Verify VPN uses approved ciphers (AES-256, TLS 1.2+)
- **Pass Criteria:** All remote sessions use encrypted protocols + MFA
- **Remediation SLA:** 1 day (CRITICAL)

---

### Identification & Authentication (IA) — 4 controls

#### IA-2: Identification and Authentication (Organizational Users)
- **Description:** Validates unique identification and MFA for privileged/remote users
- **Data Sources:** AD authentication logs, MFA service (Duo/Okta) via API
- **Logic:**
  - Check that all privileged logons have MFA event correlation
  - Verify no shared accounts in use (same username, different source IPs simultaneously)
  - Validate PIV/CAC certificate authentication for federal users
- **Pass Criteria:** 100% privileged access uses MFA, no shared accounts detected
- **Remediation SLA:** 3 days

#### IA-4: Identifier Management
- **Description:** Validates unique identifiers are assigned and managed
- **Data Sources:** ServiceNow CMDB user records, AD user objects
- **Logic:**
  - Check for duplicate `sAMAccountName` or email addresses in AD
  - Verify terminated employees have identifiers disabled (match HR system)
  - Confirm identifier format follows naming convention (e.g., firstname.lastname)
- **Pass Criteria:** No duplicate identifiers, terminated users disabled within 24h
- **Remediation SLA:** 7 days

#### IA-5: Authenticator Management
- **Description:** Validates password complexity, rotation, and secure storage
- **Data Sources (Demo):** Mock JSON config file (password_policy.json), Local EVTX (password change events 4724)
- **Logic:**
  - Parse password_policy.json for:
    - Minimum length ≥ 14 characters
    - Complexity requirements enabled
    - Password history ≥ 24
    - Maximum age ≤ 60 days
  - Check for weak algorithms (flag if DES detected, require Kerberos AES256)
- **Pass Criteria:** Policy meets NIST 800-63B guidance, no weak algorithms
- **Remediation SLA:** 14 days
- **Demo Implementation:** JSON schema validation + NIST 800-63B compliance checker

#### IA-8: Identification and Authentication (Non-Organizational Users)
- **Description:** Validates external users (contractors, partners) use distinct identifiers
- **Data Sources:** AD guest accounts, VPN logs with external domains
- **Logic:**
  - Identify accounts with `UserType = Guest` or email domains outside org
  - Verify separate OU/group for external users
  - Check for elevated privileges on external accounts (should be minimal)
  - Validate sponsor/expiration date attributes populated
- **Pass Criteria:** All external users in designated group, no unexpected privileges
- **Remediation SLA:** 7 days

---

### System & Information Integrity (SI) — 4 controls

#### SI-2: Flaw Remediation
- **Description:** Validates timely installation of security patches
- **Data Sources (Demo):** NIST NVD API (CVE data), AWS Systems Manager Patch Manager, Mock patch logs (JSON)
- **Logic:**
  - Query AWS SSM for patch compliance status
  - Cross-reference against NIST NVD published CVEs
  - Calculate days since CVE publication
  - Apply severity-based SLA:
    - CRITICAL: 15 days
    - HIGH: 30 days
    - MODERATE: 90 days
  - Check mock data for compensating controls (firewall rules, IPS signatures) if patch delayed
- **Pass Criteria:** All CVEs within SLA or have documented compensating controls
- **Remediation SLA:** Severity-dependent
- **Demo Implementation:** AWS SSM API + NIST NVD API integration via Nova Pro LangChain agent

#### SI-3: Malicious Code Protection
- **Description:** Validates antivirus/EDR is installed, updated, and scanning
- **Data Sources:** Splunk (AV logs from Defender/CrowdStrike/Carbon Black)
- **Logic:**
  - Verify AV service running (Windows: `MsMpEng.exe`, Linux: `clamd`)
  - Check definition update age ≤ 7 days
  - Validate real-time protection enabled (not just scheduled scans)
  - Review quarantine/detection events for unresolved threats
- **Pass Criteria:** AV active, definitions current, no unresolved detections >3 days
- **Remediation SLA:** 1 day

#### SI-4: System Monitoring ✅ HACKATHON DEMO
- **Description:** Validates continuous security monitoring with no log gaps
- **Data Sources (Demo):** AWS CloudWatch Logs (log stream metadata)
- **Logic:**
  - Query CloudWatch for log streams over 24h period
  - Bin into 1-hour intervals, flag gaps where count=0
  - Check for anomalies: sudden drop in log volume (>50% baseline)
- **Pass Criteria:** No gaps >1 hour, consistent log volume
- **Remediation SLA:** 1 day
- **Demo Implementation:** AWS CloudWatch Logs Insights API via Nova Pro LangChain tool

#### SI-7: Software, Firmware, and Information Integrity
- **Description:** Validates integrity checking mechanisms (file integrity monitoring)
- **Data Sources:** Splunk (AIDE/Tripwire/Sysmon logs), code signing validation
- **Logic:**
  - Check for FIM solution deployed (`aide --version`, `osqueryd`)
  - Verify critical file paths in monitoring scope (/etc, /bin, Windows\System32)
  - Review integrity violation alerts (unauthorized file modifications)
  - Validate digitally signed executables (Windows: Authenticode, Linux: RPM signatures)
- **Pass Criteria:** FIM active, no unresolved integrity violations, code signing enforced
- **Remediation SLA:** 7 days

---

### Audit & Accountability (AU) — 5 controls

#### AU-2: Event Logging
- **Description:** Validates comprehensive audit event capture per 800-53 baseline
- **Data Sources:** Splunk (audit policy configuration queries)
- **Logic:**
  - Windows: Check `auditpol /get /category:*` output
    - Logon/Logoff: Success + Failure
    - Object Access: Failure
    - Policy Change: Success
    - Privilege Use: Failure
  - Linux: Verify `auditd` rules cover `/etc/passwd`, `/etc/shadow`, sudo commands
  - Application logs: Check for API authentication logs if web services present
- **Pass Criteria:** Audit policies match 800-53 requirements (Appendix J recommended events)
- **Remediation SLA:** 7 days

#### AU-3: Content of Audit Records
- **Description:** Validates audit records contain required data elements
- **Data Sources (Demo):** Local EVTX files (random sampling), AWS CloudWatch Logs
- **Logic:**
  - Parse random sample of logs (n=100)
  - Verify presence of:
    - Timestamp (with timezone)
    - Event type/ID
    - Subject identity (user/process)
    - Outcome (success/failure)
    - Source IP (if network event)
  - Check for PII redaction in logs (SSN, CCN patterns should not appear)
- **Pass Criteria:** ≥95% of logs contain all required fields, no PII in logs
- **Remediation SLA:** 14 days
- **Demo Implementation:** Python log parser + regex PII detection

#### AU-6: Audit Review, Analysis, and Reporting
- **Description:** Validates regular review of audit logs with SIEM alerting
- **Data Sources:** Splunk saved searches, alert configurations
- **Logic:**
  - Check for active Splunk correlation searches covering MITRE ATT&CK tactics
  - Verify alert frequency (at least weekly summary reports to ISSO)
  - Validate incident response playbook linkage (alerts trigger IR-4 workflow)
  - Check for stale alerts (triggered but never acknowledged >7 days)
- **Pass Criteria:** ≥10 correlation rules active, weekly reports configured, <5% stale alerts
- **Remediation SLA:** 14 days

#### AU-9: Protection of Audit Information
- **Description:** Validates audit logs are protected from unauthorized modification
- **Data Sources:** Splunk index permissions, AD group memberships, log file ACLs
- **Logic:**
  - Verify Splunk index permissions: only `admin` role can delete
  - Check log collection uses encrypted transport (TLS with Splunk Forwarder)
  - Validate log files on source systems have restrictive ACLs (SYSTEM/Administrators only)
  - Ensure log retention meets 90-day minimum (query _audit index)
- **Pass Criteria:** Logs write-once/append-only, retention ≥90 days, encrypted in transit
- **Remediation SLA:** 7 days

#### AU-12: Audit Record Generation
- **Description:** Validates systems generate audit records at critical points
- **Data Sources (Demo):** Mock CSV asset inventory, AWS CloudWatch log streams
- **Logic:**
  - Cross-reference two inventories:
    1. Mock CSV asset inventory (systems.csv)
    2. Active AWS CloudWatch log streams (last 24h)
  - Identify "orphan" systems in CSV not sending logs to CloudWatch
  - Check for critical event types missing (e.g., privileged command exec)
- **Pass Criteria:** ≥95% of CSV systems have CloudWatch log streams, critical events present
- **Remediation SLA:** 7 days
- **Demo Implementation:** CSV parser + AWS CloudWatch DescribeLogStreams API

---

## Tier 2: Configuration & Vulnerability Management (12-15 controls)
**Priority:** High | **Timeline:** Production Months 4-6 (Post-Hackathon) | **Automation Level:** High

### Risk Assessment (RA) — 5 controls

#### RA-3: Risk Assessment
- **Description:** Validates risk assessments conducted at required frequency
- **Data Sources (Demo):** Mock JSON risk register (risk_register.json), Mock CSV systems inventory
- **Logic:**
  - Query risk_register.json for each system in systems.csv
  - Check last assessment date ≤ 365 days (annual requirement)
  - Verify assessment includes threat modeling (STRIDE/ATT&CK mapping)
  - Validate AO approval signature field present
- **Pass Criteria:** Current risk assessment (<365 days) with AO approval
- **Remediation SLA:** 30 days (schedule new assessment)
- **Demo Implementation:** JSON schema validation + date arithmetic

#### RA-5: Vulnerability Monitoring and Scanning ✅ HACKATHON DEMO
- **Description:** Validates vulnerability scanning frequency and remediation SLAs
- **Data Sources (Demo):** Mock JSON vulnerability scan results, NIST NVD API, CISA KEV JSON
- **Logic:**
  - Parse mock_vulns.json for scan age ≤ 72 hours (continuous monitoring requirement)
  - Apply CVSS-based remediation SLAs (CRITICAL: 15d, HIGH: 30d, MODERATE: 90d, LOW: 180d)
  - Cross-check against CISA KEV for known exploited vulnerabilities (immediate flag)
  - Validate scan coverage (all systems.csv entries scanned)
- **Pass Criteria:** Scans current, no SLA breaches, ≥98% asset coverage
- **Remediation SLA:** Severity-dependent
- **Demo Implementation:** JSON parsing + NIST NVD API + CISA KEV catalog integration

#### RA-5(1): Update Vulnerability Scanning Tool Capability
- **Description:** Validates vulnerability scanner has current vulnerability definitions
- **Data Sources:** Tenable/Qualys API (plugin version, last update timestamp)
- **Logic:**
  - Query scanner plugin/feed version
  - Compare against NIST NVD latest publication date
  - Verify auto-update configured
  - Check plugin age ≤ 7 days
- **Pass Criteria:** Scanner plugins updated within 7 days
- **Remediation SLA:** 3 days

#### RA-5(2): Update Vulnerabilities to be Scanned
- **Description:** Validates scanning prior to new system deployment
- **Data Sources:** ServiceNow change records, vulnerability scan reports
- **Logic:**
  - Identify new CIs (created_date within last 30 days)
  - Check for vulnerability scan within 7 days of CMDB record creation
  - Verify scan before "Production" status transition
- **Pass Criteria:** 100% of new systems scanned before production deployment
- **Remediation SLA:** Block deployment

#### RA-5(5): Vulnerability Scanning - Privileged Access
- **Description:** Validates authenticated/credentialed scanning is used
- **Data Sources:** Tenable/Qualys scan configurations
- **Logic:**
  - Query scan profiles for credential usage
  - Check for "Credentialed Scan: YES" in scan metadata
  - Verify privileged account used (not guest/anonymous)
  - Validate scan discovered internal services (checks actual authentication success)
- **Pass Criteria:** 100% of scans use credentials, authentication success rate ≥95%
- **Remediation SLA:** 7 days

---

### Configuration Management (CM) — 6 controls

#### CM-2: Baseline Configuration
- **Description:** Validates approved baseline configurations exist and are enforced
- **Data Sources:** ServiceNow (baseline documents), Ansible Tower/SCCM configs
- **Logic:**
  - Check for approved baseline document in ServiceNow per OS type
  - Verify baseline includes CIS Benchmark or DISA STIG reference
  - Validate AO/ISSO approval on baseline (within 365 days)
  - Cross-check systems against baseline (using CM-6 compliance scans)
- **Pass Criteria:** Baseline documented, approved (<365d), ≥90% systems compliant
- **Remediation SLA:** 30 days

#### CM-3: Configuration Change Control
- **Description:** Validates changes follow approval workflow
- **Data Sources:** ServiceNow change records, Git commit logs, AD audit logs
- **Logic:**
  - Identify configuration changes (AD GPO modifications, system patches, app deployments)
  - Match each change to ServiceNow Change Request (CHG) ticket
  - Verify CAB/ISSO approval on ticket before change timestamp
  - Flag emergency changes without retroactive approval (≤24h grace period)
- **Pass Criteria:** ≥95% of changes have approved tickets, emergency changes approved post-facto
- **Remediation SLA:** 14 days (document as exception)

#### CM-6: Configuration Settings ✅ HACKATHON DEMO
- **Description:** Validates system configurations meet security benchmarks
- **Data Sources (Demo):** AWS Systems Manager State Manager (compliance data), Mock CIS scan results (JSON)
- **Logic:**
  - Query AWS SSM State Manager for configuration compliance
  - Parse mock CIS scan results (mock_cis_scan.json)
  - Calculate percentage compliant with applicable baseline (CIS Level 1 minimum)
  - Flag high-severity misconfigurations (score ≤ 70%)
  - Check for drift from last scan (new failures)
- **Pass Criteria:** Compliance score ≥95%
- **Remediation SLA:** 14 days
- **Demo Implementation:** AWS SSM API + JSON CIS benchmark parser

#### CM-7: Least Functionality
- **Description:** Validates unnecessary services/protocols are disabled
- **Data Sources:** Splunk (netstat/ss output, Windows services), Nmap scan results
- **Logic:**
  - Check for prohibited services running:
    - Telnet (port 23)
    - FTP (port 21)
    - TFTP (port 69)
    - SNMP v1/v2 (port 161) — should be SNMPv3
  - Validate only required ports open (compare against ServiceNow approved port list)
  - Check for unnecessary OS features installed (Windows: IIS on non-web, SMBv1)
- **Pass Criteria:** No prohibited services, only approved ports open
- **Remediation SLA:** 7 days

#### CM-8: Information System Component Inventory
- **Description:** Validates complete and accurate asset inventory exists
- **Data Sources (Demo):** Mock CSV asset inventory (systems.csv), AWS Systems Manager Inventory, AWS CloudWatch log source IPs
- **Logic:**
  - Cross-reference three inventories:
    1. Mock CSV asset inventory (systems.csv)
    2. AWS Systems Manager managed instances
    3. AWS CloudWatch log source IPs (last 24h)
  - Flag discrepancies:
    - Systems in CloudWatch but not CSV (shadow IT)
    - Systems in CSV but not logging (potentially offline/decommissioned)
  - Verify critical attributes populated (owner, boundary, data classification)
- **Pass Criteria:** ≥98% agreement between inventories, all entries have required attributes
- **Remediation SLA:** 14 days
- **Demo Implementation:** CSV parser + AWS SSM/CloudWatch APIs + set operations

#### CM-11: User-Installed Software
- **Description:** Validates software installation controls are enforced
- **Data Sources:** Splunk (Windows Events 11707 software install, Linux package manager logs)
- **Logic:**
  - Identify software installation events outside approved deployment tools (SCCM/Ansible)
  - Check for user-initiated installs (non-SYSTEM account)
  - Validate installed software against approved whitelist (ServiceNow)
  - Flag high-risk categories: remote access tools, P2P, browsers (if not approved)
- **Pass Criteria:** ≥95% software installs via approved deployment, no prohibited software
- **Remediation SLA:** 7 days

---

### System & Communications Protection (SC) — 3 controls

#### SC-7: Boundary Protection
- **Description:** Validates firewall rules restrict traffic to authorized flows
- **Data Sources:** Splunk (firewall deny logs), ServiceNow (approved connections)
- **Logic:**
  - Query firewall deny events for boundary devices
  - Check for outbound connections to unexpected countries (GeoIP)
  - Validate deny rate (should have denials — indicates firewall actively filtering)
  - Cross-check allowed flows against ServiceNow network diagram
  - Flag overly permissive rules (0.0.0.0/0 destinations that aren't internet egress proxies)
- **Pass Criteria:** Active denials present, no unauthorized flows, no overly broad rules
- **Remediation SLA:** 3 days

#### SC-8: Transmission Confidentiality and Integrity
- **Description:** Validates encrypted protocols for sensitive data transmission
- **Data Sources:** Splunk (network traffic metadata, TLS handshake logs from SSL inspection)
- **Logic:**
  - Identify unencrypted protocols in use:
    - HTTP (port 80) for applications handling PII/PHI/CUI
    - SMTP (port 25) without STARTTLS
    - LDAP (port 389) instead of LDAPS (636)
  - Validate TLS versions ≥ 1.2
  - Check cipher suites (must exclude weak: 3DES, RC4, MD5)
- **Pass Criteria:** Sensitive data only transmitted over encrypted channels (TLS 1.2+)
- **Remediation SLA:** 7 days

#### SC-28: Protection of Information at Rest
- **Description:** Validates encryption of sensitive data at rest
- **Data Sources:** ServiceNow (encryption status attribute), Splunk (BitLocker/dm-crypt logs)
- **Logic:**
  - Query CMDB for systems with PII/PHI/CUI data classifications
  - Check encryption status:
    - Windows: BitLocker enabled (`manage-bde -status`)
    - Linux: LUKS partition present (`cryptsetup status`)
    - Cloud: AWS EBS encryption, Azure disk encryption enabled
  - Verify key management (keys not stored on same system as encrypted data)
- **Pass Criteria:** 100% of CUI/PII/PHI systems have full-disk or volume encryption
- **Remediation SLA:** 14 days

---

## Tier 3: Incident Response & Monitoring (8-12 controls)
**Priority:** Medium | **Timeline:** Production Months 7-9 (Post-Hackathon) | **Automation Level:** Medium

### Incident Response (IR) — 4 controls

#### IR-4: Incident Handling
- **Description:** Validates incidents are detected, reported, and tracked
- **Data Sources:** ServiceNow (INC incident tickets), Splunk (SIEM alerts)
- **Logic:**
  - Check for automated ticket creation from Splunk alerts (via integration)
  - Verify incident categorization (security vs. operational)
  - Validate incident response SLAs met:
    - HIGH: acknowledge within 1 hour, resolve within 24 hours
    - MEDIUM: acknowledge within 4 hours, resolve within 72 hours
  - Check for incident commander assignment (required for HIGH severity)
- **Pass Criteria:** 100% of SIEM alerts create tickets, ≥95% meet SLA
- **Remediation SLA:** Immediate (for ongoing incident)

#### IR-5: Incident Monitoring
- **Description:** Validates incidents are tracked with metrics reported to management
- **Data Sources:** ServiceNow reporting module, Splunk dashboards
- **Logic:**
  - Verify incident dashboard exists showing:
    - Open incidents by severity
    - Mean time to detect (MTTD)
    - Mean time to respond (MTTR)
    - Recurring incident patterns
  - Check for monthly ISSO report generation (automated email)
  - Validate trend analysis (incidents increasing/decreasing)
- **Pass Criteria:** Dashboard published, monthly reports sent, trend analysis performed
- **Remediation SLA:** 30 days (implement reporting)

#### IR-6: Incident Reporting
- **Description:** Validates incidents are reported to appropriate authorities
- **Data Sources:** ServiceNow (incident notifications), US-CERT reporting records
- **Logic:**
  - Identify HIGH severity incidents involving PII/CUI
  - Check for notifications sent:
    - Internal: CISO, AO, System Owner (within 1 hour)
    - External: US-CERT (within 1 hour for federal systems, per US-CERT-IR enhancement)
  - Verify breach reporting timeline (federal agencies: ≤72 hours)
  - Validate notification templates contain required elements (NIST 800-61 Section 3.2.7)
- **Pass Criteria:** 100% reportable incidents have notifications within required timeframes
- **Remediation SLA:** N/A (retroactive reporting if missed)

#### IR-8: Incident Response Plan
- **Description:** Validates current incident response plan exists
- **Data Sources:** ServiceNow (IRP document repository)
- **Logic:**
  - Check for IRP document existence
  - Verify last review date ≤ 365 days
  - Confirm AO approval signature present
  - Validate plan includes required elements:
    - Roles and responsibilities (CSIRT structure)
    - Incident categories and severity definitions
    - Reporting procedures (internal/external)
    - Communication templates
- **Pass Criteria:** IRP exists, reviewed annually, contains required sections
- **Remediation SLA:** 60 days (update plan)

---

### Contingency Planning (CP) — 3 controls

#### CP-2: Contingency Plan
- **Description:** Validates contingency plan exists and is tested
- **Data Sources:** ServiceNow (CP document repository, test records)
- **Logic:**
  - Check for contingency plan document per system
  - Verify last review date ≤ 365 days
  - Confirm annual test conducted (tabletop or functional)
  - Validate plan includes:
    - Recovery Time Objective (RTO)
    - Recovery Point Objective (RPO)
    - Essential functions prioritization
    - Alternate processing site details
- **Pass Criteria:** CP exists, tested annually, AO-approved
- **Remediation SLA:** 60 days

#### CP-9: System Backup
- **Description:** Validates backups are performed and tested
- **Data Sources:** Splunk (backup job logs from Veeam/Commvault), ServiceNow
- **Logic:**
  - Check for daily backup job completion events
  - Verify backup success rate ≥99% over 30-day period
  - Validate offsite replication (backups stored at alternate location)
  - Check for quarterly restore test records in ServiceNow
  - Verify encryption of backup data at rest
- **Pass Criteria:** Daily backups successful, quarterly restore tests passed, encrypted
- **Remediation SLA:** 3 days (for failed backups)

#### CP-10: System Recovery and Reconstitution
- **Description:** Validates recovery procedures are documented and tested
- **Data Sources:** ServiceNow (recovery procedure documents, test records)
- **Logic:**
  - Check for recovery procedure documentation
  - Verify procedures include step-by-step recovery tasks
  - Validate annual recovery test conducted (actual restore to alternate site)
  - Check test results meet RTO/RPO targets defined in CP-2
  - Verify post-recovery validation checklist (integrity verification)
- **Pass Criteria:** Procedures documented, annual test passed, RTO/RPO met
- **Remediation SLA:** 60 days

---

### Additional System & Information Integrity (SI) — 2 controls

#### SI-5: Security Alerts, Advisories, and Directives
- **Description:** Validates system receives and responds to security advisories
- **Data Sources:** US-CERT subscription status, ServiceNow (advisory tracking)
- **Logic:**
  - Verify organization subscribed to US-CERT advisories
  - Check for ISSO assigned to monitor advisories (ServiceNow user role)
  - Validate advisory disposition process:
    - Each advisory reviewed within 5 business days
    - Impact assessment documented ("Applicable" or "Not Applicable")
    - Applicable advisories result in incident tickets or change requests
  - Check for automated parsing of CVE references in advisories (link to RA-5)
- **Pass Criteria:** Subscriptions active, 100% of advisories reviewed, remediation tracked
- **Remediation SLA:** 5 days (per advisory)

#### SI-12: Information Handling and Retention
- **Description:** Validates data retention policies are enforced
- **Data Sources:** Splunk (log retention settings), ServiceNow (record lifecycle)
- **Logic:**
  - Check Splunk index retention settings:
    - Security logs: ≥90 days hot, ≥1 year archive (per NIST 800-92)
    - Audit logs: ≥1 year (per most federal regulations)
  - Verify data destruction process for end-of-life systems
  - Validate records management policy document exists (NIST 800-88 media sanitization)
  - Check for automatic disposition (ServiceNow records auto-archive after retention period)
- **Pass Criteria:** Retention meets regulatory minimums, destruction process documented
- **Remediation SLA:** 30 days

---

## Summary Statistics

| Scope | Controls | Automation Level | Timeline | Primary Data Sources |
|------|----------|------------------|----------|---------------------|
| **Hackathon Demo** | **10** | High (90%+) | **~30 days remaining** | AWS CloudWatch, SSM, EVTX files, OSCAL samples, mock JSON/CSV |
| **Production Tier 1** | 19 | High (95%+) | Post-Hackathon Months 1-3 | Splunk, AD, MFA logs, ServiceNow |
| **Production Tier 2** | 14 | High (90%+) | Post-Hackathon Months 4-6 | Vuln scanners, CMDB, config tools |
| **Production Tier 3** | 9 | Medium (70-80%) | Post-Hackathon Months 7-9 | ServiceNow GRC, incident records |
| **Production Docs** | 6 | High (85-90%) | Post-Hackathon Months 4-6 | OSCAL SSPs, policies, architecture docs |
| **PRODUCTION TOTAL** | **48** | **88% avg** | **9 months post-hackathon** | Enterprise MCP + OSCAL integrations |

**Hackathon Strategy (~30 Days Remaining):** Demonstrate core capability with 10 high-impact controls using accessible data sources. Production roadmap (9 months post-hackathon) shows scalability to 48+ controls with enterprise integrations.

**BOBBIE's Assessment Model:**
- ✅ **Validates:** Completeness, accuracy, consistency of documentation and technical implementations
- ✅ **Recommends:** Specific remediation actions with step-by-step guidance
- ❌ **Does NOT:** Generate documents, select architectures, approve risks, make authorization decisions

---

## Document Analysis Controls (Automatable via OSCAL/NLP)

### Planning (PL) — Structural Validation ✅ NEWLY AUTOMATABLE
- **PL-2:** System Security Plan (SSP) — Validate OSCAL completeness, control coverage, metadata
- **PL-4:** Rules of Behavior — Check for required sections, parse acknowledgment records
- **PL-8:** Security Architecture — Analyze architecture diagrams for required components, validate against patterns

### Program Management (PM) — Document Completeness ✅ NEWLY AUTOMATABLE  
- **PM-1:** Information Security Program Plan — Validate required sections exist, check approval dates
- **PM-9:** Risk Management Strategy — Parse risk register, verify all systems have risk assessments
- **PM-10:** Authorization Process — Track ATO workflow status, validate approval signatures exist

### Risk Assessment (RA) — Already in Tier 2
- **RA-3:** Risk Assessment — Validate assessment exists, is current (<365d), has AO approval ✅

---

## Non-Automatable Controls (True Out of Scope)

### Physical & Environmental Protection (PE)
- **PE-2:** Physical Access Authorizations — Requires on-site badge system inspection
- **PE-3:** Physical Access Control — Requires physical inspection of mantraps, locks, guards
- **PE-6:** Monitoring Physical Access — CCTV footage review for anomalies (requires human interpretation)
- **PE-13:** Fire Protection — Fire suppression system testing requires physical presence
- **PE-14:** Temperature/Humidity — Data center environmental monitoring requires on-site validation

### Personnel Security (PS)
- **PS-2:** Position Risk Designation — Requires understanding of mission-critical roles (organizational context)
- **PS-3:** Personnel Screening — Background investigation adjudication requires human judgment
- **PS-7:** Third-Party Personnel Security — Vetting contractor trustworthiness involves subjective assessment

### Final Authorization & Approval Decisions (Non-Automatable)
- **Risk Acceptance:** AO deciding "this risk is acceptable for our mission" (BOBBIE calculates score & recommends mitigation, human accepts/rejects)
- **Control Tailoring:** Choosing which controls to implement/compensate based on organizational constraints (BOBBIE assesses baseline compliance, human tailors)
- **Policy Approval:** Approving final policy content for organizational culture fit (BOBBIE validates structure/completeness, human approves content)
- **Architecture Selection:** Choosing final design based on mission priorities (BOBBIE validates architecture completeness/security, human selects)
- **ATO Decisions:** Final authorization to operate based on residual risk assessment (BOBBIE provides risk assessment, AO authorizes)

---

## OSCAL-Powered Document Analysis (High Value Addition)

### What BOBBIE Assesses with OSCAL SSPs
**Assessment Focus:** Validate compliance, identify gaps, recommend fixes — NO document generation

#### PL-2: System Security Plan Validation
**BOBBIE Assessment Checks:**
- ✅ All required sections present (System Characteristics, Control Implementation, etc.)
- ✅ Control implementation statements exist for all applicable controls
- ✅ Control statements reference actual system components in inventory
- ✅ Metadata completeness (system owner, AO, dates, classification)
- ✅ Cross-reference validity (components mentioned in controls exist in inventory)
- ✅ Responsible role assignments for each control
- ✅ Approval signatures exist and are current (<365 days)
- ✅ No orphaned controls (controls with no implementation statement)
- ✅ Consistency: system boundary described matches CMDB records

**Remediation Recommendations:**
- Missing sections → "Add [Section Name] with required elements: [list]"
- Orphaned controls → "Add implementation statement for [Control-ID] describing [expected implementation]"
- Stale signatures → "Obtain AO review/approval (last review: [date], exceeds 365-day requirement)"

**Example Logic:**
```python
def validate_ssp_oscal(ssp_json):
    findings = []
    
    # Check all baseline controls have implementation
    required_controls = get_baseline_controls(ssp_json['system_characteristics']['security_impact_level'])
    implemented_controls = [c['control_id'] for c in ssp_json['control_implementation']['implemented_requirements']]
    
    missing = set(required_controls) - set(implemented_controls)
    if missing:
        findings.append(f"FAIL: {len(missing)} required controls lack implementation statements: {missing}")
    
    # Validate component references
    components = [c['uuid'] for c in ssp_json['system_implementation']['components']]
    for control in ssp_json['control_implementation']['implemented_requirements']:
        for statement in control.get('by_components', []):
            if statement['component_uuid'] not in components:
                findings.append(f"FAIL: Control {control['control_id']} references non-existent component {statement['component_uuid']}")
    
    # Check signature freshness
    last_review = datetime.fromisoformat(ssp_json['metadata']['last_modified'])
    if (datetime.utcnow() - last_review).days > 365:
        findings.append(f"FAIL: SSP not reviewed in {(datetime.utcnow() - last_review).days} days (>365d)")
    
    return findings
```

#### PL-8: Security Architecture Validation
**BOBBIE Assessment Checks:**
- ✅ Architecture diagram exists (PDF/SVG/OSCAL diagram reference)
- ✅ Required components present (firewall, IDS/IPS, logging, encryption)
- ✅ Data flow shows sensitive data only on approved paths
- ✅ Network segmentation present (DMZ, internal, admin networks separated)
- ✅ Single points of failure identified and documented
- ✅ Architecture matches deployment (compare diagram to Splunk network flows)

**Remediation Recommendations:**
- Missing components → "Deploy [component type] to satisfy [control requirement]"
- Undocumented flows → "Update architecture diagram to include detected flows: [source→dest]"
- Segmentation gaps → "Implement VLAN/firewall rules to separate [network A] from [network B]"

**Example Logic:**
```python
def validate_architecture(oscal_ssp, network_flows_splunk):
    arch = oscal_ssp['system_implementation']['components']
    
    # Check for required security components
    required_types = {'firewall', 'intrusion-detection', 'siem', 'encryption-gateway'}
    present_types = {c['type'] for c in arch}
    
    if not required_types.issubset(present_types):
        missing = required_types - present_types
        return f"FAIL: Architecture missing required components: {missing}"
    
    # Validate data flows match documented architecture
    documented_flows = extract_dataflows_from_diagram(oscal_ssp['diagrams'][0])
    actual_flows = get_unique_network_pairs(network_flows_splunk)
    
    undocumented = actual_flows - documented_flows
    if undocumented:
        return f"FAIL: {len(undocumented)} network flows not documented in architecture"
    
    return "PASS: Architecture complete and matches deployment"
```

#### PL-4: Rules of Behavior Validation
**BOBBIE Assessment Checks:**
- ✅ Document exists and is current (<365 days)
- ✅ Required topics covered (acceptable use, prohibited activities, incident reporting, sanctions)
- ✅ User acknowledgment records exist in ServiceNow (cross-check AD users)
- ✅ New users sign within 30 days of account creation
- ✅ Annual re-acknowledgment completed

**Remediation Recommendations:**
- Unsigned users → "Require RoB acknowledgment for [N] users: [user list]"
- Missing sections → "Update RoB to include [section]: [required content per NIST 800-53]"
- Stale acknowledgments → "Initiate annual re-acknowledgment campaign for [N] users"

**Example Logic:**
```python
def validate_rob(rob_document, servicenow_records, ad_users):
    # Parse RoB document for required sections (NLP or structured format)
    required_sections = ['acceptable_use', 'prohibited_activities', 'incident_reporting', 'sanctions']
    present_sections = extract_sections(rob_document)
    
    if not all(s in present_sections for s in required_sections):
        return "FAIL: RoB missing required sections"
    
    # Check all users have signed
    signed_users = {r['user'] for r in servicenow_records if r['document_type'] == 'RoB'}
    active_users = {u['sAMAccountName'] for u in ad_users if u['enabled']}
    
    unsigned = active_users - signed_users
    if unsigned:
        return f"FAIL: {len(unsigned)} active users have not signed RoB"
    
    # Check signature freshness
    stale_sigs = [r for r in servicenow_records if (datetime.utcnow() - r['signed_date']).days > 365]
    if stale_sigs:
        return f"FAIL: {len(stale_sigs)} users have stale RoB signatures (>365d)"
    
    return "PASS: All users current on RoB acknowledgment"
```

### Policy Analysis (NLP + Rule-Based)

#### What BOBBIE Validates
- ✅ Policy document exists and is current
- ✅ Required sections present (Purpose, Scope, Roles, Procedures, Enforcement)
- ✅ Policy references correct regulatory authorities (FISMA, NIST, etc.)
- ✅ Approval signatures exist (AO, CISO, Legal)
- ✅ Policy version control maintained
- ✅ Consistency: policy statements don't contradict each other
- ✅ Completeness: policy covers all applicable controls
- ✅ Readability metrics (Flesch-Kincaid grade level for accessibility)

#### Remediation Recommendations Provided
- Missing sections → Specific section templates with required content
- Missing citations → List of required regulatory references to add
- Contradictions → Identification of conflicting statements with resolution guidance
- Stale approvals → Notification to initiate annual review process

**Example: Information Security Policy Validation**
```python
def validate_policy(policy_pdf):
    text = extract_text(policy_pdf)
    metadata = extract_metadata(policy_pdf)
    
    findings = []
    
    # Check required sections
    required_sections = ['Purpose', 'Scope', 'Roles and Responsibilities', 'Policy Statements', 
                         'Procedures', 'Enforcement', 'Review Schedule']
    detected_sections = extract_headings(text)
    
    missing = [s for s in required_sections if s not in detected_sections]
    if missing:
        findings.append(f"FAIL: Policy missing sections: {missing}")
    
    # Check for regulatory references
    required_citations = ['FISMA', 'NIST SP 800-53', 'OMB']
    cited = [c for c in required_citations if c in text]
    
    if len(cited) < len(required_citations):
        findings.append(f"WARN: Policy should reference: {set(required_citations) - set(cited)}")
    
    # Check approval
    if 'Approved by:' not in text or 'Date:' not in metadata:
        findings.append("FAIL: Policy lacks approval signature")
    
    # Check freshness
    if metadata.get('last_modified'):
        age_days = (datetime.utcnow() - metadata['last_modified']).days
        if age_days > 365:
            findings.append(f"FAIL: Policy not reviewed in {age_days} days (>365d)")
    
    # Readability check
    readability = calculate_flesch_kincaid(text)
    if readability > 14:  # College+ reading level
        findings.append(f"WARN: Policy readability grade level {readability} may be too complex")
    
    return findings if findings else ["PASS: Policy meets structural requirements"]
```

### Risk Register Analysis

#### RA-3: Risk Assessment Validation
**Beyond Just "Does it Exist?":**
- ✅ All systems in CMDB have corresponding risk assessment entries
- ✅ Risk assessments completed within required frequency (365 days)
- ✅ Threat modeling methodology documented (STRIDE/PASTA/ATT&CK)
- ✅ Risk scores calculated using approved formula (L × I)
- ✅ All HIGH risks have mitigation plans
- ✅ Mitigation plans have target completion dates
- ✅ Risk acceptance requires AO signature for MODERATE+ risks
- ✅ Residual risk documented after mitigation
- ✅ Cross-reference: mitigations map to POA&M items

**Example Logic:**
```python
def validate_risk_register(risk_register_oscal, cmdb_systems, poam_items):
    findings = []
    
    # Check coverage
    assessed_systems = {r['system_id'] for r in risk_register_oscal['risk_items']}
    cmdb_system_ids = {s['sys_id'] for s in cmdb_systems if s['status'] == 'Production'}
    
    unassessed = cmdb_system_ids - assessed_systems
    if unassessed:
        findings.append(f"FAIL: {len(unassessed)} production systems lack risk assessment")
    
    # Check risk score calculation
    for risk in risk_register_oscal['risk_items']:
        if risk['risk_score'] != (risk['likelihood_score'] * risk['impact_score']):
            findings.append(f"FAIL: Risk {risk['id']} has invalid score calculation")
        
        # Check HIGH risks have mitigations
        if risk['risk_rating'] == 'HIGH' and not risk.get('mitigation_plan'):
            findings.append(f"FAIL: HIGH risk {risk['id']} lacks mitigation plan")
        
        # Check AO approval for MODERATE+ accepted risks
        if risk['risk_rating'] in ['HIGH', 'MODERATE'] and risk['disposition'] == 'ACCEPT':
            if not risk.get('ao_approval_signature'):
                findings.append(f"FAIL: Risk {risk['id']} accepted without AO approval")
    
    # Cross-reference: mitigations should appear in POA&M
    documented_mitigations = {r['mitigation_plan']['poam_id'] for r in risk_register_oscal['risk_items'] if r.get('mitigation_plan')}
    actual_poams = {p['poam_id'] for p in poam_items}
    
    orphaned = documented_mitigations - actual_poams
    if orphaned:
        findings.append(f"FAIL: {len(orphaned)} risk mitigations reference non-existent POA&M items")
    
    return findings if findings else ["PASS: Risk register complete and consistent"]
```

---

## Data Source Requirements

### Hackathon Demo Data Sources (Accessible)
1. **NIST OSCAL Repository** — Sample SSPs, POA&Ms from GitHub (github.com/usnistgov/oscal-content)
2. **AWS CloudWatch Logs** — Security events, application logs (free tier eligible)
3. **AWS Systems Manager** — Inventory, patch compliance, configuration (free for managed instances)
4. **Windows Event Logs** — Local EVTX files (Security.evtx, System.evtx) for offline parsing
5. **NIST NVD API** — CVE data (free, public API: nvd.nist.gov)
6. **CISA KEV Catalog** — Known exploits JSON (free download: cisa.gov/known-exploited-vulnerabilities-catalog)
7. **Mock Data Files** — CSV asset inventory, JSON config baselines, sample vuln scan results

### Production Integrations (Post-Hackathon)
1. **ServiceNow CMDB** — Asset inventory, ownership, classification
2. **Splunk Enterprise** — Security logs, system logs, network traffic
3. **Active Directory** — User accounts, authentication, GPOs
4. **Vulnerability Scanners** — Tenable Nessus or Qualys VMDR (via API)
5. **Enterprise OSCAL** — Production SSPs, POA&Ms, risk registers

---

## Hackathon Demo Environment Setup

### Prerequisites (Free/Low-Cost)
1. **AWS Free Tier Account** — CloudWatch Logs, Systems Manager (12 months free)
2. **Python 3.10+** — For BOBBIE engine and log parsing
3. **AWS Bedrock Access** — Amazon Nova Pro model (pay-per-use, ~$10-20 for full demo)
4. **Sample Data Downloads:**
   - NIST OSCAL samples: `git clone https://github.com/usnistgov/oscal-content`
   - CISA KEV: `curl https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`
   - NVD CVE data: Free API at nvd.nist.gov
5. **Windows Event Logs** — Export Security.evtx from local Windows system (or use provided samples)

### Mock Data Generation Scripts
GitHub repo will include:
- `generate_mock_assets.py` — Creates CSV with 50 sample systems (hostnames, IPs, owners, data classifications)
- `generate_mock_tickets.py` — Creates JSON approval tickets for AC-2 validation
- `generate_mock_vulns.py` — Creates vulnerability scan results with CVSS scores
- `sample_password_policy.json` — AD-style password policy for IA-5 validation

### Cost Estimate
- **AWS Services:** ~$5-10 (CloudWatch Logs API calls, Systems Manager)
- **AWS Bedrock Nova Pro:** ~$10-20 (estimated for demo usage with 128K context)
- **Total:** $15-30 for entire hackathon demo

### Alternative to AWS (Zero Cost Option)
If AWS costs are prohibitive:
- Use **only OSCAL analysis + local log files**
- Parse Windows EVTX files with `python-evtx` library
- Mock all external API calls with cached JSON responses
- Demo 5 controls: PL-2 (SSP), AC-2 (accounts), AC-7 (failed logons), IA-5 (password policy), RA-5 (vuln data)

---

## Risk & Mitigation Strategy

### Risk: Data Quality Issues
- **Mitigation:** Implement data validation layer with confidence scoring
- **Example:** Flag assessments where CMDB data >90 days stale

### Risk: False Positives
- **Mitigation:** Analyst feedback loop to tune logic; suppression rules with ISSO approval

### Risk: Integration Complexity
- **Mitigation:** Modular MCP adapter architecture allows tool substitution

### Risk: Regulatory Acceptance
- **Mitigation:** Position as "analyst augmentation" not "AI replacement"; require human approval for POA&Ms

---

## Success Metrics

### Hackathon Judging Criteria Alignment

#### Technical ImpPro Integration:** Production-grade reasoning with 128K context for 10 demo controls + 48-control production roadmap
- ✅ **LangChain Orchestration:** Multi-agent system with parallel control assessment execution
- ✅ **Accessible Architecture:** AWS CloudWatch, Systems Manager, local EVTX parsing, OSCAL analysis (no enterprise licensing required)
- ✅ **System Quality:** Deterministic logic with 100% reproducibility, comprehensive error handling
- ✅ **OSCAL Document Analysis:** Novel application of Nova Pro for complete SSP validation (5000+ line documents)
- ✅ **Remediation Engine:** Context-aware fix recommendations with implementation steps and priority ranking
- ✅ **Demo Realism:** Uses accessible tools ($15-30 budget), deployable by any developer, shows production capability
- ✅ **Demo Realism:** Uses free/low-cost tools (<$15 budget), deployable by any developer

#### Enterprise or Community Impact (20% weight)
- ✅ **Federal Agency Value:** $200M+ annual market for security assessments (FISMA, FedRAMP, DoD)
- ✅ **Cost Reduction:** 70-85% reduction in assessment labor (2-4 weeks → 4-8 hours)
- ✅ **Continuous Authorization:** Enable real-time compliance monitoring vs. annual audits
- ✅ **Risk Reduction:** Catch 95%+ of control deficiencies missed in manual reviews
- ✅ **Accessibility:** Democratize federal compliance for small agencies lacking ISSO staff

#### Creativity and Innovation (20% weight)
- ✅ **Novel Application:** First agenPro's 128K context for complete SSP validation in single inference
- ✅ **Multi-Agent System:** LangChain orchestration of 10 specialized control agents with parallel execution
- ✅ **Deterministic AI:** Hybrid approach—Nova Pro reasoning for complexity, deterministic logic for auditability
- ✅ **Cross-Domain Synthesis:** Correlating logs, configs, documents, vulnerability data across 7+ sources simultaneously
- ✅ **Production-Ready Demo:** Nova Pro demonstrates scale capability (10 controls → 48 controls path)
- ✅ **Cross-Domain Synthesis:** Correlating logs, configs, documents, vulnerability data across 15+ sources

---

### Technical Metrics

**Hackathon Demo (10 controls):**15-30 minutes with parallel processing)
- **Consistency:** 100% reproducible results (deterministic logic + Nova Pro reasoning)
- **Coverage:** 10 high-impact controls demonstrated (2% of 800-53 Rev 5, proof of concept)
- **OSCAL Analysis:** Complete SSP validation (5000+ lines): 2-3 min vs. 2-4 hours manual review
- **Nova Pro Performance:** <2 seconds per control assessment, parallel execution of all 10 controls
- **Context Window:** 128K tokens handles entire assessment in single invocation
- **Cost:** $15-30Performance:** <3 seconds per control assessment, <1 minute for SSP validation
- **Cost:** <$15 for entire demo (AWS + Bedrock API calls)

**Production Vision (48 controls):**
- **Assessment Speed:** Manual (2-4 weeks) → Automated (4-8 hours)
- **Coverage:** 48 controls (24% of 800-53 Rev 5 control set)
- **Enterprise Integration:** Splunk, ServiceNow, Tenable, Active Directory

### Business Metrics
- **Cost Reduction:** 70-85% reduction in assessment labor costs
- **Risk Visibility:** Real-time control status vs. annual snapshots
- **Compliance:** Enable continuous authorization (CA) for federal systems
- **Documentation Quality:** Catch 95%+ of SSP structural deficiencies before AO review
- **Federal Market Size:** 430+ federal agencies, 12,000+ FISMA-reportable systems

### Adoption Metrics (Target: End of Year 1)
- 5 pilot systems assessed with full automation
- 80% accuracy vs. manual assessments (validation study)
- 3 federal agencies in pilot program
- POA&M generation time: <2 hours per system
- OSCAL SSP validation: < 15 minutes per system

---

---

## Amazon Nova Hackathon Submission Details

**Category:** Agentic AI  
**Submitter Type:** Organization (euCann LLC)  
**Code Repository:** [GitHub - BOBBIE Assessment Engine](https://github.com/eucann/bobbie-assessment-engine) *(to be published)*  
**Demo Video:** 3-minute walkthrough showing BOBBIE assessing AC-2, RA-5, PL-2 controls *(to be recorded)*  
**Blog Post (Bonus):** "How BOBBIE Transforms Federal Compliance" on builder.aws.com *(to be written)*  
**Hashtag:** #AmazonNova #BOBBIE #FederalCompliance #AgenticAI

**Contact:**  
- Email: [info@eucann.life](mailto:info@eucann.life)  
- Project Lead: euCann LLC AI Security Architecture Division

---

**Document Classification:** CUI // SP-CTI  
**Last Updated:** February 14, 2026  
**Hackathon Timeline:** ~30 days remaining (deadline: Mar 16, 2026)  
**Hackathon Version:** 1.0-NOVA  
**Owner:** euCann LLC — AI Security Architecture Division
