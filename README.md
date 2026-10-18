# PIVOT — Predictive Impact & Validation of Operational Transitions

**Explainable change-impact analysis and business-risk assessment for complex applications.**

> **Project Status:** Early-stage Python prototype. AWS deployment and agentic AI integrations are planned.

---

## Overview

PIVOT is a cloud-focused decision-support platform designed to help Product Managers, engineers, and technical stakeholders understand the potential downstream consequences of proposed application changes.

In complex systems, a seemingly small change can affect multiple services, business processes, and dependencies.

PIVOT helps answer three questions:

1. Which components could be affected by this change?
2. How significant is the potential business risk?
3. What evidence supports the assessment, and what requires further investigation?

PIVOT combines deterministic dependency analysis, configurable risk scoring, and evidence validation.

Future development will introduce AWS-hosted services and bounded AI-assisted investigation.

**PIVOT is not an automated release approval system.** Its purpose is to support informed decisions.

---

## The Problem

Product Managers frequently propose changes without having complete visibility into downstream technical dependencies.

For example:

A Product Manager requests a change to how available buying power is calculated in a trading application.

The request may appear straightforward.

However, the calculation could affect:

- Order management
- Margin calculations
- Account dashboards
- Other downstream services

Without a structured impact assessment, teams risk overlooking dependencies, underestimating complexity, or discovering problems late in development.

PIVOT is designed to identify potential impacts earlier.

---

## Example Business Scenario: Apex Trading

Apex Trading is a fictional financial services organization used to demonstrate PIVOT.

### Proposed Change

**CR-001: Include pending deposits in available buying power**

The Product Manager wants pending deposits included when calculating the funds available for trading.

### Potential Downstream Impacts

Based on documented application dependencies, the proposed change could affect:

| Component | Criticality | Potential Impact |
|---|---|---|
| BalanceCalculationAPI | HIGH | Source component being modified |
| OrderManagementService | HIGH | Order eligibility and buying-power checks |
| MarginService | HIGH | Margin calculations |
| AccountDashboard | MEDIUM | Displayed buying-power information |

These are potential impacts inferred from documented relationships, not confirmed failures.

PIVOT will eventually produce a structured assessment identifying affected components, dependency paths, risk factors, and evidence requiring review.

---

## Architecture

### Current Local Architecture

```text
             PROPOSED CHANGE
                    |
                    v
           ARCHITECTURE DATA
                    |
                    v
             DataValidator
                    |
                    v
           DependencyAnalyzer
                    |
                    v
               RiskEngine
                    |
                    v
          RISK ASSESSMENT
                    |
                    v
             HUMAN REVIEW
```

The three Python modules currently exist independently.

The complete assessment workflow has not yet been integrated.

---

## Core Components

### 1. DataValidator

Validates documented architecture dependencies before they are used in an assessment.

Responsibilities include:

- Detecting references to unknown components
- Identifying duplicate dependency relationships
- Evaluating evidence verification dates
- Identifying stale dependency evidence
- Identifying unverified relationships
- Reporting invalid records

Dependency evidence uses a configurable freshness threshold.

The initial default is 90 days.

Missing or stale evidence does not automatically increase business risk. Instead, it indicates that additional verification may be necessary.

### 2. DependencyAnalyzer

Identifies potential downstream impacts using documented dependency relationships.

Capabilities include:

- Directed dependency traversal
- Direct impact identification
- Indirect impact identification
- Multiple dependency-path identification
- Cycle avoidance
- Deduplication of reported paths

A component can be affected through multiple dependency paths.

However, that component should be counted only once when calculating the overall impact scope.

An absence of documented downstream dependencies does not prove that no dependencies exist.

### 3. RiskEngine

Calculates deterministic business-risk scores using configurable organizational weights.

The initial model evaluates three factors:

| Risk Factor | Default Weight |
|---|---:|
| Aggregate component criticality | 40% |
| Impact scope | 30% |
| Business-rule sensitivity | 30% |
| **Total** | **100%** |

The Risk Engine uses the criticality of all uniquely impacted components rather than relying exclusively on the most critical component.

### Risk Classifications

| Classification | Weighted Score |
|---|---|
| LOW | Below 40 |
| MEDIUM | 40 to below 75 |
| HIGH | 75 or above |

These thresholds and weights are initial design assumptions.

They are not statistically calibrated risk probabilities.

### Critical-Risk Safeguards

Weighted scoring can sometimes obscure important business risks.

PIVOT therefore supports deterministic safeguards.

For example:

If documented evidence establishes that a proposed change affects a critical financial control, the final risk classification cannot be lower than HIGH.

The original weighted score remains visible for transparency.

### Organization-Specific Configuration

Organizations can customize their scoring weights.

A financial institution may place greater emphasis on business-rule sensitivity.

Another organization may prioritize component criticality or the scope of downstream impacts.

All configurations must pass validation before use.

---

## Architectural Principles

PIVOT follows several principles.

### Deterministic Risk Scoring

Risk calculations are performed using explicit rules and documented inputs.

AI-generated reasoning cannot modify the calculated score.

### Evidence-Based Analysis

Dependency relationships must be supported by documented architecture information.

AI cannot independently create authoritative dependencies.

### Explainability

Risk assessments should explain:

- Which components may be affected
- Which dependency paths were identified
- Which risk factors contributed to the score
- Whether deterministic safeguards were applied
- Which evidence requires verification

### Human Oversight

PIVOT supports engineering and product decisions.

It does not automatically approve or reject releases.

### Separation of Concerns

PIVOT distinguishes between:

```text
BUSINESS RISK

EVIDENCE CONFIDENCE

WORKFLOW STATE

PLATFORM OPERATIONAL STATUS
```

These represent different concerns and should not be combined into a single status.

---

## Repository Structure

```text
PIVOT/
|
|-- README.md
|
|-- data/
|   |-- components.json
|   |-- dependencies.json
|   |-- business_rules.json
|
|-- src/
|   |-- analyzer.py
|   |-- data_validator.py
|   |-- risk_engine.py
|
|-- tests/
|   |-- test_analyzer.py
|   |-- test_data_validator.py
|
|-- requirements.txt
|
|-- .gitignore
```

---

## Testing Strategy

PIVOT uses Python's built-in `unittest` framework.

Tests follow behavior-driven development principles through Given/When/Then-style descriptions embedded in Python test-method docstrings.

The existing DependencyAnalyzer and DataValidator suites contain 13 previously passing tests.

RiskEngine tests are the next development milestone.

### Run Tests

From the project root:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

### Planned RiskEngine Test Coverage

RiskEngine tests will cover:

- LOW, MEDIUM, and HIGH classifications
- Risk threshold boundaries
- Invalid scoring configurations
- Aggregate component criticality
- Duplicate impacted components
- Organization-specific scoring weights
- Critical-business-control safeguards
- Invalid component references

---

## Planned AWS Architecture

PIVOT is being developed locally before introducing cloud infrastructure.

The planned architecture includes:

| Technology | Planned Responsibility |
|---|---|
| Amazon S3 | Versioned architecture and dependency evidence |
| AWS Lambda | Assessment processing and read-only tools |
| Amazon API Gateway | Controlled API access |
| Amazon DynamoDB | Assessment records and human-review state |
| Amazon Bedrock | Evidence-grounded AI investigation |
| Amazon Bedrock AgentCore | Agent runtime, tools, and observability |
| CrewAI Flow | Deterministic workflow orchestration |
| Amazon EventBridge | Optional scheduling and escalation workflows |

These integrations are planned and are not currently implemented.

---

## AI Integration Philosophy

AI will assist with interpreting assessment evidence and communicating potential impacts.

However, AI will operate within explicit engineering boundaries.

```text
DOCUMENTED ARCHITECTURE
          |
          v
DETERMINISTIC VALIDATION
          |
          v
DEPENDENCY ANALYSIS
          |
          v
DETERMINISTIC RISK SCORING
          |
          v
AI-ASSISTED EXPLANATION
          |
          v
HUMAN REVIEW
```

AI will not:

- Invent authoritative dependencies
- Override deterministic risk scores
- Approve production releases
- Modify architecture records without authorization

The objective is to combine explainable engineering controls with useful AI assistance.

---

## Development Roadmap

### Phase 1 — Local Analysis Foundation

**Status: In Progress**

- [x] Create synthetic Apex Trading architecture
- [x] Implement dependency analysis
- [x] Implement architecture data validation
- [x] Implement initial configurable risk scoring
- [x] Establish initial unit-testing framework
- [ ] Complete RiskEngine unit tests
- [ ] Integrate validated business-rule evidence
- [ ] Produce an end-to-end assessment for CR-001

### Phase 2 — Assessment Workflow

**Status: Planned**

- [ ] Integrate validation, analysis, and scoring
- [ ] Implement evidence-confidence evaluation
- [ ] Introduce structured assessment records
- [ ] Add human-review workflow states

### Phase 3 — AWS Integration

**Status: Planned**

- [ ] Store versioned architecture data in Amazon S3
- [ ] Persist assessments in DynamoDB
- [ ] Expose assessment functionality through API Gateway and Lambda
- [ ] Implement AWS observability

### Phase 4 — Agentic AI

**Status: Planned**

- [ ] Introduce CrewAI Flow orchestration
- [ ] Integrate Amazon Bedrock
- [ ] Evaluate AgentCore Runtime and Gateway
- [ ] Add evidence-grounded AI explanations
- [ ] Implement agent guardrails and failure handling

---

## Project Limitations

PIVOT is currently a portfolio proof of concept.

The initial architecture data is synthetic.

Risk weights and thresholds are configurable design assumptions and have not been calibrated against historical production incidents.

Dependency analysis is limited to documented relationships.

The platform does not currently provide production-ready change governance, automated release authorization, or a deployed AWS assessment service.

---

## Project Goal

PIVOT demonstrates how software quality engineering principles can be extended into cloud architecture, change-impact analysis, and AI-assisted operational decision support.

The project emphasizes:

**Traceability, deterministic validation, explainable risk, cloud architecture, and human oversight.**

The long-term goal is to help organizations understand the potential consequences of technical changes before those changes reach production.