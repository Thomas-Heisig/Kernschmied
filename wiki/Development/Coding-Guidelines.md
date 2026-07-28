# Coding Guidelines

The Coding Guidelines define the engineering standards used throughout the Kernschmied project. Their purpose is not merely to enforce a consistent coding style, but to ensure that the system remains maintainable, extensible, testable, and secure as it grows.

Kernschmied follows the principle that **architecture is more important than syntax**. Readable, deterministic, and well-structured software is preferred over clever or overly abstract implementations.

These guidelines apply to both backend and frontend development, as well as plugins and shared libraries.

---

# Goals

The Coding Guidelines are designed to provide:

- Consistent code quality
- Long-term maintainability
- Predictable architecture
- High readability
- Strong type safety
- Secure implementations
- Easy testing
- Stable public contracts

---

# General Principles

Every contribution should follow these principles:

- Write code for humans first.
- Prefer clarity over cleverness.
- Keep modules small and focused.
- Avoid unnecessary abstractions.
- Make dependencies explicit.
- Fail early and predictably.
- Validate data at system boundaries.
- Prefer composition over inheritance.

---

# Clean Architecture

Application code should be organized into clearly separated layers.

```text
Presentation

↓

Application

↓

Domain

↓

Infrastructure
```

Each layer has a well-defined responsibility.

---

# Single Responsibility

Each class, module, and function should have one primary responsibility.

Good example:

```text
ConfigurationResolver

↓

Resolves configuration
```

Poor example:

```text
ConfigurationResolver

↓

Loads files

↓

Validates schemas

↓

Writes database

↓

Logs users

↓

Starts services
```

Responsibilities should remain focused.

---

# Dependency Injection

Dependencies should always be injected rather than created internally.

Preferred:

```text
Service

↓

Repository

↓

Database
```

Avoid:

```text
Service

↓

new Database()
```

Dependency Injection improves testing and modularity.

---

# Explicit Dependencies

Hidden dependencies should be avoided.

Constructors and function signatures should clearly express required dependencies.

```text
ChatService(
    repository,
    configuration,
    model_registry,
)
```

Dependencies should never appear unexpectedly through global state.

---

# Avoid Global State

Global mutable state makes systems difficult to understand and test.

Avoid:

- mutable singletons
- shared mutable variables
- hidden caches
- implicit runtime state

Instead, use scoped services managed through dependency injection.

---

# Type Safety

Use strong typing wherever possible.

Backend:

- Python type hints
- Pydantic models
- Protocols
- Typed collections

Frontend:

- TypeScript
- Interfaces
- Generic types
- Discriminated unions

Avoid using untyped data structures unless absolutely necessary.

---

# Small Modules

Modules should remain focused.

Preferred:

```text
Configuration

Validation

Resolver

Storage
```

Avoid:

```text
ConfigurationEverything.py
```

Smaller modules improve readability and testing.

---

# Naming

Names should be:

- descriptive
- consistent
- domain-oriented
- unambiguous

Avoid abbreviations unless universally understood.

Good examples:

- ConfigurationResolver
- HierarchyService
- ModelRegistry
- ToolManifest

Poor examples:

- Utils
- Manager
- Helper2
- Stuff

---

# Functions

Functions should:

- perform one task
- remain short
- return predictable results
- avoid hidden side effects

Large functions should be split into smaller units.

---

# Classes

Classes should encapsulate behavior rather than collect unrelated utilities.

Good classes:

- ConfigurationService
- BootstrapManager
- ToolRegistry

Avoid "God Objects" responsible for unrelated features.

---

# Error Handling

Errors should be explicit and structured.

Avoid:

- silent failures
- ignored exceptions
- generic catch-all handlers

Prefer:

```text
Validate

↓

Raise Specific Error

↓

Structured Response
```

Errors should preserve useful diagnostic information.

---

# Validation

Validate all external input.

Examples include:

- REST requests
- configuration
- manifests
- plugin metadata
- database input
- environment variables

Never trust external input.

---

# Immutability

Prefer immutable objects whenever practical.

Immutable data:

- is easier to reason about
- simplifies testing
- improves thread safety
- reduces unintended side effects

---

# Avoid Magic Values

Hardcoded values should be avoided.

Instead of:

```text
42
```

Prefer:

```text
DEFAULT_TIMEOUT_SECONDS
```

Named constants improve readability.

---

# Configuration

Business configuration belongs in Runtime Configuration.

Infrastructure configuration belongs in environment variables.

Never mix the two.

---

# Logging

Logging should be:

- structured
- meaningful
- concise
- actionable

Avoid excessive logging.

Sensitive information must never appear in logs.

---

# Documentation

Public components should be documented.

Documentation should explain:

- purpose
- responsibilities
- contracts
- limitations

Documentation should explain **why**, not merely **what**.

---

# Comments

Comments should be rare.

Prefer self-explanatory code.

Use comments to explain:

- architectural decisions
- unusual algorithms
- non-obvious constraints

Avoid comments that simply repeat the code.

---

# Testing

Every new feature should include appropriate tests.

Recommended test categories include:

- unit tests
- integration tests
- schema validation
- API tests
- registry tests

Testing should focus on observable behavior rather than implementation details.

---

# Security

Security is everyone's responsibility.

Always:

- validate input
- authorize actions
- sanitize external data
- protect secrets
- use least privilege

Never rely on frontend validation alone.

---

# Performance

Optimize only after measuring.

Prefer:

- readable code
- correct behavior
- deterministic execution

Avoid premature optimization.

---

# API Design

Public APIs should be:

- versioned
- predictable
- documented
- stable

Breaking changes require explicit version evolution.

---

# Backend Guidelines

Backend services should:

- expose clear interfaces
- use dependency injection
- validate inputs
- remain provider-independent
- return structured errors

Business logic should not depend on framework-specific implementation details.

---

# Frontend Guidelines

Frontend components should:

- remain generic
- avoid business-specific assumptions
- use the Schema Renderer
- rely on the Component Registry
- remain strongly typed

Business behavior belongs in backend-generated schemas.

---

# Plugin Guidelines

Plugins should:

- use documented extension points
- provide valid manifests
- avoid internal APIs
- remain self-contained
- respect version compatibility

Plugins extend the platform—they do not modify it.

---

# Database Guidelines

Database access should:

- use repositories
- avoid business logic inside queries
- validate persistence models
- remain database-independent where practical

Services should not construct SQL directly.

---

# Review Checklist

Before merging code, verify:

- Architecture remains consistent.
- Contracts remain stable.
- Tests pass.
- Validation is complete.
- Error handling is explicit.
- Documentation is updated.
- Security considerations were reviewed.
- Naming is clear.
- Dependencies are explicit.
- Public APIs remain compatible.

---

# Common Anti-Patterns

Avoid:

- God objects
- Circular dependencies
- Hidden state
- Static mutable data
- Copy-and-paste implementations
- Large utility classes
- Business logic in controllers
- Framework-dependent domain logic
- Silent exception handling

These patterns reduce maintainability.

---

# Future Evolution

The Coding Guidelines are expected to evolve together with the platform.

Future additions may include:

- performance recommendations
- accessibility guidelines
- internationalization practices
- plugin quality standards
- automated code quality metrics
- architecture conformance checks

The overall philosophy of simplicity, explicitness, and stability should remain unchanged.

---

# Related Documentation

## Development

- [[Development Environment]]
- [[Testing]]
- [[Debugging]]

---

## Architecture

- [[Repository-Structure]]
- [[Extension-Points]]
- [[Contract-Versioning]]
- [[Security-Architecture]]

---

## Concepts

- [[Runtime Configuration]]
- [[Plugin-System]]
- [[Schema Versioning]]
- [[Dynamic-UI]]

---

# Summary

The Coding Guidelines establish a consistent engineering standard for every part of Kernschmied. They emphasize readability, explicit dependencies, strong typing, deterministic behavior, modular design, and secure implementations over clever or overly complex solutions.

By following these principles across the backend, frontend, plugins, and shared infrastructure, contributors help ensure that Kernschmied remains maintainable, extensible, and reliable as the platform continues to grow.

---

Back to [[Home]].
