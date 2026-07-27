# Development Deployment

The **Development** deployment profile is intended for local development, experimentation, testing, and feature implementation. It prioritizes developer productivity while preserving the same architectural principles used in production environments.

Unlike many applications that maintain completely separate development architectures, Kernschmied uses the same core runtime in every deployment profile. The Development profile simply relaxes selected operational requirements while maintaining identical public contracts, APIs, schemas, registries, and configuration systems.

This allows developers to build and test features under realistic conditions without introducing environment-specific behavior.

---

# Goals

The Development profile is designed to provide:

- Fast local development
- Minimal setup
- Rapid iteration
- Full platform functionality
- Consistent architecture
- Easy debugging
- Predictable behavior
- Smooth transition to production

---

# Design Philosophy

Development should simplify operations—not change application behavior.

```text
Application Core
        │
        ▼
Deployment Profile
        │
        ▼
Development Rules
```

Business logic, APIs, schemas, and contracts remain identical across all deployment profiles.

---

# Profile Characteristics

The Development profile typically includes:

- Local execution
- Single developer environment
- Local database
- Local AI models
- Simplified authentication
- Relaxed security policies
- Verbose logging
- Debugging support

The profile is optimized for developer productivity rather than operational security.

---

# High-Level Architecture

```text
Developer

        │

        ▼

React Frontend

        │

        ▼

FastAPI Backend

        │

        ▼

SQLite Database

        │

        ▼

Local AI Providers
```

All components usually execute on the same workstation.

---

# Typical Environment

A standard development installation may include:

- Windows
- Linux
- macOS
- Python
- FastAPI
- React
- Node.js
- SQLite
- Ollama
- Git

The exact operating system is not significant because the architecture remains platform-independent.

---

# Bootstrap

During startup, the backend initializes all core subsystems.

Typical bootstrap tasks include:

- loading environment variables
- selecting the deployment profile
- initializing the database
- loading configuration
- registering models
- registering tools
- initializing caches
- exposing API endpoints

The bootstrap sequence is identical across all deployment profiles.

---

# Local Database

SQLite is the recommended database for development.

```text
Application

↓

SQLite

↓

Configuration

↓

Hierarchy

↓

Runtime Data
```

The database can later be replaced by PostgreSQL without architectural changes.

---

# Runtime Configuration

Development uses the same Runtime Configuration system as every other profile.

Business settings remain database-driven.

Examples include:

- models
- prompts
- hierarchy
- UI schemas
- feature flags
- tools

Developers test the same configuration system that production uses.

---

# Environment Variables

Environment variables contain only infrastructure settings.

Typical examples include:

- deployment profile
- database connection
- logging configuration
- bootstrap secrets
- network settings

Business configuration does not belong in environment variables.

---

# Local AI Providers

Development commonly uses local AI providers.

Examples include:

- Ollama
- llama.cpp
- Transformers

The Model Registry abstracts provider differences.

```text
Chat Request

↓

Model Registry

↓

Provider

↓

Model
```

Switching providers does not affect the application architecture.

---

# Frontend Development

The frontend is typically executed using the Vite development server.

```text
Developer

↓

React

↓

Hot Reload

↓

Updated UI
```

This enables rapid user interface iteration.

---

# Backend Development

FastAPI is commonly started with automatic reload enabled.

```text
Code Change

↓

Backend Reload

↓

Updated API
```

Reloading affects only the development environment.

---

# Logging

Development favors detailed logging.

Typical information includes:

- bootstrap progress
- request processing
- registry initialization
- configuration resolution
- validation
- structured errors

Verbose logging simplifies debugging.

---

# Debugging

The Development profile supports debugging through standard development tools.

Typical workflows include:

- IDE debugging
- breakpoints
- request inspection
- API testing
- browser developer tools
- database inspection

Debugging facilities are not part of the production runtime.

---

# Authentication

Development may use simplified authentication.

Examples include:

- local developer identity
- mock users
- test accounts

This accelerates feature development while preserving the authorization architecture.

---

# Authorization

Although authentication may be simplified, authorization continues to use the same backend logic.

```text
Request

↓

Authorization

↓

Business Operation
```

Authorization should never be bypassed simply because the application runs locally.

---

# Security

The Development profile intentionally relaxes selected operational restrictions.

Examples may include:

- simplified login
- local origins
- verbose errors
- debug endpoints

However, the following principles remain unchanged:

- server-side validation
- authorization
- schema validation
- contract validation
- structured errors

The architecture itself remains secure.

---

# API Contracts

Development exposes the same APIs as every other deployment profile.

Examples include:

- Bootstrap
- Configuration
- Chat
- Hierarchy
- Models
- Tools
- UI Schema

No development-specific API contracts exist.

---

# Schema Validation

All schemas continue to be validated.

Examples include:

- configuration schemas
- manifests
- UI schemas
- API payloads

Development never disables schema validation.

---

# Plugin Development

The Development profile is the preferred environment for plugin authors.

Typical workflow:

```text
Create Plugin

↓

Validate Manifest

↓

Register Plugin

↓

Test

↓

Iterate
```

Plugins are validated using the same rules as production.

---

# Registry Initialization

During startup, registries discover available extensions.

Examples include:

- Model Registry
- Tool Registry
- Plugin Registry
- Component Registry
- Action Registry

Development uses identical registration logic.

---

# Caching

Caching remains active during development.

Configuration revisions invalidate caches automatically.

```text
Configuration Updated

↓

Revision++

↓

Cache Reload
```

Developers therefore test real runtime behavior.

---

# Error Handling

Structured error responses remain enabled.

Example structure:

```text
code

message

details

request_id
```

Development may include additional diagnostic information.

---

# Testing

The Development profile supports all testing activities.

Examples include:

- unit testing
- integration testing
- API testing
- frontend testing
- schema validation
- registry validation

Testing should reflect production behavior as closely as possible.

---

# Typical Workflow

```text
Modify Source Code

↓

Run Application

↓

Test Feature

↓

Update Configuration

↓

Validate Behavior

↓

Commit Changes
```

The workflow emphasizes short feedback cycles.

---

# Differences from Production

Compared to Internet deployments, Development typically provides:

| Feature | Development |
|----------|-------------|
| HTTPS | Optional |
| Authentication | Simplified |
| Logging | Verbose |
| Debug Endpoints | Enabled |
| Local Models | Common |
| SQLite | Recommended |
| Automatic Reload | Enabled |

Despite these operational differences, application contracts remain identical.

---

# Future Extensions

The Development profile supports future enhancements including:

- integrated developer dashboard
- live registry inspection
- configuration editor
- schema visualization
- prompt diagnostics
- performance profiling
- plugin debugging tools

These capabilities improve development without affecting production deployments.

---

# Relationship to Other Deployment Profiles

Development shares the same architecture with:

- [[Intranet]]
- [[Internet]]

Only operational policies differ.

---

# Related Documentation

## Deployment

- [[Deployment Overview]]
- [[Intranet]]
- [[Internet]]

---

## Architecture

- [[Bootstrap-Lifecycle]]
- [[Configuration-Architecture]]
- [[Registry-Architecture]]
- [[Security-Architecture]]

---

## Backend

- [[Bootstrap]]
- [[Configuration]]
- [[Security]]
- [[Model-Registry]]
- [[Tool-Registry]]

---

## Concepts

- [[Runtime Configuration]]
- [[Dynamic-UI]]
- [[Plugin-System]]
- [[Schema Versioning]]

---

# Summary

The Development deployment profile provides a productive local environment for building and testing Kernschmied while preserving the same architecture, contracts, schemas, registries, and runtime behavior used in production. Rather than introducing a separate development architecture, it relaxes only selected operational requirements such as authentication and logging.

By combining local execution, runtime configuration, schema validation, provider-independent registries, structured APIs, and identical backend behavior across all deployment profiles, the Development profile enables rapid iteration without sacrificing architectural consistency or long-term maintainability.

---

Back to [[Home]].
