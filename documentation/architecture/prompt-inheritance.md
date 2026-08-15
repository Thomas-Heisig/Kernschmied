{COPY_FROM: documentation/unknown/prompt-inheritance.md}
# Prompt Inheritance

The **Prompt Inheritance** architecture defines how prompts are composed from multiple hierarchical sources to produce the final prompt that is sent to an AI model.

Unlike traditional AI applications that use a single static system prompt, Kernschmied constructs prompts dynamically from multiple configuration scopes. This enables reusable organizational context, project-specific behavior, user preferences, and request-specific instructions while preserving deterministic and reproducible prompt generation.

Prompt inheritance is tightly integrated with the **Hierarchy Architecture** and the **Configuration Architecture**, making conversational behavior configurable without changing application code.

---

## Goals

The Prompt Inheritance architecture is designed to provide:

- Reusable prompt definitions
- Deterministic prompt generation
- Hierarchical context inheritance
- Configuration-driven customization
- Stable runtime behavior
- Fine-grained overrides
- Provider independence
- Auditable prompt construction

---

## Design Principles

The prompt subsystem follows several architectural principles.

## Prompts are Configuration

Prompts are treated as structured runtime configuration rather than source code.

Prompt definitions are:

- versioned
- validated
- inherited
- auditable
- cacheable

This allows administrators to modify conversational behavior without redeploying the application.

---

## Deterministic Composition

Given the same hierarchy, configuration, and request, prompt generation always produces the same result.

```text
Same Input

↓

Prompt Resolver

↓

Same Prompt

```

This deterministic behavior simplifies debugging and reproducibility.

---

## Layered Context

Rather than replacing prompts, each hierarchy level contributes additional context.

```text
Global Context

↓

Department Context

↓

Project Context

↓

Conversation Context

↓

Request Context

```

The final prompt is assembled from these layers according to defined merge rules.

---

## Prompt Resolution Pipeline

The Prompt Resolver is responsible for building the final prompt.

```text
Request

↓

Hierarchy Resolution

↓

Configuration Resolution

↓

Prompt Resolution

↓

Model Backend

```

Declarative prompt fragments are assembled only by the Prompt Resolver. The
Chat Service may append authorized conversation context as a separate,
non-instructional data section after prompt resolution.

---

## Prompt Sources

Prompts may originate from multiple scopes.

| Scope        | Typical Purpose             |
| ------------ | --------------------------- |
| System       | Global behavior             |
| Organization | Organizational policies     |
| Department   | Department-specific context |
| Project      | Project instructions        |
| Conversation | Conversation context        |
| User         | Personal preferences        |
| Request      | Temporary instructions      |

Each scope contributes only the information relevant to its responsibility.

For a nested chat, completed conversation content from ancestor chat nodes is
added from the root-most chat to the direct parent. It is labelled as data, not
as instructions, excludes persisted system messages, and is bounded before it
is appended to the effective system context. The nested chat keeps its own
history and current request separate.

---

## Hierarchical Inheritance

Prompt inheritance follows the hierarchy defined by the Hierarchy Architecture.

```text
Root

↓

Organization

↓

Department

↓

Project

↓

Conversation

↓

Request

```

Lower levels override or extend higher levels according to the configured merge strategy.

---

## Prompt Components

A resolved prompt may consist of multiple logical sections.

Typical sections include:

- identity
- behavioral guidelines
- project context
- domain knowledge
- tool instructions
- formatting rules
- safety instructions
- user context

These sections are combined into the final prompt.

---

## Global Prompt

The global prompt defines platform-wide behavior.

Typical examples:

- assistant identity
- communication style
- safety requirements
- formatting conventions

Every request inherits the global prompt.

---

## Organizational Prompt

Organizations may define additional instructions.

Examples:

- terminology
- corporate language
- compliance rules
- internal conventions

These prompts apply to all descendants.

---

## Department Prompt

Departments may specialize behavior.

Examples:

- engineering terminology
- legal language
- accounting conventions
- customer support tone

Only descendants inherit these prompts.

---

## Project Prompt

Projects may introduce project-specific context.

Examples:

- project goals
- technical stack
- coding standards
- documentation style

This context remains isolated from unrelated projects.

---

## Conversation Prompt

Conversation-specific prompts capture temporary context.

Examples:

- current objective
- discussion constraints
- temporary instructions

These prompts apply only to the active conversation.

---

## User Prompt

User preferences may contribute additional context.

Examples:

- preferred language
- preferred response style
- verbosity
- formatting preferences

These settings never override mandatory safety rules.

---

## Request Prompt

The request scope has the highest priority.

Examples:

- selected model
- temporary instructions
- explicit constraints

Request prompts exist only for a single request.

---

## Prompt Composition

The Prompt Resolver combines prompt fragments in deterministic order.

```text
System

↓

Organization

↓

Department

↓

Project

↓

Conversation

↓

User

↓

Request

↓

Final Prompt

```

Each stage contributes context before the next stage is applied.

---

## Merge Strategies

Different prompt sections may use different merge strategies.

Supported strategies include:

| Strategy   | Description                         |
| ---------- | ----------------------------------- |
| Replace    | Replace inherited content           |
| Append     | Add content after inherited prompt  |
| Prepend    | Add content before inherited prompt |
| Deep Merge | Merge structured prompt objects     |

The merge strategy is defined by the prompt schema.

---

## Example

Consider the following hierarchy:

```text
System
  "You are a helpful assistant."

↓

Project
  "You are assisting with the Kernschmied project."

↓

Conversation
  "Focus on backend architecture."

↓

Request
  "Generate Python code."

```

The resulting prompt contains all four levels in deterministic order.

---

## Prompt Templates

Prompt fragments may contain placeholders.

Example:

```text
Current Project: {{project_name}}

Current User: {{user_name}}

Current Date: {{date}}

```

Templates are expanded before prompt delivery.

---

## Context Variables

The resolver may provide runtime variables.

Examples:

- user name
- project name
- current date
- deployment profile
- selected model

Variables are resolved before the prompt is sent to the provider.

---

## Tool Context

When tools are enabled, the resolver may inject additional instructions.

Example:

```text
Available Tools

↓

Tool Instructions

↓

Prompt

```

Only authorized tools contribute prompt content.

---

## Model Independence

Prompt generation is independent of the underlying AI provider.

```text
Prompt Resolver

↓

Final Prompt

↓

Provider

↓

Model

```

The same logical prompt may be used with Ollama, OpenAI, Anthropic, or future providers.

---

## Prompt Caching

Resolved prompts may be cached for performance.

Typical cache key:

```text
Hierarchy Revision

+

Configuration Revision

+

Prompt Version

```

Caches are invalidated when relevant revisions change.

---

## Validation

Prompt definitions are validated before activation.

Validation includes:

- required fields
- supported placeholders
- schema version
- merge strategy
- references

Invalid prompts are rejected.

---

## Security

Prompt inheritance enforces several security principles.

Sensitive information must never be injected automatically.

Examples:

- API keys
- passwords
- private credentials
- internal secrets

Prompt content is always treated as configuration rather than trusted executable logic.

---

## Auditing

Prompt changes are recorded through the configuration audit system.

Typical audit data includes:

- timestamp
- modified prompt
- user
- affected hierarchy node
- configuration revision

This ensures complete traceability.

---

## Runtime Updates

Prompt modifications become active immediately if marked as runtime editable.

```text
Administrator

↓

Configuration API

↓

Validation

↓

Prompt Resolver

↓

Next Request

```

No application restart is required.

---

## Error Handling

If prompt resolution fails:

```text
Prompt Error

↓

Structured Error

↓

Request Aborted

```

The platform never generates partially resolved prompts.

---

## Relationship to Configuration

Prompt inheritance is implemented using the Configuration Resolver.

Prompt fragments participate in the same inheritance and merge pipeline as other runtime configuration.

---

## Relationship to Hierarchy

Hierarchy determines the inheritance path.

Changing the hierarchy automatically changes prompt resolution.

No prompt logic is embedded in hierarchy nodes themselves.

---

## Relationship to Registries

Model and tool registries contribute metadata but do not assemble prompts.

Prompt generation remains the exclusive responsibility of the Prompt Resolver.

---

## Performance Considerations

Prompt resolution is optimized for:

- deterministic execution
- minimal allocations
- cache reuse
- incremental resolution

The resolver is lightweight enough to execute for every request.

---

## Future Extensions

The architecture supports future capabilities including:

- conditional prompt fragments
- localization
- tenant-specific prompts
- reusable prompt libraries
- workflow prompts
- policy-based prompt selection
- prompt diagnostics

These extensions can be introduced without changing the public prompt contract.

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[Hierarchy-Architecture]]
- [[Configuration-Architecture]]
- [[Registry-Architecture]]
- [[Request-Lifecycle]]

---

## APIs

- [[Configuration]]
- [[Hierarchy]]
- [[Chat]]
- [[Bootstrap]]

---

## ADRs

- [[ADR-0011-Hierarchy-and-Prompt-Inheritance]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

## Summary

The Prompt Inheritance architecture provides a deterministic and hierarchical mechanism for constructing AI prompts from multiple configuration scopes.

By combining structured inheritance, configurable merge strategies, versioned prompt definitions, runtime configuration, and provider-independent prompt resolution, Kernschmied enables reusable conversational behavior that is flexible, auditable, secure, and fully integrated with the platform's generic hierarchy and configuration systems.

---

Back to [[Home]].
