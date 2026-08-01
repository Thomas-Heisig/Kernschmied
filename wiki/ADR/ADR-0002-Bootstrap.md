# ADR-0002: Bootstrap Configuration and Runtime Initialization

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

## Context

Kernschmied is designed as a highly configurable platform whose business behavior can evolve at runtime without requiring application redeployment.

The platform supports:

- Runtime configuration
- Multiple deployment profiles
- Dynamic hierarchies
- Configurable AI models
- Tool registries
- UI schemas
- Multi-tenant extensions (future)
- Plugin-based capabilities

At the same time, the application must remain secure and deterministic during startup.

A fundamental architectural question therefore arises:

> **Which configuration belongs to application startup, and which belongs to the runtime configuration stored in the database?**

Without a clear separation, applications often accumulate hundreds of environment variables that mix infrastructure concerns with business configuration, making deployments difficult to understand and maintain.

---

## Problem

Many applications eventually use environment variables for nearly everything:

- Feature flags
- Company information
- UI settings
- Model configuration
- Tool configuration
- Workflow behavior
- Security settings
- API endpoints
- Business defaults

This creates several problems.

## Environment Variables Become Business Configuration

Infrastructure settings become mixed with application behavior.

Changing a company name may suddenly require restarting the application.

---

## Difficult Operations

Large `.env` files become difficult to manage.

Typical production systems eventually contain hundreds of variables.

---

## Poor Runtime Flexibility

Changing configuration requires:

- editing files
- restarting services
- redeployment

instead of simply updating runtime configuration.

---

## Lack of Validation

Environment variables are typically:

- strings
- untyped
- difficult to validate
- inconsistent

---

## Inconsistent Deployments

Different environments often drift because `.env` files are edited manually.

---

## Decision

Kernschmied separates configuration into two distinct categories:

1. **Bootstrap Configuration**
2. **Runtime Configuration**

Bootstrap configuration is loaded during application startup.

Runtime configuration is loaded after the application has initialized and is stored in the database.

---

## Architectural Principle

> **Bootstrap configuration starts the platform.  
> Runtime configuration defines platform behavior.**

---

## Bootstrap Configuration

Bootstrap configuration represents the minimum information required for the application to start safely.

Typical examples include:

- Deployment profile
- Database connection
- Secret keys
- HTTPS configuration
- Logging
- Allowed model directories
- File storage paths
- Initial administrator bootstrap
- Network ports

These values are infrastructure-related and generally require an application restart when changed.

---

## Runtime Configuration

Runtime configuration represents business behavior.

Examples include:

- AI model selection
- Prompt inheritance
- Hierarchy definitions
- UI schemas
- Available tools
- Feature configuration
- Company information
- Branding
- Business rules
- Workflow configuration

These values are stored in the database and may be modified through administrative interfaces.

---

## High-Level Architecture

```text
Application Start

        │

        ▼

Read Environment

        │

        ▼

Bootstrap Configuration

        │

        ▼

Initialize Infrastructure

        │

        ▼

Database Connection

        │

        ▼

Load Runtime Configuration

        │

        ▼

Initialize Registries

        │

        ▼

Application Ready

```

---

## Startup Sequence

The startup process follows a deterministic order.

```text
Process Starts

↓

Load Environment Variables

↓

Validate Bootstrap Configuration

↓

Create Logging

↓

Initialize Dependency Injection

↓

Connect Database

↓

Run Database Migrations

↓

Load Runtime Configuration

↓

Initialize Registries

↓

Build Configuration Cache

↓

Start HTTP Server

```

Each step depends only on previously initialized infrastructure.

---

## Responsibilities

## Bootstrap Layer

Responsible for:

- reading `.env`
- validating infrastructure settings
- database initialization
- logging
- security initialization
- dependency injection
- startup diagnostics

It never loads business logic.

---

## Runtime Configuration Layer

Responsible for:

- business configuration
- registries
- schemas
- prompts
- hierarchy
- models
- tools
- tenant settings (future)

---

## Why Not Store Everything in the Database?

The database cannot be used until it has been connected.

Therefore some information must always exist beforehand.

Examples:

- database credentials
- encryption keys
- deployment mode
- TLS certificates

These belong to bootstrap configuration.

---

## Why Not Store Everything in `.env`?

Business configuration changes frequently.

Restarting the application for every small configuration change would:

- interrupt users
- increase operational complexity
- encourage duplicated configuration
- reduce flexibility

---

## Runtime Reloading

Runtime-editable configuration may be reloaded without restarting the application.

Typical workflow:

```text
Administrator

↓

Update Configuration

↓

Configuration Revision++

↓

Cache Invalidated

↓

Reload

↓

Application Uses New Configuration

```

Infrastructure settings remain unchanged until the next application restart.

---

## Configuration Validation

Both configuration layers are validated independently.

## Bootstrap Validation

Performed immediately during startup.

Examples:

- missing database URL
- invalid secret
- invalid deployment profile
- malformed filesystem path

Startup fails if validation is unsuccessful.

---

## Runtime Validation

Performed whenever configuration changes.

Examples:

- invalid model reference
- invalid hierarchy node
- unknown tool
- invalid UI schema
- duplicate identifiers

Invalid configuration is rejected before activation.

---

## Deployment Profiles

Bootstrap configuration selects the deployment profile.

Supported profiles include:

## Development

Designed for local development.

Characteristics:

- simplified authentication
- verbose logging
- developer tooling
- relaxed CORS (configurable)

---

## Intranet

Designed for trusted internal networks.

Characteristics:

- authentication required
- auditing enabled
- moderate security defaults

---

## Internet

Designed for public deployment.

Characteristics:

- HTTPS required
- strict authentication
- rate limiting
- hardened security defaults
- conservative timeout configuration

Business configuration cannot weaken these minimum security requirements.

---

## Security Considerations

Bootstrap configuration contains sensitive information.

Examples include:

- secrets
- encryption keys
- certificates
- database credentials

These values must never be stored inside runtime business configuration.

Conversely, runtime configuration must never contain infrastructure secrets.

---

## Failure Handling

Bootstrap failures are fatal.

Examples:

- missing database
- invalid secret
- failed migration
- invalid deployment profile

The application should fail fast rather than continue in an undefined state.

Runtime configuration failures should be isolated whenever possible.

Invalid business configuration should not prevent unrelated services from operating.

---

## Consequences

## Positive

### Clear Separation of Concerns

Infrastructure and business configuration are independent.

---

### Easier Operations

Small business changes do not require restarting services.

---

### Better Validation

Each configuration layer can use appropriate validation rules.

---

### Improved Security

Secrets remain separated from business data.

---

### Better Maintainability

Configuration responsibilities remain well-defined as the system grows.

---

## Negative

### More Architectural Components

The platform requires:

- bootstrap loader
- runtime configuration service
- configuration revision tracking
- cache invalidation

---

### Additional Documentation

Developers must understand the distinction between both configuration layers.

---

## Alternatives Considered

## Everything in `.env`

Advantages:

- simple
- familiar

Disadvantages:

- poor scalability
- restart required
- difficult operations

Rejected.

---

## Everything in the Database

Advantages:

- centralized configuration

Disadvantages:

- bootstrap paradox
- impossible before database initialization
- infrastructure secrets stored alongside business configuration

Rejected.

---

## Configuration Files

Examples:

- YAML
- JSON
- TOML

Advantages:

- structured

Disadvantages:

- duplicated deployments
- synchronization problems
- manual editing
- restart required

Rejected as the primary configuration mechanism.

---

## Risks

Potential risks include:

- accidental placement of business settings in `.env`
- accidental storage of secrets in runtime configuration
- configuration drift
- incomplete validation

Mitigations include:

- configuration schemas
- automated validation
- audit logging
- configuration revision tracking
- administrative tooling

---

## Implementation Notes

The implementation should provide:

- typed bootstrap settings
- typed runtime settings
- dependency injection
- immutable bootstrap configuration
- versioned runtime configuration
- audit logging
- runtime cache invalidation
- structured startup diagnostics

---

## Related Decisions

- [[ADR-0001-Schema-Driven-UI]]
- [[ADR-0003-Registry-Based-Extension]]
- [[ADR-0004-Versioned-Contracts]]
- [[ADR-0005-Deny-by-Default-Security]]

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[Bootstrap-Lifecycle]]
- [[Configuration-Architecture]]
- [[Deployment-Architecture]]

## Backend

- [[Configuration]]
- [[Runtime-Configuration]]
- [[System-Configuration]]
- [[Startup]]

## Concepts

- [[Configuration-Revision]]
- [[Dependency-Injection]]
- [[Runtime-Configuration]]

---

## Decision Summary

Kernschmied separates **bootstrap configuration** from **runtime configuration**.

Bootstrap configuration provides the minimum infrastructure required to start the platform safely and is loaded from the environment during startup.

Runtime configuration defines the application's business behavior, is stored in the database, is fully validated and versioned, and may be updated without restarting the application.

This separation provides a clear operational model, improves security, simplifies deployments, and enables the platform to evolve dynamically while maintaining deterministic startup behavior.

---

Back to [[Home]].
