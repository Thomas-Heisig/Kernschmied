# ADR-0018: Plugin and Package Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a modular platform that must evolve over many years without requiring fundamental architectural changes.

The platform shall support new capabilities without modifying the application core.

Examples include:

- AI model providers
- Tool providers
- Resource types
- Widget types
- Action handlers
- Workflow activities
- Import/Export formats
- Search providers
- Authentication providers
- Storage providers
- Integration providers
- Future marketplace packages

Some extensions are delivered together with the application.

Others may be installed later by administrators.

The platform therefore requires a clear distinction between executable software and runtime configuration.

---

# Problem

Many extensible systems eventually blur the distinction between configuration and executable code.

Typical problems include:

- Loading Python modules directly from the database
- Executing uploaded JavaScript
- Dynamically importing arbitrary packages
- Uncontrolled plugin discovery
- Missing version compatibility
- Hidden dependencies
- Inconsistent installation procedures

Such approaches introduce severe security risks and make deployments difficult to reproduce.

---

# Decision

Kernschmied adopts a **Package and Plugin Architecture** based on explicit registration, manifests and controlled installation.

The architecture distinguishes between:

- Packages
- Plugins
- Runtime Registries
- Runtime Configuration
- Runtime Instances

Only packages may contain executable code.

Runtime configuration never contains executable code.

---

# Architectural Principle

> **Packages deliver executable implementations.**
>
> **Registries expose available capabilities.**
>
> **Runtime configuration selects and configures capabilities.**
>
> **The database never stores executable application code.**

---

# High-Level Architecture

```text
Developer

        │

        ▼

Plugin Package

        │

        ▼

Package Manifest

        │

        ▼

Installation

        │

        ▼

Registry

        │

        ▼

Runtime Configuration

        │

        ▼

Application
```

---

# Package

A package represents a deployable software unit.

A package may contain:

- Python code
- React components
- Static assets
- Templates
- Documentation
- Tests
- Manifests

A package is installed through the deployment process.

Packages are immutable after installation.

---

# Plugin

A plugin is a logical extension provided by a package.

One package may provide multiple plugins.

Examples:

- Ollama Provider
- OpenAI Provider
- Calendar Integration
- Email Integration
- Markdown Renderer
- OCR Provider

Plugins become available only after successful registration.

---

# Package Manifest

Every package contains a manifest describing its capabilities.

Typical information includes:

- package identifier
- package version
- compatible platform versions
- provided plugins
- dependencies
- permissions
- capabilities
- migrations
- documentation

The manifest is declarative.

It never contains executable logic.

---

# Plugin Manifest

Each plugin provides its own manifest.

Typical metadata includes:

- plugin identifier
- display name
- description
- version
- implementation type
- supported capabilities
- configuration schema
- required permissions
- lifecycle hooks

The manifest allows the platform to validate compatibility before activation.

---

# Registration

Plugin discovery never enables functionality automatically.

Registration consists of:

- manifest validation
- compatibility verification
- dependency verification
- identifier uniqueness
- capability validation

Only successfully registered plugins become available.

---

# Activation

Registration and activation are separate operations.

A registered plugin may remain disabled.

Activation requires:

- successful validation
- administrator approval
- compatible platform version
- satisfied dependencies

---

# Runtime Configuration

Runtime configuration determines:

- whether a plugin is enabled
- configuration values
- hierarchy assignments
- permissions
- visibility
- limits
- policies

Configuration is stored in the database.

Changing configuration never changes executable code.

---

# Package Lifecycle

Every package follows a consistent lifecycle.

```text
Package

↓

Installed

↓

Validated

↓

Registered

↓

Available

↓

Activated

↓

Running

↓

Disabled

↓

Removed
```

---

# Plugin Lifecycle

Plugins follow their own lifecycle.

```text
Discovered

↓

Validated

↓

Registered

↓

Inactive

↓

Active

↓

Deprecated

↓

Disabled

↓

Archived
```

---

# Dependency Management

Packages may declare dependencies.

Examples include:

- minimum platform version
- required registry types
- required providers
- required plugins

Dependency resolution occurs before activation.

Circular dependencies are rejected.

---

# Version Compatibility

Packages declare supported platform versions.

Examples:

- minimum version
- maximum version
- supported contract versions
- supported schema versions

Incompatible packages cannot be activated.

---

# Registry Integration

Packages never communicate directly with application internals.

Instead they register capabilities through registries.

Examples:

- Model Registry
- Tool Registry
- Widget Registry
- Action Registry
- Resource Registry
- Search Registry
- Integration Registry

The application communicates only with registries.

---

# Runtime Safety

Packages cannot bypass platform security.

All operations continue to use:

- authorization
- validation
- audit logging
- revision management
- configuration services

Plugins never receive unrestricted system access.

---

# Security

The platform explicitly forbids:

- execution of database-stored Python code
- execution of uploaded JavaScript
- arbitrary imports
- dynamic eval()
- unrestricted reflection
- loading modules from uncontrolled locations

Executable code must always originate from trusted packages.

---

# Administrative Interfaces

The administration UI may provide:

- installed packages
- available plugins
- compatibility information
- dependency graphs
- activation status
- update availability
- validation results

Administrators never edit package contents.

---

# Future Marketplace

The architecture supports a future package marketplace.

Possible package categories include:

- AI Providers
- Tools
- Widgets
- Integrations
- Themes
- Workflow Activities
- Resource Types
- Search Providers

Marketplace support does not change the security model.

Every package must still pass validation before activation.

---

# Consequences

## Positive

### Strong Separation of Responsibilities

Packages deliver executable functionality.

Runtime configuration controls behavior.

---

### Secure Runtime

The database never contains executable application code.

---

### Predictable Deployments

Every executable component is versioned and reproducible.

---

### Stable Extension Model

All extensibility follows the same registration process.

---

### Easier Testing

Packages can be tested independently before installation.

---

### Marketplace Ready

Future package repositories can reuse the same architecture.

---

## Negative

### Higher Initial Complexity

Package management requires additional infrastructure.

---

### Manifest Maintenance

Every package must provide complete metadata.

---

### Compatibility Management

Version compatibility must be maintained over time.

---

### Controlled Installation

Adding executable functionality requires package installation rather than database configuration.

---

# Alternatives Considered

## Direct Dynamic Imports

Advantages

- Very simple implementation

Disadvantages

- Unsafe
- Difficult to validate
- Hard to reproduce
- Hidden dependencies

Rejected.

---

## Executable Database Plugins

Advantages

- Maximum runtime flexibility

Disadvantages

- Major security risks
- Impossible to audit reliably
- Uncontrolled execution
- Difficult debugging

Rejected.

---

## Runtime JavaScript Execution

Advantages

- Flexible frontend behavior

Disadvantages

- Security risks
- Difficult sandboxing
- Contract violations
- Unpredictable behavior

Rejected.

---

## Hardcoded Extensions

Advantages

- Simple implementation

Disadvantages

- Poor scalability
- Frequent core modifications
- Violates Open/Closed Principle

Rejected.

---

# Related ADRs

- ADR-0001 — Schema-Driven User Interface
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0009 — Runtime Registry Architecture
- ADR-0010 — Generic Resource Architecture
- ADR-0011 — Widget Architecture
- ADR-0012 — Action Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0019 — Audit and Revision Architecture
- ADR-0022 — Integration Architecture
- ADR-0028 — AI Model Architecture
- ADR-0029 — Tool Execution Architecture

---

# Implementation Notes

The first MVP supports only trusted local packages delivered with the application.

Future marketplace support, package signing, automatic updates and external repositories are intentionally outside the MVP but are fully compatible with this architecture.
