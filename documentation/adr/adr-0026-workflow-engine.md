# ADR-0026: Workflow Engine Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a configurable platform capable of orchestrating complex business processes across multiple subsystems.

Many operations cannot be completed through a single API request.

Typical examples include:

- AI-assisted document generation
- Approval processes
- Multi-step configuration
- Import and export operations
- Tool orchestration
- AI model pipelines
- Scheduled automations
- Human approval steps
- Long-running background jobs
- External system synchronization

These processes must remain reliable, resumable, auditable and configurable without requiring changes to the application core.

The platform therefore requires a generic workflow engine.

---

# Problem

Without a dedicated workflow engine, orchestration logic becomes scattered across services.

Typical problems include:

- duplicated business logic
- nested service calls
- difficult error handling
- missing retries
- poor visibility
- no execution history
- impossible resumability
- inconsistent authorization
- difficult testing

As the platform evolves, orchestration complexity increases rapidly.

---

# Decision

Kernschmied adopts a **generic, registry-driven Workflow Engine**.

Workflows are represented as versioned definitions stored in the Runtime Registry.

The workflow engine executes only registered workflow elements and never arbitrary executable code.

Workflow definitions describe:

- execution flow
- conditions
- actions
- participants
- events
- retries
- compensation
- approvals
- variables
- transitions

The workflow engine coordinates execution while individual services remain responsible for business logic.

---

# Architectural Principle

> **Services perform work.**
>
> **Workflows coordinate services.**
>
> **The Workflow Engine orchestrates execution without containing business logic.**

---

# High-Level Architecture

```text
Workflow Definition

        │

        ▼

Workflow Engine

        │

        ▼

Workflow Runtime

        │

        ▼

Registered Actions

        │

        ▼

Business Services
```

---

# Workflow Definition

Every workflow is represented by a versioned definition.

Typical metadata includes:

- identifier
- name
- description
- version
- status
- revision
- schema version

Workflow definitions are immutable after activation.

New behavior requires a new revision.

---

# Workflow Steps

A workflow consists of ordered steps.

Examples include:

- start
- action
- decision
- condition
- parallel execution
- wait
- approval
- notification
- event
- timer
- end

Each step declares its required inputs and outputs.

---

# Execution Model

The engine executes workflows as state machines.

Each workflow instance maintains:

- current state
- execution history
- variables
- timestamps
- retries
- participant assignments

Execution may pause and resume at any time.

---

# State Model

Typical workflow states include:

- draft
- active
- running
- waiting
- suspended
- completed
- cancelled
- failed
- archived

State transitions are validated.

---

# Variables

Workflow variables are stored separately from workflow definitions.

Variables may contain:

- primitive values
- structured objects
- resource references
- workflow context

Variables never contain executable code.

---

# Context Integration

Every workflow executes within an Effective Context.

The engine receives:

- tenant
- hierarchy node
- workspace
- project
- chat
- identity
- permissions
- deployment profile

Workflow execution never bypasses authorization.

---

# Action Integration

Workflow steps invoke registered Actions.

The engine never calls services directly.

Execution always follows:

Workflow Step

↓

Action Registry

↓

Action

↓

Business Service

---

# Event Integration

Workflow execution generates platform events.

Examples include:

- workflow.started
- workflow.waiting
- workflow.resumed
- workflow.completed
- workflow.failed
- workflow.cancelled

Other services may subscribe to these events.

---

# Human Tasks

Some workflow steps require human interaction.

Examples include:

- approval
- rejection
- manual review
- confirmation
- document signing

Human tasks remain pending until completed.

---

# Timers

Workflows may contain timers.

Examples include:

- delay execution
- timeout
- reminder
- scheduled continuation

Timers integrate with the Scheduling Architecture.

---

# Error Handling

Failures are explicit workflow states.

The engine supports:

- retry
- timeout
- compensation
- rollback where applicable
- manual intervention

Failures never terminate the workflow engine.

---

# Compensation

Some workflows require compensating actions.

Examples include:

- delete created resource
- revoke approval
- cancel external request

Compensation is defined explicitly.

---

# Persistence

Workflow instances are persisted.

Stored information includes:

- execution state
- variables
- history
- timestamps
- revisions
- audit references

The engine supports restart recovery.

---

# Registry Integration

Workflow definitions are Runtime Registry entries.

They follow the common lifecycle:

- draft
- validated
- active
- deprecated
- archived

Discovery never implies activation.

---

# Runtime Configuration

Workflow behavior may be configured through runtime configuration.

Examples include:

- concurrency limits
- retry policies
- timeout defaults
- execution quotas

Execution logic itself remains versioned.

---

# Security

Workflow execution always evaluates:

- authentication
- authorization
- deployment profile
- action permissions

Workflow definitions never contain secrets.

---

# Audit

Every execution step generates audit information.

Examples include:

- workflow start
- state transition
- approval
- retry
- cancellation
- completion

Audit data is immutable.

---

# Versioning

Workflow definitions are versioned independently.

Existing workflow instances continue using the version they started with.

New executions use the currently active version.

---

# API Contracts

Future APIs may include:

- Create Workflow
- Activate Workflow
- Start Workflow
- Pause Workflow
- Resume Workflow
- Cancel Workflow
- List Executions
- Workflow History

All contracts are versioned.

---

# Consequences

## Positive

### Centralized Orchestration

Business process coordination exists in a single subsystem.

---

### Runtime Extensibility

New workflows can be introduced without modifying application code.

---

### Better Maintainability

Business logic remains inside services.

---

### Resumable Execution

Long-running processes survive application restarts.

---

### Auditability

Every workflow execution is traceable.

---

### Platform Consistency

All business processes follow the same execution model.

---

## Negative

### Increased Complexity

Workflow orchestration introduces additional runtime components.

---

### More Persistence

Workflow state must be stored reliably.

---

### Operational Monitoring

Workflow execution requires monitoring and diagnostics.

---

### Testing Effort

Workflow definitions require dedicated validation and automated tests.

---

# Alternatives Considered

## Hardcoded Service Orchestration

Advantages

- Simple implementation
- Fast development

Disadvantages

- High coupling
- Difficult maintenance
- Poor extensibility

Rejected.

---

## External Workflow Engine

Advantages

- Mature ecosystem

Disadvantages

- Additional infrastructure
- Integration complexity
- Reduced platform control

Rejected for the MVP.

---

## Script-Based Automation

Advantages

- Flexible

Disadvantages

- Difficult validation
- Security risks
- Poor versioning

Rejected.

---

# Related ADRs

- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0007 — Generic Hierarchy and Context Architecture
- ADR-0009 — Runtime Registry Architecture
- ADR-0012 — Action Architecture
- ADR-0013 — Event Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0019 — Audit and Revision Architecture
- ADR-0022 — Integration Architecture
- ADR-0027 — Scheduling and Automation
- ADR-0029 — Tool Execution Architecture

---

# Implementation Notes

The MVP initially supports sequential workflows with action execution and persistence.

Parallel execution, compensation, graphical workflow editing, BPMN import/export and advanced orchestration are introduced incrementally without changing the workflow contracts.
