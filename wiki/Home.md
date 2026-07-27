# Kernschmied Wiki

> **Version:** 1.0  
> **Status:** Living Documentation  
> **Repository:** https://github.com/Thomas-Heisig/Kernschmied

---

# Welcome to the Kernschmied Wiki

Welcome to the official documentation of **Kernschmied**.

Kernschmied is a **modular, schema-driven AI platform** built with **Python**, **FastAPI**, **React**, and **TypeScript**. It is designed to run locally while providing a solid architectural foundation for deployment in intranet and internet environments without requiring fundamental redesigns.

The project emphasizes:

- Long-term maintainability
- Stable public contracts
- Dynamic business logic
- Secure-by-default architecture
- Extensibility through registries and manifests
- Generic frontend rendering
- Versioned schemas
- Modern software engineering practices

This wiki serves as the central source of truth for developers, contributors, and future maintainers.

---

# Project Vision

Kernschmied is more than a chat application.

It is intended to become a flexible platform for AI-assisted business applications that can be adapted to many different domains without changing the underlying architecture.

The guiding principle is:

> **Dynamic business logic, stable contracts, strict security boundaries and versioned schemas.**

---

# Technology Stack

## Backend

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy Async
- Alembic
- SQLite (default)
- PostgreSQL (planned)
- Server-Sent Events (SSE)

---

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS

---

## Development

- Git
- GitHub
- VS Code
- pytest
- ESLint
- Ruff
- Pyright

---

# Documentation Structure

## Getting Started

For new developers.

- [[Getting-Started]]
- [[Installation]]

---

## Architecture

Core architecture and design decisions.

- [[Architecture]]
- [[Project-Principles]]

---

## Backend

Backend implementation details.

- [[Backend-Overview]]
- [[Bootstrap]]
- [[Configuration]]
- [[Contracts]]
- [[Hierarchy]]
- [[Chat]]
- [[Model-Registry]]
- [[Tool-Registry]]
- [[Security]]
- [[Error-Handling]]
- [[Database]]
- [[Dependency-Injection]]

---

## Frontend

Frontend architecture.

- [[Frontend-Overview]]
- [[Schema-Renderer]]
- [[Generic-Tree]]
- [[Component-Registry]]
- [[Action-Registry]]
- [[State-Management]]
- [[API-Client]]
- [[Streaming]]
- [[Forms]]
- [[UI-Schema]]

---

## API

REST and streaming interfaces.

- [[Bootstrap]]
- [[Hierarchy]]
- [[UI-Schema]]
- [[Chat]]
- [[Models]]
- [[Tools]]
- [[Configuration]]
- [[Errors]]
- [[SSE]]

---

## Concepts

Core architectural concepts.

- [[Dynamic-UI]]
- [[Runtime-Configuration]]
- [[Configuration-Revisions]]
- [[Prompt-Inheritance]]
- [[Plugin-System]]
- [[Schema-Versioning]]

---

## Deployment

Deployment profiles.

- [[Development]]
- [[Intranet]]
- [[Internet]]

---

## Development

Guidelines for contributors.

- [[Coding-Guidelines]]
- [[Testing]]
- [[Release-Process]]
- [[Roadmap]]
- [[TODO]]

---

## Architecture Decision Records (ADR)

Design decisions are documented as ADRs.

- [[ADR-0001-Schema-Driven-UI]]
- [[ADR-0002-Bootstrap]]
- [[ADR-0003-Registries]]
- [[ADR-0004-Security-Profiles]]
- [[ADR-0005-Versioned-Contracts]]

---

# Core Principles

Kernschmied follows a small number of strict architectural rules:

- Stable public contracts
- Schema-driven frontend
- Generic UI components
- Explicit registration
- Backend authority
- Runtime validation
- Versioned schemas
- Security by default
- Dependency injection
- Configuration stored in the database

For more details see:

→ [[Project-Principles]]

---

# Development Workflow

Typical workflow:

1. Pull the latest changes.
2. Create a feature branch.
3. Implement the feature.
4. Add tests.
5. Update the documentation.
6. Create a Pull Request.
7. Perform code review.
8. Merge after approval.

---

# Repository

GitHub Repository:

https://github.com/Thomas-Heisig/Kernschmied

Issue Tracker:

https://github.com/Thomas-Heisig/Kernschmied/issues

Discussions:

https://github.com/Thomas-Heisig/Kernschmied/discussions *(optional)*

---

# Contributing

If you want to contribute to Kernschmied, please read:

- `CONTRIBUTING.md`
- [[Coding-Guidelines]]
- [[Testing]]

---

# Documentation Philosophy

Documentation is considered part of the product.

Every significant architectural decision should be documented.

Documentation should evolve together with the implementation.

Outdated documentation should be corrected as soon as possible.

---

# Roadmap

The long-term roadmap includes:

- Generic hierarchy
- Dynamic UI schemas
- AI model registry
- Tool registry
- Plugin ecosystem
- Multi-provider AI support
- Enterprise deployment
- Advanced security profiles
- Configuration revisions
- Audit logging
- Modular administration

For details see:

→ [[Roadmap]]

---

# Need Help?

Useful pages:

- [[FAQ]]
- [[Glossary]]
- [[Installation]]
- [[Getting-Started]]

---

# License

See the repository `LICENSE` file for licensing information.

---

**Welcome to Kernschmied — build once, extend forever.**