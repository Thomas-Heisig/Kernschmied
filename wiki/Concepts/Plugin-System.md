# Plugin System

The **Plugin System** enables Kernschmied to be extended through independently developed modules without requiring modifications to the application core.

Instead of embedding every feature directly into the backend or frontend, plugins provide additional capabilities through well-defined manifests, registries, schemas, and stable interfaces. The core platform remains responsible for discovery, validation, authorization, lifecycle management, and security.

A fundamental design principle is:

> **Plugins extend the platform, but they never become part of the platform itself.**

Every plugin operates within clearly defined architectural boundaries.

---

# Goals

The Plugin System is designed to provide:

- Runtime extensibility
- Stable extension points
- Manifest-driven discovery
- Strong validation
- Secure execution
- Provider independence
- Version compatibility
- Long-term maintainability

---

# Core Principles

## Extension, Not Modification

Plugins add functionality.

They do **not** modify existing application code.

```text
Core Platform

+

Plugin

↓

Extended Functionality
```

The core application remains unchanged regardless of installed plugins.

---

## Stable Contracts

Plugins communicate exclusively through documented contracts.

They never depend on:

- internal classes
- database schemas
- private APIs
- implementation details

This allows the platform to evolve without breaking compatible plugins.

---

## Explicit Registration

Every plugin must be explicitly discovered and registered.

```text
Plugin Directory

↓

Manifest Discovery

↓

Validation

↓

Registry

↓

Available Plugin
```

Unknown directories are ignored.

---

## Secure by Default

A plugin is **not trusted simply because it exists**.

Every plugin must:

- provide a valid manifest
- pass schema validation
- satisfy compatibility requirements
- expose only supported extension points

Registration does not imply authorization.

---

# High-Level Architecture

```text
Plugin Package

↓

Manifest

↓

Plugin Registry

↓

Backend / Frontend Integration

↓

Application
```

The Plugin Registry acts as the central coordination point.

---

# Plugin Structure

A typical plugin contains:

```text
plugin/

├── plugin.json
├── backend/
├── frontend/
├── schemas/
├── assets/
└── README.md
```

Only the manifest is required for discovery.

---

# Plugin Manifest

Each plugin provides a versioned manifest.

Typical information includes:

- plugin identifier
- display name
- version
- schema version
- author
- description
- compatible platform versions
- capabilities
- extension points

The manifest is validated during bootstrap.

---

# Plugin Discovery

Plugin discovery occurs during application startup.

```text
Search Plugin Directories

↓

Read plugin.json

↓

Validate Manifest

↓

Register Plugin

↓

Application Ready
```

Plugins with invalid manifests are rejected.

---

# Plugin Registry

The Plugin Registry maintains metadata about installed plugins.

Typical responsibilities include:

- discovery
- validation
- registration
- compatibility checks
- revision tracking
- metadata lookup

The registry does not execute plugin code.

---

# Plugin Lifecycle

A plugin typically progresses through the following lifecycle.

```text
Discovered

↓

Validated

↓

Registered

↓

Initialized

↓

Available

↓

Disabled / Removed
```

Each state transition is deterministic.

---

# Backend Plugins

Backend plugins may contribute:

- tools
- model providers
- schemas
- configuration
- API extensions
- validators

Business services remain independent of plugin implementations.

---

# Frontend Plugins

Frontend plugins may contribute:

- UI schemas
- component registrations
- action registrations
- icons
- translations
- documentation

They operate through predefined frontend extension points.

---

# Manifest Validation

Validation includes:

- schema version
- required fields
- unique identifier
- version format
- supported capabilities
- compatible platform version

Invalid manifests prevent registration.

---

# Version Compatibility

Plugins declare supported platform versions.

Example:

```text
Plugin

↓

Compatible With

↓

Platform Version
```

Incompatible plugins are rejected during startup.

---

# Extension Points

Plugins may extend only documented extension points.

Examples include:

- Tool Registry
- Model Registry
- UI Schema generation
- Action Registry
- Component Registry
- configuration providers

Undocumented internal APIs are not considered stable extension points.

---

# Configuration

Plugins may define configuration schemas.

Configuration is:

- validated
- versioned
- stored in the database
- resolved through the Configuration Service

Plugins never read raw configuration directly from storage.

---

# Schema Integration

Plugins may contribute schemas.

Typical schema categories include:

- UI schemas
- configuration schemas
- validation schemas
- tool input schemas
- tool output schemas

All schemas must be versioned.

---

# Registry Integration

Plugins integrate with existing registries rather than replacing them.

```text
Plugin

↓

Registry

↓

Application Services
```

Registries remain the authoritative source of runtime metadata.

---

# Tool Integration

Plugins may contribute executable tools.

```text
Plugin

↓

Tool Manifest

↓

Tool Registry

↓

Authorized Execution
```

Tool execution follows the standard security pipeline.

---

# Model Integration

Plugins may contribute model providers.

```text
Plugin

↓

Provider Manifest

↓

Model Registry

↓

Provider Backend
```

Provider implementations remain isolated behind stable interfaces.

---

# UI Integration

Plugins may contribute additional UI definitions.

```text
Plugin

↓

UI Schema

↓

Schema Renderer

↓

Rendered Interface
```

The frontend never executes arbitrary plugin code outside supported extension points.

---

# Security

The Plugin System enforces strict security boundaries.

Plugins:

- cannot bypass authorization
- cannot bypass validation
- cannot register undocumented extension points
- cannot replace core services
- cannot access private application state directly

Security policies are enforced by the core platform.

---

# Dependency Management

Plugins should minimize dependencies.

Recommended principles include:

- depend on public contracts
- avoid internal modules
- avoid circular dependencies
- keep plugins self-contained

The platform remains responsible for dependency resolution.

---

# Error Handling

Plugin failures are isolated.

Example:

```text
Plugin Error

↓

Registry

↓

Structured Error

↓

Remaining Plugins Continue
```

A faulty plugin should not compromise the entire platform whenever recovery is possible.

---

# Performance

The Plugin System is optimized for:

- deterministic startup
- lightweight discovery
- immutable metadata
- efficient registry lookups
- revision-aware caching

Runtime plugin discovery is avoided after bootstrap unless explicitly supported.

---

# Testing

Plugins should be tested independently from the application core.

Recommended tests include:

- manifest validation
- compatibility verification
- schema validation
- registry integration
- authorization
- API compatibility

Core platform tests and plugin tests should remain separate.

---

# Future Extensions

The Plugin System supports future capabilities including:

- signed plugins
- plugin marketplaces
- tenant-specific plugins
- hot-reloadable plugins
- dependency graphs
- plugin sandboxing
- plugin health monitoring
- remote plugin repositories

These enhancements can be introduced without changing the existing plugin architecture.

---

# Relationship to Other Concepts

The Plugin System integrates closely with:

- [[Schema-Driven Architecture]]
- [[Configuration]]
- [[Versioning]]
- [[Dynamic-UI]]
- [[Configuration Revisions]]

---

# Related Documentation

## Concepts

- [[Dynamic-UI]]
- [[Schema-Driven Architecture]]
- [[Configuration]]
- [[Runtime Configuration]]
- [[Versioning]]

---

## Architecture

- [[Extension-Points]]
- [[Manifest-System]]
- [[Registry-Architecture]]
- [[Configuration-Architecture]]
- [[Contract-Versioning]]

---

## Backend

- [[Model-Registry]]
- [[Tool-Registry]]
- [[Configuration]]
- [[Bootstrap]]
- [[Security]]

---

## Frontend

- [[Component-Registry]]
- [[Action-Registry]]
- [[Schema-Renderer]]
- [[UI-Schema]]

---

# Summary

The Plugin System enables Kernschmied to be extended through independently developed modules while preserving stable contracts, strict security boundaries, and architectural consistency. Plugins contribute functionality through manifests, schemas, and documented extension points rather than modifying the application core.

By combining manifest-driven discovery, registry-based integration, version compatibility checks, backend-controlled authorization, schema validation, and provider-independent extension mechanisms, the Plugin System provides a scalable foundation for evolving the platform without sacrificing maintainability, security, or long-term compatibility.

---

Back to [[Home]].
