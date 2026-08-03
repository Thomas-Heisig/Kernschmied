# ADR-0012: Generic Action Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a schema-driven platform where user interactions are represented as generic actions rather than business-specific application logic.

The platform must support:

- generic user interactions
- runtime configuration
- configurable permissions
- configurable workflows
- configurable resources
- configurable widgets
- configurable hierarchy nodes
- AI-assisted actions
- future plugins
- long-term maintainability

Every user interaction should be represented as an Action that can be validated, authorized, audited and executed consistently.

The application core therefore requires a generic action architecture.

---

# Problem

Traditional applications typically implement actions directly inside frontend components or backend controllers.

Examples include:

- Save Customer
- Create Project
- Delete User
- Archive Document
- Approve Invoice
- Start Workflow

Each business action usually introduces:

- dedicated frontend handlers
- dedicated backend endpoints
- duplicated validation
- duplicated permission checks
- inconsistent auditing

This approach does not scale for a configurable platform.

---

## Business Logic Leaks into the Frontend

Frontend components frequently contain business-specific behavior.

This duplicates backend logic and increases maintenance costs.

---

## Tight Coupling

Business operations become tightly coupled to:

- pages
- widgets
- resources
- routes
- controllers

Adding new functionality often requires modifications across multiple layers.

---

## Poor Runtime Extensibility

Introducing new actions typically requires:

- backend development
- frontend development
- deployment

instead of configuration.

---

## Inconsistent Authorization

Permission checks become scattered across the application.

Different implementations may apply different authorization rules.

---

## Difficult Auditing

Actions implemented independently often produce inconsistent audit information.

---

# Decision

Kernschmied adopts a **Generic Action Architecture**.

Every user interaction is represented as a generic Action.

Actions are independent of resources, widgets and frontend components.

Widgets invoke Actions.

Resources expose available Actions.

The backend validates, authorizes and executes Actions.

---

# Architectural Principle

> **Widgets trigger actions.
>
> Resources expose actions.
>
> The backend authorizes and executes actions.
>
> The frontend never implements business logic.**

---

# High-Level Architecture

```text
User

        │

        ▼

Widget

        │

        ▼

Action Definition

        │

        ▼

Action Registry

        │

        ▼

Authorization

        │

        ▼

Validation

        │

        ▼

Execution

        │

        ▼

Events
```

---

# Core Concepts

The action architecture consists of several independent concepts.

---

## Action Definition

An Action Definition describes an executable operation.

Typical metadata includes:

- identifier
- display name
- description
- category
- permissions
- capabilities
- confirmation policy
- transaction mode
- risk classification

Definitions are configuration.

---

## Action Invocation

An Action Invocation represents one execution request.

Typical properties include:

- action identifier
- execution context
- parameters
- expected revision
- idempotency key

Invocations are validated before execution.

---

## Action Execution

An Action Execution represents runtime processing.

Typical states include:

- prepared
- waiting_confirmation
- running
- completed
- failed
- cancelled

Executions are auditable.

---

## Action Result

Every Action produces a structured result.

Typical information includes:

- execution identifier
- status
- result payload
- generated events
- warnings
- validation messages
- errors

Results follow versioned contracts.

---

# Action Registry

All Actions are managed through the Action Registry.

The registry is responsible for:

- registration
- discovery
- validation
- lifecycle
- capability metadata
- revision tracking

Only registered Actions may be executed.

---

# Action Categories

Typical categories include:

- create
- update
- delete
- archive
- restore
- export
- import
- AI
- workflow
- navigation
- administration

Additional categories may be introduced through configuration.

---

# Action Capabilities

Every Action declares its capabilities.

Examples include:

- reversible
- idempotent
- asynchronous
- synchronous
- transactional
- auditable
- AI-enabled
- batch-capable

Capabilities are declarative metadata.

---

# Risk Classification

Every Action defines its operational risk.

Typical classes include:

- A — low risk
- B — normal risk
- C — elevated risk
- D — critical risk

Risk classification influences:

- confirmation
- auditing
- permissions
- execution policy

---

# Confirmation Policy

Actions define whether confirmation is required.

Typical policies include:

- never
- contextual
- always

The backend decides whether confirmation is required.

The frontend only presents the confirmation request.

---

# Transaction Modes

Actions declare their execution model.

Examples include:

- local transaction
- remote idempotent
- remote compensatable
- remote non-reversible

Transaction modes determine execution guarantees.

---

# Authorization

Every Action is authorized by the backend.

Authorization may consider:

- authenticated user
- tenant
- hierarchy
- resource
- permissions
- classification
- deployment profile

The frontend never determines authorization.

---

# Validation

Every Action Invocation is validated before execution.

Validation includes:

- schema validation
- parameter validation
- revision validation
- permission validation
- context validation

Validation failures prevent execution.

---

# Optimistic Locking

Actions may reference an expected revision.

If the resource revision has changed, execution is rejected.

This prevents accidental overwriting of concurrent modifications.

---

# Idempotency

Actions may support idempotent execution.

Repeated requests with the same idempotency key must not produce duplicate side effects.

---

# Action Events

Actions generate versioned events.

Typical events include:

- action.started
- action.completed
- action.failed
- action.cancelled
- action.confirmation_required

Events are transported through the generic event contract.

---

# Generic User Interface

Widgets never contain business logic.

Widgets only:

- collect parameters
- invoke Actions
- display results
- react to events

Business behavior always resides in the backend.

---

# Runtime Configuration

Action Definitions are runtime configuration.

Administrators may configure:

- visibility
- permissions
- confirmation policies
- execution parameters
- availability

without modifying application code.

---

# Dynamic Extensibility

New Actions may be introduced through the Registry Architecture.

Adding Actions must not require modifications to:

- widgets
- resources
- REST clients
- existing Actions

Only validated Action Definitions become active.

---

# Security

Actions never bypass security.

The backend validates:

- authentication
- authorization
- permissions
- revisions
- deployment profile
- classification

Every execution is auditable.

---

# Separation of Responsibilities

The backend is responsible for:

- authorization
- validation
- execution
- auditing
- event generation
- transaction management

The frontend is responsible for:

- collecting user input
- displaying confirmations
- presenting execution progress
- presenting results

Business logic remains exclusively in the backend.

---

# Relationship to Other ADRs

This decision complements:

- ADR-0001 — Schema-Driven User Interface
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0006 — API Contracts and Versioning
- ADR-0009 — Dynamic Registry and Runtime Definitions
- ADR-0010 — Generic Resource Architecture
- ADR-0011 — Generic Widget Architecture

The Generic Action Architecture depends on registry-managed actions, generic resources, generic widgets and versioned contracts.

---

# Consequences

## Positive

### Generic Business Operations

The application executes generic Actions rather than business-specific methods.

---

### Runtime Extensibility

New Actions become available through configuration.

---

### Consistent Authorization

Every Action follows the same authorization model.

---

### Consistent Validation

Every Action follows the same validation process.

---

### Centralized Auditing

All executions are audited consistently.

---

### Reduced Frontend Complexity

Widgets remain presentation components.

---

### Better Maintainability

Business behavior evolves through configuration.

---

### AI Readiness

AI systems may invoke Actions through the same contracts as human users.

---

## Negative

### Higher Initial Complexity

Generic execution infrastructure requires careful design.

---

### More Metadata

Actions require lifecycle and capability metadata.

---

### Strong Contract Governance

Action contracts must remain stable over time.

---

### Documentation Requirements

Action definitions and capabilities must be documented consistently.

---

# Alternatives Considered

## Business-Specific Controllers

### Advantages

- Simple implementation
- Familiar architecture

### Disadvantages

- Tight coupling
- Code duplication
- Poor extensibility
- Inconsistent authorization

Rejected.

---

## Frontend Business Logic

### Advantages

- Fast implementation
- Immediate interaction

### Disadvantages

- Security risks
- Duplicated validation
- Difficult maintenance

Rejected.

---

## Runtime Script Execution

Executing dynamically supplied scripts.

### Advantages

- Maximum flexibility

### Disadvantages

- Security risks
- Non-deterministic behavior
- Difficult testing
- Difficult auditing

Rejected.

---

# Compliance

All Action-related implementations shall comply with this ADR.

In particular:

- actions shall be registry-managed
- action definitions shall be configuration
- actions shall be versioned
- action execution shall occur exclusively in the backend
- widgets shall invoke actions rather than implement business logic
- authorization shall always be server-side
- validation shall precede execution
- optimistic locking shall be supported where applicable
- idempotency shall be supported where applicable
- action execution shall generate versioned events
- action execution shall be auditable
- action evolution shall occur through runtime configuration
- public action contracts shall remain backward compatible whenever possible
