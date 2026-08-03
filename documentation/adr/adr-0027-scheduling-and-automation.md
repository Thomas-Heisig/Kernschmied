# ADR-0027: Scheduling and Automation Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as an event-driven and highly configurable platform.

Many platform functions must execute automatically without direct user interaction.

Typical examples include:

- scheduled workflows
- recurring maintenance
- background synchronization
- reminder notifications
- periodic imports
- periodic exports
- report generation
- cache cleanup
- backup execution
- AI model maintenance
- registry synchronization
- event-triggered automations

The platform therefore requires a generic scheduling and automation subsystem.

---

# Problem

Without a dedicated scheduling architecture, automated execution becomes scattered throughout the application.

Typical problems include:

- duplicated timer logic
- operating system dependencies
- inconsistent retries
- missing execution history
- poor observability
- unreliable execution after restarts
- difficult testing
- inconsistent authorization

As the platform grows, background processing becomes increasingly difficult to maintain.

---

# Decision

Kernschmied adopts a **generic Scheduling and Automation Architecture**.

Scheduling is responsible only for determining **when** work should start.

Business logic is never implemented inside scheduled jobs.

Scheduled execution always delegates to:

- workflows
- actions
- registered services

The scheduler coordinates execution without containing business logic.

---

# Architectural Principle

> **Schedulers decide when execution begins.**
>
> **Workflows decide what happens.**
>
> **Services perform the actual work.**

---

# High-Level Architecture

```text
Trigger

        │

        ▼

Scheduler

        │

        ▼

Automation Engine

        │

        ▼

Workflow Engine

        │

        ▼

Actions

        │

        ▼

Business Services
```

---

# Scheduling Model

Scheduling supports multiple trigger types.

Examples include:

- one-time execution
- recurring execution
- cron schedules
- interval schedules
- delayed execution
- event-based execution
- manual execution
- startup execution

Every scheduled task is represented as a versioned runtime definition.

---

# Trigger Types

Supported trigger categories include:

- cron
- interval
- once
- delay
- event
- webhook (future)
- external signal (future)

Each trigger is validated before activation.

---

# Automation Definitions

Automation definitions describe:

- trigger
- target
- execution parameters
- execution policy
- retry policy
- timeout policy
- authorization context

Automation definitions never contain executable code.

---

# Job Model

Each execution creates a Job Instance.

Typical information includes:

- identifier
- automation identifier
- workflow identifier
- execution status
- timestamps
- retries
- execution duration
- result
- audit references

Job instances are immutable after completion.

---

# Execution States

Typical job states include:

- scheduled
- queued
- running
- waiting
- completed
- failed
- cancelled
- expired

State transitions are validated.

---

# Event-Based Automation

Automations may subscribe to platform events.

Examples include:

- resource.created
- resource.updated
- workflow.completed
- chat.message.created
- registry.changed
- configuration.changed

Events may trigger workflows automatically.

---

# Workflow Integration

The scheduler never executes business logic directly.

Instead it starts:

- workflows
- actions
- approved background services

Workflow orchestration remains the responsibility of ADR-0026.

---

# Authorization

Automated execution always runs within an Effective Security Context.

Execution identity may be:

- service account
- automation account
- system account

User permissions are never assumed implicitly.

---

# Service Accounts

Every automated execution is associated with an explicit execution identity.

Execution identities are auditable and permission controlled.

---

# Retry Policy

Automation definitions specify retry behavior.

Typical options include:

- no retry
- fixed retry
- exponential backoff
- maximum retry count

Retries are deterministic.

---

# Timeout Policy

Each automation defines execution limits.

Examples include:

- execution timeout
- queue timeout
- expiration time

Expired jobs never continue automatically.

---

# Concurrency

The scheduler supports concurrency policies.

Examples include:

- allow parallel execution
- single instance
- queue duplicates
- discard duplicates

Policies prevent uncontrolled resource usage.

---

# Persistence

All scheduled definitions and job instances are persisted.

Stored information includes:

- schedule
- execution history
- state
- retries
- timestamps
- revisions

The scheduler supports restart recovery.

---

# Runtime Configuration

Scheduling behavior is configurable.

Examples include:

- worker count
- polling interval
- queue size
- retry defaults
- execution limits

Definitions remain versioned.

---

# Registry Integration

Automation definitions are Runtime Registry entries.

Lifecycle:

- draft
- validated
- active
- deprecated
- archived

Activation always requires validation.

---

# Events

The scheduler publishes events.

Examples include:

- automation.started
- automation.completed
- automation.failed
- job.created
- job.expired
- retry.started

Other services may subscribe.

---

# Monitoring

The scheduler exposes operational metrics.

Examples include:

- queued jobs
- running jobs
- failed jobs
- average duration
- retry count
- execution throughput

Monitoring integrates with the observability architecture.

---

# Audit

Every execution generates immutable audit entries.

Typical information includes:

- execution identity
- trigger
- workflow
- duration
- result
- errors

Audit data supports traceability.

---

# Versioning

Automation definitions are versioned independently.

Existing executions continue using the version they started with.

New executions use the active version.

---

# API Contracts

Future APIs may include:

- Create Automation
- Activate Automation
- Pause Automation
- Resume Automation
- Delete Automation
- Trigger Automation
- List Jobs
- Job History

All contracts are versioned.

---

# Consequences

## Positive

### Centralized Scheduling

All automated execution follows one architecture.

---

### Reliable Execution

Jobs survive restarts through persistence.

---

### Runtime Flexibility

Schedules may be changed without redeployment.

---

### Better Observability

Every execution is traceable.

---

### Workflow Integration

Scheduling and workflows remain clearly separated.

---

### Platform Consistency

All automation follows identical lifecycle rules.

---

## Negative

### Additional Runtime Components

Scheduling requires dedicated infrastructure.

---

### Persistent Storage

Job history increases storage requirements.

---

### Operational Monitoring

Background processing requires supervision.

---

### Increased Testing

Scheduling logic requires extensive automated tests.

---

# Alternatives Considered

## Operating System Cron

Advantages

- Simple
- Mature

Disadvantages

- Outside application control
- No audit integration
- Poor portability

Rejected.

---

## Embedded Timers

Advantages

- Easy implementation

Disadvantages

- Lost after restart
- Difficult clustering
- No persistence

Rejected.

---

## External Scheduling Platform

Advantages

- Mature ecosystem

Disadvantages

- Additional infrastructure
- Increased operational complexity

Rejected for the MVP.

---

# Related ADRs

- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0009 — Runtime Registry Architecture
- ADR-0012 — Action Architecture
- ADR-0013 — Event Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0015 — Chat and Conversation Architecture
- ADR-0019 — Audit and Revision Architecture
- ADR-0022 — Integration Architecture
- ADR-0026 — Workflow Engine Architecture
- ADR-0030 — Monitoring and Observability
- ADR-0031 — Performance and Caching

---

# Implementation Notes

The MVP initially supports one-time, interval and cron-based execution with persistent job storage.

Future releases may introduce distributed workers, clustered scheduling, webhook triggers, calendar-based scheduling, dependency graphs and advanced execution policies without changing the scheduling contracts.
