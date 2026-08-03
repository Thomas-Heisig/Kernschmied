# ADR-0029: Tool Execution Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as an extensible AI platform.

Artificial Intelligence alone cannot perform many real-world tasks.

Instead, AI models must cooperate with backend tools that provide controlled access to external systems and platform functionality.

Typical examples include:

- web search
- document processing
- file management
- database queries
- calendar integration
- email integration
- REST API calls
- workflow execution
- report generation
- data import
- data export
- future integrations

The platform therefore requires a generic tool execution architecture.

---

# Problem

Without a dedicated tool architecture, backend functionality becomes tightly coupled to business services and AI providers.

Typical problems include:

- duplicated integration logic
- inconsistent authorization
- missing validation
- unsafe execution
- poor auditability
- provider-specific implementations
- difficult extensibility
- inconsistent error handling

As the platform evolves, adding new tools becomes increasingly difficult.

---

# Decision

Kernschmied adopts a **generic Tool Execution Architecture**.

Business services and AI models never execute tools directly.

Every tool invocation passes through a centralized Tool Execution Service.

The execution service is responsible for:

- validation
- authorization
- execution
- timeout handling
- audit logging
- result normalization

Only registered tools may be executed.

---

# Architectural Principle

> **AI Models request tool execution.**
>
> **The Tool Service validates the request.**
>
> **Registered Tool Providers perform the execution.**
>
> **Registries define what is available.**

---

# High-Level Architecture

```text
Business Service / AI Model

            │

            ▼

      Tool Service

            │

            ▼

     Tool Registry

            │

            ▼

     Tool Provider

            │

            ▼

     External System
```

---

# Tool Registry

Every tool is represented by a Runtime Registry entry.

Typical metadata includes:

- identifier
- name
- version
- provider
- capabilities
- permissions
- timeout
- enabled state
- revision

Activation always requires validation.

---

# Tool Providers

Every tool belongs to a Tool Provider.

Examples include:

- Local Tools
- REST Providers
- Database Providers
- Calendar Providers
- Email Providers
- File Providers
- AI Providers
- Future Plugin Providers

Providers implement standardized contracts.

---

# Tool Manifests

Every tool is described by a versioned manifest.

Typical information includes:

- identifier
- description
- input schema
- output schema
- permissions
- required capabilities
- supported execution modes
- timeout policy

Manifests never contain executable business logic.

---

# Tool Discovery

Tool discovery is explicit.

Only validated and activated tools become available.

Tool availability depends on:

- deployment profile
- runtime configuration
- permissions
- hierarchy context
- provider status

Discovery never implies execution permission.

---

# Tool Invocation

Every execution follows the same lifecycle.

Typical steps include:

- request validation
- permission evaluation
- input validation
- execution
- output validation
- audit logging
- event publication

Every invocation is deterministic.

---

# Input Validation

Every tool validates its input before execution.

Validation uses versioned schemas.

Invalid requests are rejected before reaching the provider.

---

# Output Validation

Tool results are validated before becoming available to business services or AI models.

Responses are normalized into common platform contracts.

Provider-specific response formats never leave the Tool Service.

---

# Permission Model

Every tool declares required permissions.

Typical permissions include:

- tool.execute
- tool.read
- tool.write
- tool.admin

Permission evaluation follows ADR-0024.

---

# Runtime Configuration

Tool behaviour is configurable.

Examples include:

- enabled state
- timeout
- retry policy
- concurrency limits
- execution quotas
- provider configuration

Configuration follows ADR-0014.

---

# Execution Isolation

Tools execute within controlled runtime boundaries.

Typical isolation includes:

- execution timeout
- memory limits
- process isolation
- network restrictions
- filesystem restrictions

Execution policies depend on deployment profile.

---

# AI Integration

AI models never execute backend functionality directly.

Instead they generate structured tool requests.

The Tool Service validates every request before execution.

Tool results are returned as structured events.

---

# Event Integration

Tool execution publishes standardized platform events.

Typical events include:

- tool.started
- tool.progress
- tool.completed
- tool.failed
- tool.timeout

Other services may subscribe to these events.

---

# Error Handling

Tool-specific errors are translated into generic platform errors.

Typical categories include:

- validation failure
- authorization failure
- timeout
- unavailable provider
- execution failure
- quota exceeded

Business services never receive provider-specific exceptions.

---

# Monitoring

Operational metrics include:

- execution count
- execution duration
- failure rate
- timeout count
- provider availability
- quota usage

Monitoring integrates with ADR-0030.

---

# Audit

Every tool invocation generates immutable audit information.

Typical information includes:

- execution identity
- tool identifier
- provider
- execution time
- request identifier
- hierarchy context
- execution result

Sensitive parameters may be redacted according to policy.

---

# Versioning

Tool definitions evolve independently.

Existing executions continue using the resolved tool version.

New executions use the currently active version.

All contracts follow ADR-0005.

---

# API Contracts

Future APIs may include:

- List Tools
- Get Tool
- Activate Tool
- Deactivate Tool
- Validate Tool
- Test Tool
- Execute Tool
- Tool Capabilities

All contracts are versioned.

---

# Consequences

## Positive

### Safe Execution

All tool execution follows identical security rules.

---

### Provider Independence

Business services remain independent of individual tool implementations.

---

### Runtime Flexibility

Tools may be enabled or disabled without redeployment.

---

### Better Observability

Every execution is measurable and auditable.

---

### Future Readiness

New tools integrate through registries rather than application changes.

---

## Negative

### Additional Runtime Layer

Tool execution requires an additional service layer.

---

### Manifest Maintenance

Every tool requires validated manifests.

---

### Runtime Validation

Input and output validation increases implementation effort.

---

### Operational Monitoring

Tool providers require continuous monitoring.

---

# Alternatives Considered

## Direct Tool Invocation

### Advantages

- Simple implementation
- Fast development

### Disadvantages

- Tight coupling
- Poor security
- Difficult auditing
- Code duplication

Rejected.

---

## Provider-Specific Integrations

### Advantages

- Full provider flexibility

### Disadvantages

- Inconsistent APIs
- Difficult maintenance
- Poor extensibility

Rejected.

---

## AI Direct System Access

### Advantages

- Minimal architecture

### Disadvantages

- Uncontrolled execution
- Security risks
- No audit trail
- No permission enforcement

Rejected.

---

# Related ADRs

- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0009 — Runtime Registry Architecture
- ADR-0012 — Action Architecture
- ADR-0013 — Event Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0019 — Audit and Revision Architecture
- ADR-0022 — Integration Architecture
- ADR-0024 — Identity and Authorization
- ADR-0028 — AI Model Architecture
- ADR-0030 — Monitoring and Observability
- ADR-0031 — Performance and Caching

---

# Implementation Notes

The MVP initially supports locally registered backend tools executed through a centralized Tool Service and Tool Registry. Future releases may introduce distributed tool execution, remote tool providers, containerized isolation, workflow integration, execution queues, sandboxing and advanced quota management without changing the public tool contracts.
