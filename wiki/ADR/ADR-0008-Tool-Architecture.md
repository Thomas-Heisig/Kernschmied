# ADR-0008: Tool Architecture and Execution

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

One of the primary goals of Kernschmied is to build an AI platform that can safely interact with external systems.

Large Language Models should not contain business logic or direct infrastructure access.

Instead, models interact with the outside world through explicitly defined **Tools**.

Examples include:

- Calculator
- File System
- Database
- Email
- OCR
- Web Search
- Calendar
- ERP Integration
- Document Generation
- Future Plugins

Every tool must behave predictably, be independently testable, and integrate into the platform without modifying the application core.

---

# Problem

Without a structured tool architecture, AI integrations typically evolve into tightly coupled code where:

- prompts call arbitrary functions
- business logic becomes embedded inside tools
- tools bypass security
- different providers expose different interfaces
- adding a new tool requires modifying the application core

This leads to:

- inconsistent APIs
- duplicated validation
- difficult testing
- security risks
- poor maintainability

---

# Decision

Kernschmied adopts a **registry-based tool architecture**.

Every tool:

- implements a common contract
- is registered through the Tool Registry
- is described by a manifest (`tool.json`)
- validates its input and output
- executes through a centralized execution pipeline
- is authorized before execution

Models never execute Python code directly.

They request tool execution through a structured Tool Call contract.

---

# Architectural Principle

> Models request capabilities.
>
> The platform decides whether and how those capabilities are executed.

---

# High-Level Architecture

```text
LLM

        │

        ▼

Tool Call

        │

        ▼

Tool Registry

        │

        ▼

Permission Check

        │

        ▼

Input Validation

        │

        ▼

Tool Execution

        │

        ▼

Output Validation

        │

        ▼

Structured Result
```

---

# Goals

The Tool Architecture should provide:

- Explicit registration
- Stable contracts
- Provider independence
- Security
- Validation
- Testability
- Extensibility
- Runtime discovery

---

# Tool Lifecycle

Every tool follows the same lifecycle.

```text
Application Startup

↓

Discover Manifest

↓

Validate Manifest

↓

Register Tool

↓

Registry Ready

↓

Execute on Demand
```

---

# Tool Definition

Every tool implements the common tool interface.

Typical responsibilities include:

- metadata
- input schema
- output schema
- execution
- validation

Business services remain outside the tool itself.

---

# Tool Manifest

Each tool provides a declarative manifest.

Example:

```text
tool.json
```

The manifest typically contains:

- identifier
- name
- version
- description
- capabilities
- category
- permissions
- input schema
- output schema

The manifest is validated before registration.

---

# Why Manifests?

Manifests allow the platform to:

- discover tools
- validate compatibility
- expose metadata
- build administration interfaces
- generate documentation

without executing tool code.

---

# Tool Registry

The Tool Registry is responsible for:

- discovery
- registration
- lookup
- validation
- metadata
- health information

Business services interact with the registry rather than individual tools.

---

# Tool Factory Registry

Tool construction is delegated to the Tool Factory Registry.

Responsibilities include:

- dependency injection
- lifecycle management
- provider-specific initialization
- singleton management where appropriate

Tool instances should never be created manually.

---

# Execution Pipeline

Tool execution follows a deterministic process.

```text
Tool Call

↓

Lookup

↓

Permission Check

↓

Input Validation

↓

Create Tool Instance

↓

Execute

↓

Output Validation

↓

Return Result
```

Every step is mandatory.

---

# Tool Calls

Models never execute tools directly.

Instead they emit structured tool calls.

Example:

```json
{
  "tool": "calculator",
  "arguments": {
    "expression": "2 + 2"
  }
}
```

The backend validates the request before execution.

---

# Input Validation

Every tool defines a structured input schema.

Validation should verify:

- required properties
- data types
- ranges
- formats
- business constraints where appropriate

Invalid requests are rejected before execution.

---

# Output Validation

Tool responses are validated before being returned to the model.

Benefits include:

- predictable contracts
- safer prompting
- easier testing
- provider independence

---

# Tool Categories

Typical categories include:

## Utility

- calculator
- datetime
- uuid

---

## Files

- read file
- write file
- search files

---

## Documents

- PDF
- DOCX
- Markdown
- Spreadsheet

---

## Communication

- email
- calendar
- notifications

---

## AI

- OCR
- embeddings
- speech
- translation

---

## Business

- ERP
- CRM
- inventory
- invoices

---

## Plugins

Future plugins may introduce additional categories.

---

# Permission Model

Tool execution is always authorized.

Permission checks may consider:

- user
- deployment profile
- workspace
- hierarchy node
- tool category
- runtime configuration

Authorization remains backend responsibility.

---

# User Confirmation

Some tools require explicit confirmation.

Examples include:

- deleting files
- sending emails
- modifying databases
- executing external actions

Typical workflow:

```text
Tool Call

↓

Confirmation Required

↓

User Approves

↓

Execute
```

---

# Tool Isolation

Tools should remain isolated.

A tool should not:

- access unrelated services
- modify global state
- bypass the registry
- call another tool directly

Cross-tool coordination belongs to application services.

---

# Error Handling

Tools return structured errors.

Example:

```json
{
  "success": false,
  "error": {
    "code": "file_not_found",
    "message": "The requested file does not exist."
  }
}
```

Unexpected exceptions are converted into structured platform errors.

---

# Security Considerations

Tools represent one of the largest attack surfaces within the platform.

Therefore:

- every tool must be registered explicitly
- manifests are validated
- inputs are validated
- outputs are validated
- permissions are enforced
- execution is audited
- deny-by-default applies

Models never execute arbitrary Python code.

---

# Performance Considerations

The architecture supports:

- lazy initialization
- dependency injection
- asynchronous execution
- metadata caching
- registry lookup caching

Tools should perform only the work necessary for the requested operation.

---

# Dynamic Discovery

During startup the registry discovers tool manifests.

```text
Tool Directory

↓

tool.json

↓

Validation

↓

Registration
```

Unknown or invalid manifests are rejected.

Discovery never implies automatic trust.

---

# Provider Independence

The tool interface is independent from any specific LLM provider.

Whether the model originates from:

- Ollama
- OpenAI
- llama.cpp
- Anthropic
- Gemini

the execution pipeline remains identical.

---

# Operational Impact

The architecture enables:

- runtime tool discovery
- administrative inspection
- health monitoring
- capability reporting
- audit logging

Operations teams can determine exactly which tools are installed and available.

---

# Consequences

## Positive

- Strong separation of concerns
- Provider independence
- Stable execution contracts
- Safer AI interactions
- Runtime discovery
- Easy extensibility
- Centralized validation

## Negative

- Additional infrastructure
- Manifest maintenance
- Registry complexity
- Validation overhead

---

# Alternatives Considered

## Direct Function Calls

Models invoke Python functions directly.

Rejected due to:

- poor security
- tight coupling
- difficult validation

---

## Dynamic Code Execution

Loading arbitrary Python modules at runtime.

Rejected because it violates the platform's security principles.

---

## Provider-Specific Tool APIs

Each provider implements its own execution model.

Rejected because it fragments the architecture and complicates maintenance.

---

# Risks

Potential risks include:

- unsafe tools
- incorrect manifests
- insufficient validation
- permission bypass
- overly powerful tools

Mitigation includes:

- registry validation
- dependency injection
- deny-by-default
- audit logging
- automated testing
- security reviews

---

# Implementation Notes

The implementation should provide:

- BaseTool interface
- Tool Registry
- Tool Factory Registry
- tool.json manifests
- Pydantic input/output schemas
- dependency injection
- structured execution pipeline
- permission checks
- audit logging

Tool execution should always remain deterministic and observable.

---

# Related Decisions

- [[ADR-0003-Registries]]
- [[ADR-0004-Security-Profiles]]
- [[ADR-0005-Versioned-Contracts]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Registry-Architecture]]
- [[Manifest-System]]

---

## Backend

- [[Tool-Registry]]
- [[Model-Registry]]
- [[Configuration]]
- [[Security]]

---

## Frontend

- [[API-Client]]

---

## Concepts

- [[Plugin-System]]
- [[Dependency-Injection]]
- [[Tool-Manifests]]
- [[Runtime-Configuration]]

---

# Decision Summary

Kernschmied adopts a **registry-based tool architecture** in which every tool is defined through a common contract, described by a validated `tool.json` manifest, registered explicitly, and executed through a centralized validation and authorization pipeline.

Large Language Models never execute code directly. Instead, they emit structured tool calls that are validated, authorized, executed, and audited by the platform.

This architecture provides provider independence, strong security guarantees, extensibility, deterministic behavior, and a maintainable foundation for integrating built-in capabilities as well as future plugins.

---

Back to [[Home]].
