# ADR-0017: Documentation Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is intended to become a long-lived, extensible platform that will evolve over many years.

The project includes:

- Backend
- Frontend
- API contracts
- Runtime configuration
- Registries
- AI models
- Tools
- Workflows
- Resources
- Widgets
- Actions
- Knowledge
- Future plugins
- Future deployment profiles

As the platform grows, documentation becomes a critical architectural component rather than a secondary artifact.

Documentation must evolve together with the system.

It must remain:

- authoritative
- versioned
- searchable
- maintainable
- reviewable
- understandable
- accessible to both humans and AI agents

---

# Problem

Many software projects eventually accumulate documentation that becomes inconsistent with the implementation.

Typical problems include:

- outdated documents
- duplicated information
- contradictory descriptions
- undocumented architecture decisions
- missing contracts
- undocumented APIs
- scattered knowledge

This creates uncertainty for developers and AI assistants alike.

---

## Documentation Becomes Outdated

Implementation evolves faster than documentation.

Developers gradually stop trusting the documentation.

---

## Duplicate Information

The same concept is described in multiple places.

Eventually these descriptions diverge.

---

## Missing Architecture Decisions

Important architectural decisions remain undocumented.

Future contributors cannot understand why specific solutions were chosen.

---

## Difficult Onboarding

New developers require significant time to understand the project.

Knowledge transfer depends on individuals rather than documentation.

---

## Poor AI Support

AI assistants perform best when documentation is complete, structured and authoritative.

Unstructured documentation leads to inconsistent results.

---

# Decision

Kernschmied adopts a **Documentation Architecture** in which documentation is treated as an architectural artifact.

Documentation evolves together with the implementation and follows the same governance principles as source code.

Documentation is part of the platform architecture.

---

# Architectural Principle

> **Code explains how the system works.**
>
> **Documentation explains why the system exists.**
>
> **Both must evolve together.**

---

# High-Level Architecture

```text
Architecture

        │

        ▼

ADR

        │

        ▼

Contracts

        │

        ▼

Implementation

        │

        ▼

Tests

        │

        ▼

User Documentation
```

---

# Core Concepts

The Documentation Architecture consists of several independent layers.

---

## Architecture Decision Records (ADR)

Architectural decisions are documented as ADRs.

Every significant architectural decision shall have exactly one authoritative ADR.

ADRs explain:

- context
- problem
- decision
- consequences
- alternatives

ADRs are immutable except for editorial improvements.

---

## Architecture Documentation

Architecture documentation explains how the platform is organized.

Examples include:

- system architecture
- runtime architecture
- deployment architecture
- registry architecture
- contract architecture

Architecture documents describe concepts rather than implementation details.

---

## Contract Documentation

Every public contract is documented.

Examples include:

- REST APIs
- Server-Sent Events
- Bootstrap
- UI Schemas
- Registry contracts
- Resource contracts
- Widget contracts
- Action contracts

Contract documentation is the authoritative description of platform interfaces.

---

## Developer Documentation

Developer documentation describes implementation guidance.

Examples include:

- coding standards
- project structure
- testing strategy
- migration guides
- contribution guidelines

Developer documentation complements ADRs but never replaces them.

---

## Operational Documentation

Operational documentation describes deployment and operation.

Examples include:

- installation
- backup
- monitoring
- maintenance
- troubleshooting
- upgrades

---

## User Documentation

User documentation describes platform functionality.

Examples include:

- administration
- configuration
- workflows
- tutorials
- reference guides

User documentation is independent from implementation details.

---

# Documentation Hierarchy

Documentation follows a clear hierarchy.

```text
Vision

    │

    ▼

ADR

    │

    ▼

Architecture

    │

    ▼

Contracts

    │

    ▼

Implementation

    │

    ▼

Tests

    │

    ▼

Operations / User Guides
```

Higher levels define intent.

Lower levels implement intent.

Lower levels shall never contradict higher levels.

---

# Single Source of Truth

Every concept has exactly one authoritative source.

Examples:

- architecture → ADR
- API → contract documentation
- configuration → runtime configuration documentation
- implementation → source code

Documentation shall reference other documents rather than duplicate their content.

---

# Documentation Structure

Documentation shall be organized into logical domains.

Typical structure:

```text
documentation/

    adr/
    architecture/
    contracts/
    development/
    deployment/
    operations/
    api/
    user-guide/
    reference/
```

Additional domains may be introduced without changing the architecture.

---

# Versioning

Documentation evolves together with the platform.

Architecture documentation follows platform evolution.

Public contracts follow ADR-0005.

Historical documentation remains available when required.

---

# Relationship to Source Code

Documentation and implementation shall remain synchronized.

Changes to architecture require documentation updates.

Changes to public contracts require documentation updates.

Undocumented architectural changes are considered incomplete.

---

# AI Readability

Documentation shall be optimized for both humans and AI systems.

Documents should:

- use consistent terminology
- avoid ambiguity
- define concepts explicitly
- minimize duplication
- use stable headings
- separate concepts clearly

AI-generated documentation shall follow the same standards.

---

# Documentation Review

Documentation changes are reviewed like source code.

Review verifies:

- correctness
- consistency
- completeness
- terminology
- architectural alignment

Documentation reviews are part of the development process.

---

# Traceability

Major implementation areas should be traceable to documentation.

Typical traceability includes:

- ADR → Architecture
- Architecture → Contracts
- Contracts → Implementation
- Implementation → Tests

This enables understanding of design decisions throughout the platform.

---

# Dynamic Extensibility

New architectural concepts may introduce new documentation sections.

The Documentation Architecture itself remains unchanged.

Documentation structure is extensible but governed.

---

# Security

Documentation shall never expose:

- secrets
- credentials
- private keys
- confidential customer information
- internal security mechanisms

Security-sensitive documentation follows access control policies.

---

# Relationship to Other ADRs

This decision complements:

- ADR-0001 — Schema-Driven User Interface
- ADR-0002 — Bootstrap Configuration and Runtime Initialization
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0006 — API Contracts and Versioning
- ADR-0014 — Runtime Configuration Architecture
- ADR-0016 — Knowledge Architecture

The Documentation Architecture provides the governance model for all architectural knowledge within the platform.

---

# Consequences

## Positive

### Better Maintainability

Architecture remains understandable over many years.

---

### Consistent Knowledge

Every concept has one authoritative description.

---

### Improved Onboarding

New developers understand the platform more quickly.

---

### Better AI Support

Structured documentation improves AI-assisted development.

---

### Architectural Traceability

Design decisions remain understandable long after implementation.

---

### Reduced Duplication

Cross-references replace repeated explanations.

---

### Long-Term Stability

Documentation evolves with the platform rather than becoming obsolete.

---

## Negative

### Additional Maintenance

Documentation requires continuous updates.

---

### Review Effort

Documentation becomes part of the review process.

---

### Governance Requirements

Documentation quality requires active governance.

---

### Initial Investment

Creating comprehensive documentation requires additional effort.

---

# Alternatives Considered

## Documentation After Implementation

### Advantages

- Faster initial development

### Disadvantages

- Frequently outdated
- Missing rationale
- Poor consistency

Rejected.

---

## Wiki-Based Documentation Only

### Advantages

- Easy editing
- Familiar workflow

### Disadvantages

- Weak versioning
- Difficult reviews
- Poor traceability

Rejected.

---

## Code Comments Only

### Advantages

- Close to implementation

### Disadvantages

- No architectural overview
- Missing design rationale
- Poor discoverability

Rejected.

---

## AI-Generated Documentation Only

### Advantages

- Fast generation

### Disadvantages

- Potential inconsistencies
- Missing governance
- No authoritative ownership

Rejected.

---

# Compliance

All documentation-related work shall comply with this ADR.

In particular:

- architecture decisions shall be documented as ADRs
- every concept shall have a single authoritative source
- documentation shall evolve together with implementation
- documentation shall avoid unnecessary duplication
- public contracts shall be documented
- documentation shall support both humans and AI assistants
- documentation changes shall be reviewed
- documentation shall never expose sensitive information
- terminology shall remain consistent across all documents
- documentation shall remain versioned and traceable
- documentation shall remain aligned with platform architecture
- implementation shall not intentionally contradict approved documentation