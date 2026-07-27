# C4 Container Architecture

The **C4 Container Diagram** describes the major executable containers that make up the Kernschmied platform and the relationships between them.

Within the C4 model, a **container** is an independently deployable or executable unit such as a web application, backend service, database, or external system.

Kernschmied intentionally consists of a small number of clearly separated containers with well-defined responsibilities and stable contracts.

---

# Goals

The container architecture is designed to provide:

- Clear separation of responsibilities
- Stable service boundaries
- Provider independence
- Modular implementation
- Schema-driven frontend
- Centralized security
- Future scalability
- Technology independence where appropriate

---

# C4 Model Overview

The C4 model describes software architecture on four levels:

| Level | Description |
|--------|-------------|
| Level 1 | System Context |
| **Level 2** | **Container Diagram** |
| Level 3 | Component Diagram |
| Level 4 | Code |

This document focuses on **Level 2 – Containers**.

---

# High-Level Container Diagram

```text
                    +----------------------+
                    |      Web Browser     |
                    |  React / TypeScript  |
                    +----------+-----------+
                               |
                     HTTPS / REST / SSE
                               |
                               v
+-----------------------------------------------------------+
|                   FastAPI Backend                         |
|-----------------------------------------------------------|
| Bootstrap API                                             |
| Chat API                                                  |
| Configuration API                                         |
| Hierarchy API                                             |
| UI Schema API                                             |
| Models API                                                |
| Tools API                                                 |
+-------------+-----------------------------+---------------+
              |                             |
              |                             |
              v                             v
     +------------------+          +------------------+
     |  SQLite /        |          |  LLM Providers   |
     | PostgreSQL       |          |------------------|
     |                  |          | Ollama           |
     | Configuration    |          | OpenAI           |
     | Hierarchy        |          | Anthropic        |
     | Chat Data        |          | Gemini           |
     +------------------+          | llama.cpp        |
                                   +------------------+
```

---

# Container Responsibilities

The platform currently consists of four primary containers:

| Container | Responsibility |
|-----------|----------------|
| Frontend | User Interface |
| Backend | Business Logic |
| Database | Persistent Storage |
| LLM Providers | AI Model Execution |

Each container owns a clearly defined set of responsibilities.

---

# Frontend Container

Technology:

- React
- TypeScript
- Vite
- Tailwind CSS

Responsibilities:

- Render UI
- Schema interpretation
- Form rendering
- Tree rendering
- Chat interface
- Streaming
- User interaction

The frontend never contains business rules.

---

# Frontend Internal Modules

```text
Frontend

├── Bootstrap Client

├── API Client

├── Schema Renderer

├── Generic Tree

├── Component Registry

├── Action Registry

├── Chat View

└── State Management
```

Each module communicates exclusively through stable frontend contracts.

---

# Backend Container

Technology:

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy Async

Responsibilities:

- REST APIs
- SSE Streaming
- Authentication
- Authorization
- Configuration
- Registry management
- Prompt inheritance
- Tool execution
- Provider abstraction

The backend is the authoritative source of truth.

---

# Backend Layers

```text
REST API

↓

Application Services

↓

Registries

↓

Configuration Resolver

↓

Repositories

↓

Database / Providers
```

Dependencies always point downward.

---

# Database Container

Supported databases:

- SQLite (default)
- PostgreSQL (production)

Responsibilities:

- configuration
- hierarchy
- chats
- audit log
- revisions
- metadata

Business logic is intentionally excluded from the database.

---

# LLM Provider Container

The provider layer is abstracted through the Provider Registry.

Possible providers include:

- Ollama
- llama.cpp
- OpenAI
- Anthropic
- Gemini
- Azure OpenAI

The frontend is unaware of provider-specific implementations.

---

# Backend ↔ Database

Communication:

```text
SQLAlchemy Async

↓

Repositories

↓

Database
```

Repositories encapsulate all persistence logic.

---

# Backend ↔ LLM Providers

Communication:

```text
Chat Service

↓

Model Registry

↓

Provider Registry

↓

BaseModelBackend

↓

Provider
```

Provider-specific APIs never reach business services.

---

# Frontend ↔ Backend

Communication occurs exclusively through:

- REST
- Server-Sent Events (SSE)

No direct database access exists.

---

# Communication Matrix

| Source | Destination | Protocol |
|----------|-------------|----------|
| Frontend | Backend | HTTPS |
| Frontend | Backend | REST |
| Frontend | Backend | SSE |
| Backend | Database | SQLAlchemy |
| Backend | Providers | HTTP / SDK |
| Backend | Filesystem | Internal |

All communication is initiated through the backend.

---

# Container Boundaries

Each container owns its own responsibility.

## Frontend

Owns:

- presentation
- rendering
- user interaction

Does **not** own:

- business rules
- permissions
- persistence

---

## Backend

Owns:

- application logic
- validation
- authorization
- orchestration

Does **not** own:

- rendering
- browser state

---

## Database

Owns:

- persistent storage

Does **not** own:

- application logic
- authorization

---

## Providers

Own:

- inference
- embeddings
- model execution

Do **not** own:

- permissions
- hierarchy
- configuration

---

# Startup Sequence

```text
Backend

↓

Database

↓

Configuration

↓

Registries

↓

Server Ready

↓

Frontend

↓

Bootstrap

↓

Load Resources

↓

Ready
```

The backend is always initialized before the frontend.

---

# Request Flow

Typical request:

```text
User

↓

Frontend

↓

REST API

↓

Service Layer

↓

Repositories

↓

Database

↓

Response
```

Streaming requests additionally involve the Provider Layer.

---

# Streaming Flow

```text
Frontend

↓

Chat API

↓

Model Registry

↓

Provider

↓

SSE Stream

↓

Frontend
```

The streaming contract remains provider-independent.

---

# Security Boundaries

Security is enforced entirely by the backend.

```text
Frontend

↓

Authentication

↓

Authorization

↓

Business Services
```

The frontend never decides access rights.

---

# Deployment

Typical deployment:

```text
Browser

↓

HTTPS

↓

FastAPI

↓

SQLite/PostgreSQL

↓

LLM Providers
```

All containers may execute on one machine during development.

Production deployments may distribute containers independently.

---

# Scalability

The architecture allows independent scaling of:

- frontend
- backend
- providers
- database

Scaling strategies remain independent of business logic.

---

# Failure Isolation

Container boundaries isolate failures.

Examples:

Provider unavailable:

```text
Provider

↓

Error

↓

Backend

↓

Structured Error

↓

Frontend
```

Database failures do not affect frontend rendering logic directly.

---

# Technology Independence

The architecture intentionally isolates technologies.

Possible replacements include:

| Current | Future |
|----------|---------|
| React | Another SPA Framework |
| SQLite | PostgreSQL |
| Ollama | Another Provider |
| FastAPI | Alternative HTTP Framework (if contracts remain stable) |

Stable contracts minimize migration effort.

---

# Relationship to the C4 System Context

The **System Context Diagram** identifies:

> External actors and systems.

The **Container Diagram** identifies:

> Executable applications and services.

Together they describe the platform from the outside inward.

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[System-Context]]
- [[Request-Lifecycle]]
- [[Registry-Architecture]]
- [[Repository-Structure]]
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

---

## ADRs

- [[ADR-0002-Bootstrap]]
- [[ADR-0003-Registries]]
- [[ADR-0008-Tool-Architecture]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

# Summary

The C4 Container Architecture describes the major executable building blocks of the Kernschmied platform and the stable communication paths between them.

By separating the schema-driven frontend, the FastAPI backend, persistent storage, and provider-independent AI model backends into clearly defined containers, the platform achieves modularity, maintainability, scalability, and long-term architectural flexibility while preserving stable public contracts and strong security boundaries.

---

Back to [[Home]].
