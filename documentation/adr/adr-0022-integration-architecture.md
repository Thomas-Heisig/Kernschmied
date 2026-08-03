# ADR-0022: Integration Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as an open platform that must integrate with a wide variety of external systems throughout its lifetime.

The platform itself should remain independent of any individual vendor or protocol while allowing new integrations to be added without modifying the application core.

Examples include:

- Microsoft Outlook
- Microsoft Exchange
- Gmail
- Google Calendar
- Microsoft Teams
- Slack
- Nextcloud
- SharePoint
- JTL-Wawi
- ERP systems
- CRM systems
- SIP providers
- Telephony systems
- REST services
- GraphQL services
- Databases
- MQTT
- OPC-UA
- Webhooks
- AI APIs
- Future enterprise systems

The integration architecture must therefore provide a consistent, secure and extensible framework for communication with external systems.

---

# Problem

External systems differ significantly in:

- protocols
- authentication methods
- data formats
- availability
- latency
- error handling
- rate limits
- security models
- versioning

Directly embedding vendor-specific logic throughout the application creates several problems.

Typical examples include:

- duplicated integration logic
- tight coupling
- vendor lock-in
- inconsistent authentication
- difficult testing
- poor maintainability
- complex upgrades

The platform therefore requires a common integration architecture.

---

# Decision

Kernschmied adopts a **Provider-Based Integration Architecture**.

Every external system is represented by an integration provider.

Business services never communicate directly with external systems.

Instead they communicate exclusively with the Integration Service.

The Integration Service delegates communication to registered providers.

---

# Architectural Principle

> **Business services request capabilities.**
>
> **Integration providers implement external communication.**
>
> **External systems never become part of the application core.**

---

# High-Level Architecture

```text
Application

        │

        ▼

Integration Service

        │

        ▼

Integration Registry

        │

 ┌──────┼──────────────┬──────────────┐
 │      │              │              │
 ▼      ▼              ▼              ▼

Email  Calendar      ERP         Custom
Provider Provider   Provider    Provider
```

---

# Integration Service

The Integration Service is the single entry point for all external communication.

Responsibilities include:

- provider selection
- request validation
- authorization
- retry handling
- timeout handling
- error normalization
- auditing
- event generation

Business services never communicate directly with providers.

---

# Integration Providers

Every external system is implemented as an integration provider.

Examples include:

- Outlook Provider
- Gmail Provider
- Google Calendar Provider
- Exchange Provider
- JTL Provider
- REST Provider
- GraphQL Provider
- SIP Provider
- Webhook Provider
- File System Provider

Providers remain isolated from each other.

---

# Integration Registry

The Integration Registry manages available providers.

Responsibilities include:

- registration
- discovery
- validation
- lifecycle management
- capability metadata

Only registered providers become available.

---

# Capability-Based Design

Business services never depend on vendor names.

Instead they request capabilities.

Examples include:

- send email
- read mailbox
- create calendar event
- upload document
- search contacts
- initiate phone call
- execute ERP operation

The provider determines how the capability is implemented.

---

# Runtime Configuration

Runtime configuration defines:

- enabled providers
- credentials
- endpoints
- default providers
- retry policies
- timeout policies
- synchronization intervals
- mapping rules

Configuration is stored in the database.

Sensitive credentials are stored using the platform's secret management system.

Secrets are never stored in plain runtime configuration.

---

# Authentication

The architecture supports multiple authentication methods.

Examples include:

- OAuth 2.0
- OpenID Connect
- API Keys
- Basic Authentication
- Bearer Tokens
- Client Certificates
- Service Accounts
- Username/Password
- Anonymous Access (where appropriate)

Authentication details remain provider-specific.

---

# Communication Patterns

The architecture supports different communication models.

Examples include:

## Request / Response

Typical REST or GraphQL APIs.

---

## Streaming

Long-running streams such as:

- Server-Sent Events
- WebSockets
- AI streaming responses

---

## Event-Based

Examples include:

- webhooks
- message queues
- publish / subscribe

---

## Scheduled Synchronization

Background synchronization tasks.

Examples:

- mailbox synchronization
- calendar synchronization
- ERP synchronization

---

# Data Mapping

External data formats are mapped into platform contracts.

Examples include:

- email
- calendar event
- contact
- document
- task
- customer
- invoice

Business services operate exclusively on platform contracts.

---

# Error Handling

Providers translate external errors into standardized platform errors.

Business services never receive vendor-specific exceptions.

Typical normalized categories include:

- authentication failed
- authorization denied
- connection unavailable
- timeout
- validation failed
- rate limited
- unsupported operation
- temporary failure

---

# Retry Policy

Retry behavior is configurable.

Possible strategies include:

- no retry
- immediate retry
- exponential backoff
- scheduled retry
- manual retry

The Integration Service coordinates retries.

---

# Rate Limiting

Providers may define:

- request limits
- concurrency limits
- burst limits
- cooldown periods

The platform respects external service limitations.

---

# Event Integration

Integration providers publish platform events.

Examples include:

- email.received
- calendar.updated
- contact.changed
- webhook.received
- synchronization.completed

Other platform components subscribe to these events.

---

# Workflow Integration

Workflow activities may invoke integration capabilities.

Examples include:

- send notification
- create calendar appointment
- upload document
- create ERP order

Workflows remain independent of provider implementations.

---

# Audit Integration

Every externally visible operation generates audit information.

Audit records include:

- provider
- operation
- user
- tenant
- request identifier
- result

Sensitive payloads are excluded.

---

# Security

Integration providers execute under the platform security model.

They must never:

- bypass authorization
- expose secrets
- access unrelated tenant data
- execute arbitrary code
- disable auditing

Every operation is authorized before execution.

---

# Tenant Isolation

Integrations are tenant-aware.

Each tenant may configure:

- different providers
- different credentials
- different endpoints
- different synchronization settings

Tenant configuration never leaks into another tenant.

---

# Plugin Integration

New providers are delivered through packages.

Examples include:

- SAP
- Salesforce
- HubSpot
- Microsoft Dynamics
- Discord
- WhatsApp
- Signal
- Telegram

The application core remains unchanged.

---

# Monitoring

The platform records provider metrics.

Examples include:

- response time
- request count
- error rate
- retry count
- synchronization duration

Metrics support diagnostics and capacity planning.

---

# Performance

Providers may implement:

- batching
- caching
- incremental synchronization
- background processing
- connection pooling

Performance optimizations remain internal to providers.

---

# Consequences

## Positive

### Loose Coupling

Business services remain independent of external systems.

---

### Replaceable Providers

Different vendors may provide the same capability.

---

### Centralized Security

Authorization and auditing remain consistent.

---

### Easier Testing

Providers can be tested independently.

---

### Runtime Flexibility

Providers may be enabled or disabled without changing application code.

---

### Marketplace Ready

Future integration packages follow the same architecture.

---

## Negative

### Additional Abstraction

Provider architecture increases implementation complexity.

---

### Mapping Effort

External data requires normalization.

---

### Lifecycle Management

Providers require validation, registration and configuration.

---

### Configuration Complexity

Large installations may manage many providers.

---

# Alternatives Considered

## Direct API Calls

Advantages

- Simple implementation

Disadvantages

- Tight coupling
- Duplicate logic
- Vendor lock-in

Rejected.

---

## Vendor SDK Everywhere

Advantages

- Fast development

Disadvantages

- SDK dependency throughout the codebase
- Difficult upgrades
- Inconsistent architecture

Rejected.

---

## One Integration per Module

Advantages

- Local implementation

Disadvantages

- No reuse
- Duplicate authentication
- Duplicate error handling

Rejected.

---

## External Integration Platform Only

Advantages

- Rich ecosystem

Disadvantages

- Additional infrastructure
- Vendor dependency
- Reduced platform control

Rejected.

---

# Related ADRs

- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0006 — API Contracts and Versioning
- ADR-0009 — Runtime Registry Architecture
- ADR-0012 — Action Architecture
- ADR-0013 — Event Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0018 — Plugin and Package Architecture
- ADR-0019 — Audit and Revision Architecture
- ADR-0020 — Multi-Tenant Architecture
- ADR-0021 — Search Architecture
- ADR-0024 — Identity and Authorization
- ADR-0026 — Workflow Engine
- ADR-0029 — Tool Execution Architecture
- ADR-0030 — Monitoring and Observability

---

# Implementation Notes

The MVP intentionally focuses on a small number of local and cloud integrations.

Future providers—including ERP systems, telephony, messaging platforms, industrial protocols and enterprise services—must integrate through the Integration Service and Integration Registry without modifying the application core or public contracts.