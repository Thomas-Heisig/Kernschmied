# Configuration Architecture

The **Configuration Architecture** defines how runtime configuration is stored, validated, inherited, versioned, and consumed throughout the Kernschmied platform.

Unlike many traditional applications where business configuration is stored in configuration files, Kernschmied separates **bootstrap configuration** from **runtime configuration**.

Infrastructure and security bootstrap values remain outside the database, while business-related configuration is stored in the database, validated through schemas, and distributed through deterministic configuration resolution.

This architecture allows administrators to modify business behavior without redeploying the application while preserving security, stability, and version compatibility.

---

## Goals

The configuration architecture is designed to provide:

- Centralized configuration management
- Strong validation
- Versioned configuration
- Deterministic inheritance
- Runtime updates
- Safe caching
- Auditability
- Security isolation
- Provider independence

---

## Design Principles

The configuration subsystem follows several fundamental principles.

## Configuration is Data

Configuration is treated as structured application data rather than source code.

Configuration is:

- validated
- versioned
- auditable
- cached
- resolved
- inherited

---

## Bootstrap Configuration is Static

Bootstrap configuration defines how the application starts.

Examples include:

- database connection
- deployment profile
- logging
- HTTPS
- secret keys
- CORS defaults

These values are typically loaded from:

- `.env`
- environment variables
- startup configuration

They are **not** editable through the administration interface.

---

## Runtime Configuration is Dynamic

Business configuration is stored inside the database.

Examples:

- default models
- prompts
- UI settings
- provider selection
- feature configuration
- hierarchy defaults
- chat settings

Runtime configuration may be modified without restarting the application.

---

## Separation of Responsibilities

```text
                Configuration

                    │

        ┌───────────┴────────────┐

        │                        │

Bootstrap Configuration   Runtime Configuration

(.env)                    (Database)

```

This separation prevents accidental modification of infrastructure settings.

---

## Bootstrap Configuration

Bootstrap configuration includes infrastructure values that are required before the application can start.

Typical examples:

- database URL
- deployment profile
- secret keys
- HTTPS configuration
- log level
- application name

These values are immutable while the application is running.

---

## Runtime Configuration

Runtime configuration contains all business-specific settings.

Typical examples include:

- default model
- enabled tools
- system prompts
- hierarchy behavior
- UI defaults
- provider settings
- feature flags

Runtime configuration is resolved dynamically for every request.

---

## Configuration Sources

The platform may obtain configuration from multiple sources.

```text
Environment Variables

↓

Bootstrap Configuration

↓

Database

↓

Request Context

↓

Resolved Configuration

```

Higher-priority sources override lower-priority sources where appropriate.

---

## Configuration Storage

Runtime configuration is stored in the database.

Typical entities include:

- system configuration
- configuration revisions
- audit log
- hierarchy overrides
- user preferences

The storage format remains independent of the consuming services.

---

## Configuration Schema

Every configuration entry is validated using a schema.

Example:

```json
{
  "key": "chat.default_model",
  "value": "qwen2.5-coder:7b
}
```

The schema determines:

- type
- validation rules
- allowed values
- default value
- documentation

---

## Configuration Validation

Validation occurs before configuration becomes active.

Typical validation checks include:

- required fields
- data types
- numeric ranges
- enumerations
- object structure
- references
- schema version

Invalid configuration is rejected.

---

## Configuration Resolver

Applications never access configuration storage directly.

Instead, all services use the Configuration Resolver.

```text
Database

↓

Configuration Repository

↓

Configuration Resolver

↓

Business Service

```

The resolver is responsible for inheritance and merging.

---

## Configuration Scopes

Configuration exists at multiple scopes.

```text
SYSTEM

↓

NODE

↓

PROJECT

↓

CHAT

↓

USER

↓

REQUEST

```

Each scope may override values defined by higher scopes.

---

## Scope Definitions

## System

Global defaults for the entire platform.

Examples:

- default model
- global prompts
- default tool set

---

## Node

Configuration attached to hierarchy nodes.

Examples:

- department prompt
- project defaults
- permissions

---

## Project

Project-specific configuration.

Examples:

- model selection
- custom prompts
- enabled tools

---

## Chat

Conversation-specific settings.

Examples:

- temporary model
- active tool list
- context limits

---

## User

User preferences.

Examples:

- language
- UI theme
- preferred model

---

## Request

Temporary configuration valid only during a single request.

Examples:

- explicitly selected model
- tool overrides
- request metadata

---

## Configuration Resolution

Configuration is resolved from top to bottom.

```text
System

↓

Node

↓

Project

↓

Chat

↓

User

↓

Request

↓

Resolved Configuration

```

Each level overrides previous values where permitted.

---

## Merge Strategies

Different configuration types require different merge behavior.

Supported merge strategies include:

| Strategy   | Description          |
| ---------- | -------------------- |
| replace    | Complete replacement |
| extend     | Append values        |
| deep_merge | Merge nested objects |

The merge strategy is defined by the configuration schema.

---

## Example Resolution

```text
System

default_model = qwen

↓

Project

default_model = mistral

↓

Request

default_model = gemma

↓

Resolved = gemma

```

The request scope has the highest priority.

---

## Configuration Revisions

Every successful runtime modification increments the global configuration revision.

```text
Configuration Updated

↓

Revision++

↓

Clients Detect Change

↓

Reload

```

This allows efficient cache invalidation.

---

## Runtime Updates

Configuration changes become active immediately if marked as runtime editable.

```text
Admin

↓

Configuration API

↓

Validation

↓

Database

↓

Revision++

↓

Runtime

```

No restart is required.

---

## Non-Runtime Configuration

Some configuration changes require a restart.

Examples:

- database connection
- deployment profile
- HTTPS certificates

These values remain outside the runtime configuration system.

---

## Caching

Configuration resolution is optimized using caching.

Typical cache levels include:

- configuration repository
- resolved configuration
- schema metadata

Caches are invalidated using configuration revisions.

---

## Dependency Injection

Services receive configuration through dependency injection.

```text
Configuration Resolver

↓

Application Service

↓

Business Logic

```

Services never access configuration storage directly.

---

## Audit Logging

Every configuration modification generates an audit log entry.

Typical audit information includes:

- timestamp
- user
- changed key
- previous value
- new value
- request identifier

This enables complete traceability.

---

## Security

Configuration architecture enforces several security rules.

Secrets are never stored inside business configuration.

Examples:

- API keys
- passwords
- certificates

remain outside runtime configuration.

Authorization is required for all configuration changes.

---

## Versioning

Configuration schemas are versioned independently.

This allows:

- schema evolution
- backward compatibility
- migrations
- validation updates

Applications resolve configuration according to the active schema version.

---

## Failure Handling

Invalid configuration never becomes active.

```text
Update Request

↓

Validation Failed

↓

Reject Update

↓

Previous Configuration Remains Active

```

This guarantees platform stability.

---

## Relationship to Bootstrap

Bootstrap exposes only metadata about configuration.

Examples:

- configuration revision
- supported versions

The actual configuration is retrieved through dedicated APIs.

---

## Relationship to Hierarchy

Hierarchy nodes may contribute configuration.

```text
Hierarchy Node

↓

Configuration Override

↓

Resolver

↓

Resolved Configuration

```

Hierarchy therefore becomes part of the configuration pipeline.

---

## Relationship to Prompt Inheritance

Prompt inheritance is implemented using the same configuration resolution mechanism.

Prompt values participate in the standard scope resolution process.

---

## Relationship to Registries

Model and tool registries consume configuration to determine:

- enabled providers
- defaults
- capabilities
- restrictions

Registries never modify configuration directly.

---

## Performance Considerations

Configuration resolution is optimized for:

- low latency
- minimal database access
- deterministic results
- cache reuse

Resolution should be inexpensive enough to occur for every request.

---

## Future Extensions

The architecture allows future additions such as:

- tenant-specific configuration
- localization
- plugin configuration
- policy engines
- remote configuration synchronization
- configuration templates

These extensions can be introduced without changing the public configuration contracts.

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[Bootstrap-Lifecycle]]
- [[Hierarchy-Architecture]]
- [[Prompt-Inheritance]]
- [[Registry-Architecture]]
- [[Repository-Structure]]

---

## APIs

- [[Configuration]]
- [[Bootstrap]]
- [[Hierarchy]]

---

## ADRs

- [[ADR-0010-Configuration-Management]]
- [[ADR-0011-Hierarchy-and-Prompt-Inheritance]]
- [[ADR-0005-Versioned-Contracts]]

---

## Summary

The Configuration Architecture provides a deterministic, validated, and versioned runtime configuration system that clearly separates immutable bootstrap settings from dynamic business configuration.

By combining schema validation, scoped inheritance, configurable merge strategies, revision-based cache invalidation, and centralized configuration resolution, Kernschmied enables safe runtime customization while maintaining predictable behavior, strong security boundaries, and long-term architectural stability.

---

Back to [[Home]].
