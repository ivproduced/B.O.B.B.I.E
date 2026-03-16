# We Built an AI Agent That Does Federal Security Audits in 30 Minutes Instead of 4 Weeks

*A build log for B.O.B.B.I.E. — our Amazon Nova Hackathon submission*

---

Here's a number that stops most people cold: a single FedRAMP authorization assessment can cost a vendor **$250,000–$500,000** in third-party assessor fees alone — before a single hour of internal ISSO labor is counted. Multiply that across the federal government's tens of thousands of information systems requiring annual assessment, and the compliance burden is staggering.

That burden is the manual security control assessment — the soul-crushing, multi-week process of proving to an authorizing official that yes, your system does in fact meet the 300+ requirements in NIST SP 800-53.

A typical assessment takes **2–4 weeks**. It involves a small team of ISSOs, auditors, and technical reviewers manually combing through system documentation, pulling AWS console screenshots, querying logs, and cross-referencing CVE databases. The output is a report and a POA&M (Plan of Action & Milestones) that everyone immediately starts dreading having to update in 12 months.

It felt like a problem begging for AI.

So we built **B.O.B.B.I.E.** — *Bot Oversight & Boundary Benchmarking Inference Engine*.

---

## The Core Idea

The insight was simple: NIST 800-53 is already a structured document. Every control has a family, an ID, and a set of assessment objectives. That structure maps cleanly onto a multi-agent architecture — one orchestrator, one specialized AI agent per control family, each agent knowing exactly what evidence to gather and how to score it.

Instead of a human spending a week pulling audit logs to check whether failed login attempts are triggering lockouts (AC-7), you let an agent read the log evidence and produce a PASS or FAIL verdict with traceable reasoning in seconds.

**The hypothesis: what if a full NIST 800-53 assessment could run in under 30 minutes, against a real AWS environment, with output good enough to anchor a real POA&M?**

---

## The Build

We're running this as an Amazon Nova Hackathon submission, which shaped some of our choices. The AI backbone is **Amazon Nova Pro** via AWS Bedrock — 128K context window, which matters when you're feeding in full OSCAL System Security Plans that can run 5,000+ lines.

The architecture ended up as a hierarchy:

- **A master orchestrator** that spins up family agents in parallel, aggregates their results, and generates the final compliance report and POA&M
- **8 family agents** active in the hackathon build (AC, AU, CM, IA, PL, PM, RA, SI), covering 10 controls, with the architecture designed to scale to all 20 NIST families
- **Dedicated tools** per agent: AWS API callers for live infrastructure, OSCAL loaders for SSP validation, EVTX parsers for Windows event logs, and CVE/KEV enrichment for vulnerability checks

The agents aren't just prompt wrappers. Each one implements deterministic pre-checks — password policy thresholds, audit log field completeness rates, vulnerability SLA calculations — before passing context to Nova Pro for reasoning. The hybrid approach keeps results consistent and auditable.

For infrastructure sources, we built collectors for four modes: **live AWS API calls**, **Terraform state files**, **AWS Config snapshots**, and **CloudFormation**. The same assessment engine runs against all of them.

The web interface is built on **React + USWDS** (the U.S. Web Design System, standard for federal government interfaces), backed by an Express.js API layer that streams assessment logs in real time so you can watch each family agent work through its controls.

---

## The Moment It Clicked

The test that made it feel real was running the full stack against a mock Terraform state file paired with a fabricated `context_evidence.json` — a JSON document encoding 10 controls' worth of deliberate pass/fail scenarios we'd designed by hand.

The evidence file intentionally told the truth: AU-3 audit records had 100% field completeness. The IA-5 password policy met every NIST 800-63B threshold. PL-2 had all required SSP sections. Those should PASS.

But AC-2 had an account created without an ISSO-approved ticket. AC-7 had a user with 7 consecutive failed logons and no lockout. RA-5 had a critical CVE sitting unpatched for 22 days, breaching the 15-day SLA, alongside a CISA KEV entry. Those should all FAIL.

The results came back:

> **AC** — 0 Pass · 2 Fail  
> **AU** — 1 Pass · 0 Fail  
> **CM** — 0 Pass · 1 Fail  
> **IA** — 1 Pass · 0 Fail  
> **PL** — 1 Pass · 0 Fail  
> **PM** — 0 Pass · 1 Fail  
> **RA** — 0 Pass · 1 Fail  
> **SI** — 0 Pass · 2 Fail

Every single one matched exactly. 3 Pass. 7 Fail. Correct finding, correct family agent, correct reasoning in the POA&M entry.

For a system built in a few weeks, that was the moment.

---

## What It Can't Do (Yet)

To be honest about where this is: the hackathon build is a demonstrator, not a production ATO tool. Some controls require human judgment that no agent should replace — especially around policy intent and risk acceptance. The live AWS collection path doesn't cover every service a real FedRAMP system would touch. And the Nova Pro calls add up — a full demo run costs roughly $10–20 in API calls.

But none of that makes the core result less interesting. The architecture works. The evidence pipeline works. The scoring is correct and traceable.

---

## Why This Matters Beyond the Hackathon

FedRAMP alone has ~350 authorized cloud systems, each requiring annual assessments. FISMA covers tens of thousands of federal information systems. The backlog of delayed ATOs has real consequences — good security tools sitting unapproved, contracts stuck, programs blocked.

If autonomous assessment agents can get even a fraction of that assessment burden off human reviewers — handling the mechanical evidence gathering, log analysis, and CVE triage while humans focus on judgment calls — that's a meaningful shift.

We're building toward that. BOBBIE is the first concrete step.

---

*B.O.B.B.I.E. is our submission to the Amazon Nova AI Hackathon 2026. Stack: Amazon Nova Pro · AWS Bedrock · LangChain · Python · React · USWDS · NIST OSCAL. Built by the euCann Software Development team.*

*Deadline: March 16, 2026.*
