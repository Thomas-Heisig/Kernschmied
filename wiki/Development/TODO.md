# TODO

The **TODO** page provides an overview of planned technical work, architectural improvements, and future enhancements for the Kernschmied platform.

Unlike the [[Roadmap]], which describes the long-term direction of the project, this page focuses on concrete implementation tasks, engineering priorities, and technical refinements. The list is intentionally dynamic and evolves continuously as the project progresses.

Items listed here represent development goals rather than commitments to a specific release.

---

# Goals

The TODO list serves several purposes:

- Track ongoing development
- Prioritize engineering work
- Document architectural improvements
- Coordinate future enhancements
- Highlight technical debt
- Improve transparency
- Support release planning
- Encourage community contributions

---

# Guiding Principles

The TODO list follows a few important principles.

- Architecture before features
- Stable contracts first
- Incremental improvements
- Small, reviewable changes
- Test-driven development whenever practical
- Documentation accompanies implementation
- Security is never postponed
- Backward compatibility is preferred

---

# Priority Levels

Tasks are grouped by priority rather than deadlines.

| Priority | Meaning |
|----------|---------|
| Critical | Required for platform stability or correctness |
| High | Important architectural improvements |
| Medium | Valuable enhancements with moderate impact |
| Low | Nice-to-have improvements |
| Future | Long-term ideas and research topics |

Priorities may change as the platform evolves.

---

# Current Focus

The current development focus is on strengthening the architectural foundation while expanding platform capabilities.

Primary objectives include:

- improving administration
- extending AI functionality
- refining runtime configuration
- strengthening plugin support
- improving documentation
- expanding automated testing

---

# Critical Tasks

The following items are considered foundational.

## Administration Interface

- Complete configuration management
- Hierarchy editor
- Model administration
- Tool administration
- Prompt administration
- Revision monitoring
- Audit log viewer

---

## Security

- Complete authentication integration
- Fine-grained authorization
- Session management
- Security policy validation
- Deployment hardening

---

## Testing

- Expand automated test coverage
- Improve integration testing
- Add contract validation
- Extend plugin tests
- Increase end-to-end testing

---

# High Priority Tasks

## Runtime Configuration

- Configuration templates
- Configuration comparison
- Rollback support
- Scheduled activation
- Environment-aware overrides

---

## Prompt Management

- Prompt editor
- Prompt diagnostics
- Prompt visualization
- Prompt version history
- Merge strategy inspection

---

## Model Management

- Capability negotiation
- Provider diagnostics
- Health monitoring
- Model benchmarking
- Runtime provider switching

---

## Tool Management

- Tool permissions
- Tool categories
- Tool health monitoring
- Tool execution history
- Usage statistics

---

## UI Improvements

- Improved dashboards
- Responsive layouts
- Accessibility enhancements
- Theme support
- Localization

---

# Medium Priority Tasks

## Plugin System

- Dependency management
- Plugin diagnostics
- Plugin lifecycle improvements
- Signed manifests
- Sandboxing research

---

## Documentation

- Administrator guide
- Plugin development guide
- Deployment cookbook
- Architecture diagrams
- Migration guides

---

## Performance

- Registry optimization
- Configuration caching
- Hierarchy optimization
- Streaming improvements
- Memory profiling

---

## Monitoring

- Metrics dashboard
- Runtime diagnostics
- Configuration metrics
- Registry statistics
- Health reports

---

# Low Priority Tasks

Potential quality-of-life improvements include:

- keyboard shortcuts
- customizable dashboards
- advanced themes
- workflow templates
- visual customization

These items should not compromise architectural consistency.

---

# Future Ideas

The following concepts are intentionally exploratory.

## AI

- multimodal interaction
- autonomous workflows
- advanced reasoning
- document intelligence
- voice interaction

---

## Collaboration

- shared workspaces
- collaborative editing
- activity feeds
- organization templates
- team permissions

---

## Enterprise

- cluster awareness
- distributed configuration
- advanced auditing
- policy engine
- tenant management

---

## Ecosystem

- plugin marketplace
- template repository
- shared schema libraries
- extension catalog
- package signing

---

# Technical Debt

Technical debt should remain visible and actively managed.

Typical examples include:

- temporary implementations
- duplicated logic
- deprecated compatibility code
- legacy interfaces
- incomplete test coverage

Whenever possible, technical debt should be resolved incrementally rather than accumulated.

---

# Documentation Tasks

Documentation should evolve together with the implementation.

Areas for improvement include:

- additional architecture examples
- developer tutorials
- operational guides
- troubleshooting documentation
- API examples
- plugin examples

Documentation is considered part of the product.

---

# Testing Tasks

Future testing improvements include:

- regression test expansion
- performance benchmarks
- compatibility verification
- visual regression tests
- automated deployment validation

Testing remains a continuous activity.

---

# Release Preparation

Before every release, verify:

- implementation completed
- tests passing
- documentation updated
- schemas validated
- manifests validated
- migrations reviewed
- release notes prepared

Release readiness should always be evaluated holistically.

---

# Community Contributions

External contributions are encouraged.

Contributors are encouraged to:

- improve documentation
- fix bugs
- add tests
- optimize performance
- improve accessibility
- suggest architectural improvements

Every contribution should follow the project's coding guidelines and architectural principles.

---

# Tracking Progress

Progress should focus on completed architectural capabilities rather than the number of finished tasks.

Typical milestones include:

```text
Planned

↓

In Progress

↓

Under Review

↓

Completed
```

This workflow keeps development transparent and predictable.

---

# Relationship to the Roadmap

The TODO list complements the [[Roadmap]].

- The Roadmap defines **where** the project is going.
- The TODO list defines **what** is currently being worked on.

Together they provide both strategic direction and practical implementation guidance.

---

# Best Practices

When adding new TODO items:

- describe the objective clearly
- keep tasks focused
- avoid implementation-specific details
- link related documentation
- update priorities as needed
- remove completed tasks promptly

A well-maintained TODO list is easier to understand and contributes to efficient project planning.

---

# Related Documentation

## Development

- [[Roadmap]]
- [[Coding Guidelines]]
- [[Release Process]]
- [[Testing]]

---

## Architecture

- [[Repository-Structure]]
- [[Extension-Points]]
- [[Manifest-System]]

---

## Concepts

- [[Runtime Configuration]]
- [[Plugin-System]]
- [[Schema Versioning]]
- [[Dynamic-UI]]

---

# Summary

The TODO page provides a continuously evolving overview of the engineering work planned for Kernschmied. It complements the long-term [[Roadmap]] by focusing on concrete technical tasks, architectural refinements, quality improvements, documentation, testing, and platform enhancements.

By prioritizing stable architecture, incremental progress, strong documentation, automated testing, and secure implementation, the TODO list helps guide the ongoing evolution of Kernschmied while preserving the project's core design principles.

---

Back to [[Home]].
