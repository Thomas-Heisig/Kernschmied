# Architecture Decision Index

The **Architecture Decision Records (ADRs)** document the most important architectural decisions made during the development of Kernschmied.

Each ADR captures the context, the problem, the chosen solution, the alternatives that were considered, and the long-term consequences of the decision.

The goal of this index is to provide a single entry point into the architectural evolution of the project.

---

## Purpose

The Architecture Decision Index exists to:

- document important architectural decisions
- explain why specific approaches were chosen
- preserve architectural knowledge
- simplify onboarding of new contributors
- provide traceability between implementation and design
- avoid repeatedly discussing previously resolved topics

ADRs are intended to evolve together with the platform.

---

## What is an ADR?

An Architecture Decision Record (ADR) is a lightweight document describing one significant architectural decision.

Each ADR answers five fundamental questions:

1. What problem existed?
2. What decision was made?
3. Why was this decision chosen?
4. Which alternatives were considered?
5. What are the long-term consequences?

Unlike implementation documentation, ADRs explain **why**, not **how**.

---

## ADR Lifecycle

Every ADR follows the same lifecycle.

```text
Proposal

↓

Review

↓

Accepted

↓

Implemented

↓

Superseded (optional)

↓

Archived (optional)

```

Most ADRs remain permanently valid.

Some may later be superseded by newer decisions.

---

## ADR Status

The following status values are used.

| Status      | Meaning                  |
| ----------- | ------------------------ |
| Proposed    | Under discussion         |
| Accepted    | Official architecture    |
| Implemented | Fully implemented        |
| Superseded  | Replaced by another ADR  |
| Deprecated  | No longer recommended    |
| Archived    | Historical documentation |

---

## Relationship to Source Code

Architecture decisions should always be reflected in the implementation.

```text
ADR

↓

Architecture

↓

Implementation

↓

Tests

↓

Documentation

```

When implementation changes require architectural changes, the corresponding ADR should also be updated or superseded.

---

## ADR Organization

The ADRs are organized by architectural topic rather than by implementation layer.

Current areas include:

- UI Architecture
- Bootstrap
- Registries
- Security
- Configuration
- Hierarchy
- Deployment
- Provider Architecture
- Error Handling

Future ADRs should follow the same organizational principles.

---

## ADR Cross References

Architecture Decision Records frequently reference:

- Architecture documentation
- API documentation
- Frontend documentation
- Backend implementation
- Related ADRs

GitHub Wiki links are used throughout the documentation.

Example:

```text
[[ADR-0003-Registries]]

```

---

## Current ADR Collection

## ADR-0001

### Schema-Driven UI

Decision

The frontend is built around a schema-driven architecture rather than hardcoded business components.

Related documentation:

- [[UI-Schema]]
- [[Schema-Renderer]]
- [[Frontend-Overview]]

---

## ADR-0002

### Bootstrap

Defines the bootstrap endpoint as the single application initialization contract.

Related documentation:

- [[Bootstrap]]
- [[Bootstrap-Lifecycle]]

---

## ADR-0003

### Registries

Introduces centralized registries for models and tools.

Related documentation:

- [[Registry-Architecture]]
- [[Models]]
- [[Tools]]

---

## ADR-0004

### Security Profiles

Introduces deployment-independent security profiles and centralized authorization.

Related documentation:

- [[Security-Architecture]]
- [[Deployment-Architecture]]

---

## ADR-0005

### Versioned Contracts

Defines versioned public REST and streaming contracts.

Related documentation:

- [[Contract-Versioning]]
- [[REST-API]]

---

## ADR-0006

### API Contracts and Versioning

Defines independent versioning of public APIs, schemas and streaming contracts.

Related documentation:

- [[Contract-Versioning]]
- [[Bootstrap]]

---

## ADR-0007

### Database and Storage Architecture

Documents storage abstraction, repositories, migrations and persistence strategy.

Related documentation:

- [[Repository-Structure]]
- [[Configuration-Architecture]]

---

## ADR-0008

### Tool Architecture

Introduces provider-independent tool execution using manifests and registries.

Related documentation:

- [[Tools]]
- [[Registry-Architecture]]

---

## ADR-0009

### Authentication and Authorization

Documents centralized authentication and authorization architecture.

Related documentation:

- [[Security-Architecture]]
- [[Deployment-Architecture]]

---

## ADR-0010

### Configuration Management

Defines runtime configuration, scopes, inheritance and revisions.

Related documentation:

- [[Configuration]]
- [[Configuration-Architecture]]

---

## ADR-0011

### Hierarchy and Prompt Inheritance

Defines generic hierarchy nodes and deterministic inheritance.

Related documentation:

- [[Hierarchy]]
- [[Hierarchy-Architecture]]
- [[Prompt-Inheritance]]

---

## ADR-0012

### Frontend Architecture

Documents the schema-driven frontend architecture.

Related documentation:

- [[Frontend-Overview]]
- [[UI-Schema-Pipeline]]

---

## ADR-0013

### Error Handling and Logging

Defines structured platform-wide error handling.

Related documentation:

- [[Errors]]
- [[Security-Architecture]]

---

## ADR-0014

### Deployment Profiles

Defines immutable deployment profiles and operational behavior.

Related documentation:

- [[Deployment-Architecture]]
- [[Security-Architecture]]

---

## ADR-0015

### LLM Provider Architecture

Defines provider abstraction through model registries and manifests.

Related documentation:

- [[Models]]
- [[Registry-Architecture]]
- [[Manifest-System]]

---

## Creating New ADRs

New Architecture Decision Records should be created whenever changes affect:

- public architecture
- platform behavior
- extension mechanisms
- security
- deployment
- contracts
- persistence
- runtime configuration

Minor implementation details generally do not require ADRs.

---

## ADR Naming Convention

ADRs use sequential numbering.

Example:

```text
ADR-0001

ADR-0002

ADR-0003

```

Numbers are never reused.

Titles should be concise and descriptive.

---

## Recommended ADR Structure

Every ADR should include:

```text
Status

Context

Problem

Decision

Architecture

Alternatives

Consequences

Security

Performance

Related Documentation

Summary

```

This ensures consistency across the project.

---

## Relationship to Architecture Documentation

Architecture documentation explains:

> **How the system works.**

ADRs explain:

> **Why the system was designed this way.**

Both document types complement each other.

---

## Relationship to APIs

API documentation specifies:

- endpoints
- request contracts
- response contracts
- versioning

ADRs describe why these APIs exist in their current form.

---

## Maintaining ADRs

When architecture evolves:

- create a new ADR if introducing a significant decision
- supersede older ADRs when necessary
- preserve historical records
- update cross references

Existing ADRs should not be rewritten to erase historical context.

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[System-Context]]
- [[Request-Lifecycle]]
- [[Registry-Architecture]]
- [[Configuration-Architecture]]
- [[Deployment-Architecture]]
- [[Security-Architecture]]

---

## APIs

- [[Bootstrap]]
- [[Chat]]
- [[Configuration]]
- [[Hierarchy]]
- [[Models]]
- [[Tools]]
- [[Errors]]
- [[UI-Schema]]

---

## Frontend

- [[Frontend-Overview]]
- [[Schema-Renderer]]
- [[Component-Registry]]
- [[Action-Registry]]
- [[Generic-Tree]]

---

## Summary

The Architecture Decision Index provides a structured overview of all Architecture Decision Records within the Kernschmied project.

Together, the ADRs document the reasoning behind the platform's most significant architectural choices, creating a permanent architectural knowledge base that supports long-term maintainability, consistent decision-making, and efficient onboarding of future contributors.

---

Back to [[Home]].
