# Dependency Injection

The **Dependency Injection (DI)** architecture is the mechanism through which the Kernschmied backend constructs, manages, and provides shared infrastructure to application components.

Rather than allowing services to create or locate their own dependencies, the backend injects required infrastructure through well-defined interfaces. This approach reduces coupling, improves testability, simplifies lifecycle management, and ensures deterministic application behavior.

Kernschmied relies on **FastAPI's dependency injection system** together with explicit bootstrap initialization. There is no global service locator, hidden singleton magic, or implicit dependency discovery.

---

## Goals

The Dependency Injection architecture is designed to provide:

- Loose coupling
- Explicit dependencies
- Deterministic object creation
- Simplified testing
- Shared infrastructure
- Clear lifecycle management
- Better maintainability
- Stable architectural boundaries

---

## Design Principles

## Explicit Dependencies

Every component explicitly declares the services it requires.

Example:

```text
Chat Service

↓

Configuration Service

↓

Model Registry

↓

Database Session

```

Nothing is created implicitly.

---

## Constructor Injection

Application services receive dependencies through constructors whenever practical.

Example:

```text
ChatService

↓

ConfigurationService

↓

ModelRegistry

↓

PromptResolver

```

Dependencies remain visible and testable.

---

## No Service Locator

Services never search for dependencies at runtime.

The following pattern is intentionally avoided:

```text
Service

↓

Global Registry

↓

Hidden Dependency

```

Instead, dependencies are injected before the service is used.

---

## Infrastructure Before Business Logic

Infrastructure is created during bootstrap.

Business services consume infrastructure rather than constructing it.

---

## High-Level Architecture

```text
Bootstrap

↓

Infrastructure

↓

Dependency Injection

↓

Application Services

↓

Repositories / Providers

```

Bootstrap owns infrastructure creation.

---

## Why Dependency Injection?

Without dependency injection, services would create their own infrastructure.

```text
Chat Service

↓

Create Database

↓

Create Registry

↓

Create Provider

```

This approach leads to:

- tight coupling
- duplicated initialization
- difficult testing
- inconsistent lifecycles

Dependency injection avoids these problems.

---

## Dependency Categories

Typical injected dependencies include:

- database sessions
- configuration service
- configuration resolver
- model registry
- tool registry
- prompt resolver
- authenticated user
- request context
- logger

Application code should depend on abstractions rather than implementation details.

---

## Application Bootstrap

Bootstrap creates shared infrastructure.

Typical sequence:

```text
Environment

↓

Database

↓

Configuration

↓

Registries

↓

Services

↓

FastAPI

```

Only after successful initialization does the application begin processing requests.

---

## FastAPI Integration

FastAPI resolves request-specific dependencies automatically.

Typical flow:

```text
HTTP Request

↓

Dependency Resolver

↓

Endpoint

↓

Service

```

Dependency resolution occurs before endpoint execution.

---

## Request Scope

Certain dependencies exist only for the lifetime of a single request.

Examples include:

- database session
- authenticated user
- request context
- request identifier

These objects are disposed of automatically when the request finishes.

---

## Application Scope

Some dependencies are shared across the application.

Typical examples include:

- model registry
- tool registry
- configuration service
- provider factories

These objects are created during bootstrap and reused.

---

## Service Construction

Application services receive infrastructure rather than creating it.

Example:

```text
Configuration Service

↓

Prompt Resolver

↓

Chat Service

```

This keeps services focused on business logic.

---

## Repository Injection

Repositories receive database sessions through dependency injection.

```text
Request

↓

Database Session

↓

Repository

↓

Database

```

Repositories never create their own sessions.

---

## Registry Injection

Registries are injected wherever runtime metadata is required.

Example:

```text
Chat Service

↓

Model Registry

↓

Tool Registry

```

The service remains unaware of registry implementation details.

---

## Provider Injection

Provider factories or provider abstractions are injected into services.

```text
Chat Service

↓

Model Registry

↓

Provider Backend

```

Services never instantiate provider implementations directly.

---

## Configuration Injection

Resolved configuration is made available through dedicated services or resolvers.

```text
Configuration Resolver

↓

Resolved Configuration

↓

Application Service

```

Configuration resolution remains centralized.

---

## Request Context

A request context object may contain:

- request identifier
- authenticated user
- timestamps
- hierarchy references
- metadata

The context accompanies request processing without introducing global state.

---

## Authentication

Authenticated user information is injected into endpoints and services.

```text
Authentication

↓

User Context

↓

Authorization

↓

Business Logic

```

Security-sensitive information is not retrieved through global variables.

---

## Logging

Structured loggers may be injected where appropriate.

Logging infrastructure remains centralized while allowing contextual logging within services.

---

## Lifecycle Management

Dependencies have clearly defined lifetimes.

| Lifetime    | Examples                          |
| ----------- | --------------------------------- |
| Application | Registries, configuration service |
| Request     | Database session, request context |
| Transient   | Temporary helper objects          |

Correct lifetime management prevents resource leaks.

---

## Immutability

Injected infrastructure should remain immutable whenever possible.

Examples include:

- registries
- configuration snapshots
- provider metadata

Immutable objects simplify reasoning about application behavior.

---

## Testing

Dependency injection greatly simplifies testing.

Instead of constructing real infrastructure, tests can inject:

- mock repositories
- fake providers
- test registries
- in-memory configuration

Example:

```text
Test

↓

Fake Model Registry

↓

Chat Service

↓

Assertions

```

Production code remains unchanged.

---

## Error Handling

Dependency resolution failures are treated as infrastructure failures.

Example:

```text
Database Unavailable

↓

Dependency Creation Failed

↓

Application Error

```

Such failures are detected before business logic executes.

---

## Performance

Dependency injection improves performance by:

- reusing shared infrastructure
- avoiding unnecessary object creation
- minimizing initialization work during requests
- allowing efficient resource pooling

The dependency graph should remain lightweight and deterministic.

---

## Security

Dependency injection contributes to security by:

- preventing unauthorized object creation
- centralizing infrastructure initialization
- controlling service lifetimes
- ensuring consistent authorization infrastructure

Security-sensitive services are initialized only through trusted bootstrap logic.

---

## Anti-Patterns

The following practices should be avoided.

## Hidden Singletons

Avoid:

```text
Global Instance

↓

Used Everywhere

```

Use injected shared services instead.

---

## Service Locator

Avoid:

```python
service = GlobalRegistry.get("configuration")
```

Services should declare dependencies explicitly.

---

## Manual Construction

Avoid:

```python
database = Database()
repository = Repository(database)
service = ChatService(repository)
```

Object graphs should be assembled during bootstrap rather than within request handlers.

---

## Future Extensions

The architecture supports future enhancements including:

- scoped dependency containers
- plugin-provided services
- tenant-specific dependency graphs
- diagnostics for dependency resolution
- lifecycle monitoring

These additions can be introduced without changing existing service contracts.

---

## Relationship to Other Backend Components

Dependency Injection connects all backend layers.

```text
Bootstrap

↓

Dependency Injection

↓

Services

↓

Repositories

↓

Providers

```

It acts as the infrastructure backbone of the backend.

---

## Relationship to Architecture

Dependency Injection integrates closely with:

- [[Bootstrap-Lifecycle]]
- [[Configuration-Architecture]]
- [[Registry-Architecture]]
- [[Request-Lifecycle]]
- [[Security-Architecture]]

---

## Related Documentation

## Backend

- [[Backend-Overview]]
- [[Bootstrap]]
- [[Services]]
- [[Repositories]]
- [[Provider-System]]
- [[Configuration]]

---

## Architecture

- [[Bootstrap-Lifecycle]]
- [[Registry-Architecture]]
- [[Request-Lifecycle]]
- [[Security-Architecture]]

---

## APIs

- [[Bootstrap]]
- [[Configuration]]
- [[Chat]]

---

## Summary

The Dependency Injection architecture provides the foundation for constructing and managing shared infrastructure throughout the Kernschmied backend.

By relying on explicit dependencies, deterministic bootstrap initialization, FastAPI's dependency injection system, well-defined object lifetimes, and strict separation between infrastructure and business logic, the backend remains modular, testable, maintainable, and scalable while avoiding hidden dependencies, global state, and service locator patterns.

---

Back to [[Home]].
