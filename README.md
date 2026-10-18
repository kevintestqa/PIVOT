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

The Risk Engine evaluates both the component being modified and its potential downstream impacts.

#### Overall Risk Formula

PIVOT uses three weighted factors:

| Risk Factor | Default Weight |
|---|---:|
| Component criticality | 40% |
| Downstream impact scope | 30% |
| Business-rule sensitivity | 30% |
| **Total** | **100%** |

The overall formula is:

```text
Risk Score =
    (Component Criticality × 0.40)
  + (Impact Scope × 0.30)
  + (Business-Rule Sensitivity × 0.30)
```

All factors use a normalized scale of 0–100.

The resulting score is a deterministic risk indicator, not a statistical probability of failure.

#### Component Criticality

Component criticality considers two dimensions:

1. Source component criticality
2. Maximum downstream component criticality

Criticality values are normalized as follows:

| Criticality | Normalized Score |
|---|---:|
| LOW | 0 |
| MEDIUM | 50 |
| HIGH | 100 |

When documented downstream dependencies exist:

```text
Component Criticality =
    Source Criticality
  + (100 - Source Criticality)
    × (Maximum Downstream Criticality / 100)
    × 0.40
```

The source component establishes the baseline.

Downstream criticality can increase this score but cannot reduce it.

PIVOT uses the highest criticality among documented downstream components rather than their average. This prevents newly discovered LOW-criticality dependencies from diluting the impact of a HIGH-criticality dependency.

When no downstream dependencies are documented:

```text
Component Criticality = Source Criticality
```

This prevents the source component's criticality from being artificially reduced.

The downstream contribution is configurable:

```text
Downstream Contribution Weight =
    1 - source_criticality_weight
```

The default downstream contribution weight is 0.40.

Despite the configuration name, this is no longer a traditional 60/40 weighted average.

#### Monotonicity Requirement

PIVOT enforces the following architectural invariant:

**Adding documented downstream exposure must never reduce the calculated risk score when all other inputs remain unchanged.**

This is achieved through two mechanisms:

- Maximum downstream criticality prevents dilution.
- Unique downstream component count measures increasing exposure.

This behavior is covered by regression tests.

#### Downstream Impact Scope

Impact scope measures the number of unique downstream components potentially affected.

```text
Impact Scope =
    min(Unique Downstream Components / Scope Cap, 1) × 100
```

The default scope cap is five components.

For example:

| Downstream Components | Scope Score |
|---|---:|
| 0 | 0 |
| 1 | 20 |
| 2 | 40 |
| 3 | 60 |
| 4 | 80 |
| 5 or more | 100 |

The source component is excluded from the downstream impact count.

#### Business-Rule Sensitivity

Business-rule sensitivity reflects the importance of documented business behavior affected by the proposed change.

| Sensitivity | Score |
|---|---:|
| LOW | 0 |
| MEDIUM | 50 |
| HIGH | 100 |

Sensitivity must be supported by documented business evidence.

AI-generated assumptions cannot independently establish authoritative business-rule sensitivity.

#### Example Risk Calculation

Consider a proposed change affecting:

- One HIGH-criticality source component
- Three LOW-criticality downstream components
- A MEDIUM-sensitivity business rule

**Step 1: Calculate component criticality**

```text
Source Criticality = 100

Maximum Downstream Criticality = 0

Component Criticality =
    100 + (100 - 100) × (0 / 100) × 0.40

Component Criticality = 100
```

**Step 2: Calculate impact scope**

```text
Impact Scope = (3 / 5) × 100

Impact Scope = 60
```

**Step 3: Calculate business-rule sensitivity**

```text
Business-Rule Sensitivity = 50
```

**Step 4: Calculate overall risk**

```text
Risk Score =
    (100 × 0.40)
  + (60 × 0.30)
  + (50 × 0.30)

Risk Score = 40 + 18 + 15

Risk Score = 73
```

**Final Classification: MEDIUM**

#### Risk Assessment Output

The Risk Engine returns a structured, explainable assessment.

Its output distinguishes the calculated risk score from the final
risk classification, which may be affected by deterministic safeguards.

| Output Field | Purpose |
|---|---|
| `change_id` | Unique identifier for the proposed change |
| `source_component_id` | Component being modified |
| `weighted_score` | Calculated numerical risk score (0–100) |
| `weighted_level` | Risk classification before safeguards |
| `risk_level` | Final risk classification after safeguards |
| `factor_scores` | Breakdown of the three scoring factors |
| `source_criticality_score` | Normalized source component criticality |
| `downstream_criticality_score` | Maximum downstream component criticality |
| `impacted_component_count` | Number of unique downstream components |
| `guardrail_applied` | Whether a critical-business-control safeguard raised the classification |
| `source_criticality_weight` | Configuration value controlling the incremental downstream contribution |
| `weights` | Scoring weights used during the assessment |
| `reasons` | Human-readable explanations supporting the assessment |

##### Weighted Risk vs. Final Risk

PIVOT distinguishes between calculated risk and safeguard-adjusted risk.

For example, a proposed change might produce:

```json
{
  "change_id": "CR-001",
  "weighted_score": 65,
  "weighted_level": "MEDIUM",
  "risk_level": "HIGH",
  "guardrail_applied": true
}
```

#### Important Architectural Considerations

- A HIGH-criticality source does not automatically produce a HIGH overall risk classification.
- Missing downstream dependencies do not prove that no dependencies exist.
- Evidence confidence is evaluated separately from business risk.
- A documented critical business control can establish a minimum HIGH risk classification.
- The original weighted score remains visible when a safeguard changes the final classification.
- Risk weights and thresholds are configurable design assumptions, not statistically calibrated probabilities.
- PIVOT provides decision support and does not automatically approve or reject releases.

---

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
|   |-- test_risk_engine.py
|
|-- requirements.txt
|
|-- .gitignore
```

---

## Testing Strategy

PIVOT uses Python's built-in `unittest` framework.

Tests follow behavior-driven development principles through Given/When/Then-style descriptions embedded in Python test-method docstrings.

All three core modules have automated unit-test coverage. The latest confirmed test execution passed 30 tests, including source-criticality and downstream-exposure regression tests.

### Run Tests

From the project root:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

### RiskEngine Test Coverage

RiskEngine tests cover:

- LOW, MEDIUM, and HIGH classifications
- Risk threshold boundaries
- Invalid scoring configurations
- Maximum downstream criticality and source baseline
- Monotonicity when additional dependencies are discovered
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
- [x] Complete RiskEngine unit tests
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