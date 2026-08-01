# Frequently Asked Questions (FAQ)

> **Version:** 1.0  
> **Status:** Living Document

---

# Introduction

This page answers the most common questions about **Kernschmied**.

If your question is not answered here, please open a GitHub Issue or Discussion.

Repository:

<https://github.com/Thomas-Heisig/Kernschmied>

---

# General

## What is Kernschmied?

Kernschmied is a modular, schema-driven AI platform designed for long-term maintainability and extensibility.

Instead of hardcoding business logic into the frontend, the backend provides schemas describing:

- forms
- layouts
- hierarchy
- actions
- permissions
- configuration

The frontend renders these schemas using generic components.

---

## Why was Kernschmied created?

Many AI applications become difficult to maintain because business logic, UI, configuration and infrastructure become tightly coupled.

Kernschmied separates these concerns to enable:

- stable APIs
- reusable components
- configurable business logic
- long-term evolution
- secure deployment

---

## Is Kernschmied only a chat application?

No.

The chat interface is only one feature.

The architecture is intended to support many future applications, including:

- knowledge management
- document generation
- workflow automation
- configurable administration
- AI-assisted business processes
- plugin-based extensions

---

# Architecture

## Why is the frontend schema-driven?

A schema-driven frontend allows new business functionality to be introduced without rewriting the user interface.

The backend defines **what** should be displayed.

The frontend decides **how** to render it using generic components.

See:

- [[Schema-Renderer]]
- [[UI-Schema]]

---

## Why are there no business-specific React components?

Business-specific components increase coupling and reduce maintainability.

Instead of components such as:

- CustomerTree
- ProjectNode
- InvoicePanel

Kernschmied uses generic components such as:

- TreeNode
- FormRenderer
- PropertyGrid
- ListRenderer

---

## Why are contracts so important?

Public contracts define how different parts of the system communicate.

Stable contracts allow the internal implementation to evolve without breaking clients.

Examples include:

- REST responses
- request models
- SSE events
- UI schemas
- manifests

---

## Why are schemas versioned?

Versioning allows the project to evolve while remaining compatible with older clients.

Breaking changes require a new schema version.

---

# Configuration

## Why is business configuration stored in the database?

Business settings change frequently.

Examples include:

- prompts
- hierarchy
- model assignments
- tool assignments
- UI configuration

Storing them in the database allows runtime changes without modifying the application code.

---

## What belongs in the `.env` file?

Only infrastructure and bootstrap settings.

Examples:

- database connection
- secret keys
- deployment profile
- ports
- hosts

Business configuration should never be stored in `.env`.

---

# Frontend

## Can I create custom React pages?

Generally, no.

New functionality should be implemented through:

- schemas
- registries
- generic components

Only infrastructure-level UI should be hardcoded.

---

## What happens if the backend sends an unknown component?

The frontend should display the component as **unsupported**.

Unknown components must never be executed automatically.

---

## Can the frontend authorize actions?

No.

Authorization is always performed by the backend.

---

# Backend

## Why does the backend generate UI schemas?

Because the backend knows:

- permissions
- validation
- configuration
- hierarchy
- business rules

The frontend only renders what the backend describes.

---

## Why use FastAPI?

FastAPI provides:

- automatic validation
- dependency injection
- OpenAPI generation
- high performance
- excellent developer experience

---

## Why use Pydantic v2?

Pydantic provides:

- strong validation
- typed models
- serialization
- schema generation

---

# Registries

## What is a registry?

A registry is a controlled list of available resources.

Examples:

- Model Registry
- Tool Registry
- Component Registry
- Action Registry

Registries prevent unknown resources from being executed automatically.

---

## Why must resources be explicitly registered?

Discovery does not imply permission.

A plugin, model or tool may exist but still require explicit approval before use.

---

# Plugins

## Does Kernschmied support plugins?

Yes.

Plugins are designed to be:

- discoverable
- validated
- configurable
- explicitly enabled

Plugins must never bypass security boundaries.

---

## Can plugins execute arbitrary Python code?

No.

Plugins operate within defined interfaces and security constraints.

Dynamic discovery does not mean unrestricted execution.

---

# AI Models

## Can multiple AI providers be used?

Yes.

The architecture supports multiple providers through a common abstraction.

Examples include:

- local models
- cloud providers
- future integrations

---

## Are models configured in code?

No.

Models are described by manifests and managed through the Model Registry.

---

# Security

## Why is the backend authoritative?

The backend is the only trusted source for:

- validation
- authorization
- persistence
- business logic

The frontend is considered an untrusted client.

---

## Why are unknown schemas rejected?

Rejecting unknown schemas prevents:

- undefined behavior
- security risks
- accidental execution
- inconsistent UI rendering

---

## Why are there different deployment profiles?

Different environments require different security levels.

Profiles include:

- Development
- Intranet
- Internet

Each profile enforces a minimum security baseline.

---

# Development

## How should I contribute?

Please read:

- `CONTRIBUTING.md`
- [[Coding-Guidelines]]
- [[Testing]]

---

## Do I need to update the documentation?

Yes.

Documentation is part of the project.

Architectural or functional changes should be reflected in the documentation.

---

## Are automated tests required?

Yes.

Every significant feature should include appropriate automated tests.

Preferred order:

1. Unit tests
2. Integration tests
3. API tests
4. Frontend tests

---

# Documentation

## Where should I start reading?

Recommended order:

1. [[Getting-Started]]
2. [[Project-Principles]]
3. [[Architecture]]
4. [[Backend-Overview]]
5. [[Frontend-Overview]]

---

## Where are architecture decisions documented?

Architecture decisions are documented as ADRs.

Examples:

- [[ADR-0001-Schema-Driven-UI]]
- [[ADR-0002-Bootstrap]]
- [[ADR-0003-Registries]]
- [[ADR-0004-Security-Profiles]]
- [[ADR-0005-Versioned-Contracts]]

---

# Repository

## Where can I report bugs?

GitHub Issues:

<https://github.com/Thomas-Heisig/Kernschmied/issues>

---

## Where can I discuss ideas?

Please use the Issue tracker on GitHub to discuss ideas:

<https://github.com/Thomas-Heisig/Kernschmied/issues>

---

## Where can I contribute?

Repository:

<https://github.com/Thomas-Heisig/Kernschmied>

---

# Related Pages

- [[Home]]
- [[Getting-Started]]
- [[Installation]]
- [[Project-Principles]]
- [[Architecture]]
- [[Glossary]]
- [[Backend-Overview]]
- [[Frontend-Overview]]
- [[Security]]
- [[Testing]]

---

## Still have questions?

If your question is not covered here:

1. Search the existing GitHub Issues.
2. Check the project documentation.
3. Open a new GitHub Issue or Discussion.
4. Provide as much context as possible, including logs, screenshots and reproduction steps.

---

Zurück zu [[Home]].
