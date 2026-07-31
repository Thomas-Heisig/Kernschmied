# Release Process

The **Release Process** defines how new versions of Kernschmied are planned, validated, published, and deployed. Its purpose is to ensure that every release is predictable, reproducible, well-tested, and fully traceable.

Rather than treating releases as simple code snapshots, Kernschmied considers every release a coordinated evolution of source code, schemas, APIs, manifests, documentation, and runtime configuration. Every released version represents a stable platform state that can be reproduced and supported over time.

The Release Process applies equally to the backend, frontend, plugins, documentation, and deployment artifacts.

---

# Goals

The Release Process is designed to provide:

- Predictable releases
- Reproducible builds
- Stable public contracts
- Comprehensive validation
- Controlled version evolution
- Reliable deployment
- Complete traceability
- Long-term maintainability

---

# Design Principles

The release process follows several core principles.

- Every release is reproducible.
- Every release is versioned.
- Every release is validated.
- Every release is documented.
- Every release preserves stable contracts.
- Every release can be traced back to its source.

Releases should never depend on undocumented manual steps.

---

# Release Lifecycle

A release follows a deterministic lifecycle.

```text
Planning

↓

Development

↓

Testing

↓

Validation

↓

Release Candidate

↓

Final Release

↓

Deployment

↓

Maintenance
```

Each stage has clearly defined responsibilities.

---

# High-Level Workflow

```text
Source Code

↓

Build

↓

Automated Validation

↓

Release Candidate

↓

Final Approval

↓

Version Tag

↓

Published Release
```

Every released artifact originates from a validated source revision.

---

# Versioning

Every release receives an explicit version.

Example:

```text
0.1.0

↓

0.2.0

↓

1.0.0
```

Version numbers communicate platform evolution and compatibility expectations.

---

# Semantic Versioning

Kernschmied follows Semantic Versioning.

| Version Part | Meaning                           |
| ------------ | --------------------------------- |
| Major        | Breaking changes                  |
| Minor        | New compatible functionality      |
| Patch        | Compatible fixes and improvements |

Examples:

```text
1.2.0

↓

1.2.1
```

Compatible bug fix.

```text
1.2.0

↓

1.3.0
```

New functionality.

```text
1.2.0

↓

2.0.0
```

Breaking architectural evolution.

---

# Release Planning

Before implementation begins, a release should define:

- objectives
- architectural changes
- API changes
- schema changes
- migration requirements
- documentation updates
- testing scope

Planning reduces release risk.

---

# Feature Development

Development takes place on feature branches.

Typical workflow:

```text
Main

↓

Feature Branch

↓

Implementation

↓

Review

↓

Merge
```

The main branch should always remain releasable.

---

# Code Review

Every significant change should undergo peer review.

Review typically verifies:

- architecture
- correctness
- readability
- security
- maintainability
- testing
- documentation

Reviews improve long-term code quality.

---

# Automated Validation

Every release candidate should pass automated validation.

Typical validation includes:

- compilation
- linting
- static analysis
- schema validation
- manifest validation
- unit tests
- integration tests

Failures block the release process.

---

# Testing

Testing should verify the complete platform.

Recommended categories include:

- backend tests
- frontend tests
- API tests
- configuration tests
- registry tests
- plugin tests
- deployment tests

All critical functionality should be validated before release.

---

# Contract Validation

Public contracts are verified before publication.

Examples include:

- REST APIs
- UI schemas
- manifests
- runtime configuration
- SSE events

Unexpected breaking changes should be detected before deployment.

---

# Documentation

Documentation is part of every release.

Documentation updates include:

- architecture
- APIs
- deployment
- configuration
- migration notes
- release notes

Documentation should reflect the released platform rather than future plans.

---

# Release Candidate

A Release Candidate (RC) represents a version believed to be production-ready.

Typical workflow:

```text
Feature Complete

↓

Validation

↓

Release Candidate

↓

Final Verification
```

Only critical issues should delay a Release Candidate.

---

# Final Release

Once validation is complete, the release becomes official.

```text
Release Candidate

↓

Approval

↓

Version Tag

↓

Published Release
```

Published releases should remain immutable.

---

# Build Reproducibility

A release should be reproducible from version-controlled sources.

```text
Version Tag

↓

Build

↓

Identical Artifacts
```

Builds should not depend on undocumented local modifications.

---

# Deployment Readiness

Before deployment, verify:

- configuration
- database migrations
- provider compatibility
- plugin compatibility
- schema versions
- documentation

Deployment should never introduce unexpected runtime changes.

---

# Database Migrations

Schema changes requiring persistence updates should use version-controlled migrations.

Typical workflow:

```text
Migration

↓

Validation

↓

Deployment

↓

Updated Database
```

Database changes should be backward-compatible whenever practical.

---

# Runtime Configuration

Runtime configuration is not part of the application build.

Instead:

```text
Application

+

Runtime Configuration

↓

Operational Platform
```

Configuration changes should be versioned and audited independently.

---

# Plugin Compatibility

Plugins should be validated against the target platform version.

Checks include:

- manifest compatibility
- schema versions
- supported extension points
- registry integration

Incompatible plugins should be identified before deployment.

---

# Security Review

Before release, security-sensitive changes should be reviewed.

Examples include:

- authentication
- authorization
- configuration
- secret handling
- API exposure
- dependency updates

Security validation is part of the release process.

---

# Dependency Management

Dependencies should be reviewed before every release.

Verify:

- supported versions
- security advisories
- compatibility
- licensing
- maintenance status

Outdated or vulnerable dependencies should be addressed before publication whenever practical.

---

# Release Notes

Each release should include release notes describing:

- new functionality
- bug fixes
- architectural improvements
- breaking changes
- migration requirements
- known limitations

Release notes provide a clear overview of platform evolution.

---

# Rollback Strategy

Every deployment should have a rollback plan.

Typical rollback process:

```text
Deployment Failure

↓

Rollback

↓

Previous Stable Release
```

Rollback procedures should be documented and tested.

---

# Long-Term Support

Stable releases may receive maintenance updates.

Maintenance releases typically include:

- bug fixes
- security updates
- compatibility improvements

New features should generally be introduced in new minor or major releases.

---

# Traceability

Every release should be traceable to:

- source revision
- version tag
- build artifacts
- migration scripts
- documentation
- release notes

Traceability simplifies maintenance and auditing.

---

# Common Release Checklist

Before publishing a release, verify:

- Source code is complete.
- All tests pass.
- Schemas are validated.
- Manifests are validated.
- Documentation is updated.
- Version numbers are correct.
- Migration scripts are verified.
- Security review is complete.
- Release notes are prepared.
- Deployment instructions are current.

---

# Future Evolution

The Release Process supports future enhancements including:

- automated release pipelines
- signed release artifacts
- continuous delivery
- automated compatibility verification
- release quality dashboards
- dependency health reporting
- reproducible container images

These enhancements strengthen automation while preserving the underlying release philosophy.

---

# Relationship to Other Development Processes

The Release Process works together with:

- [[Coding Guidelines]]
- [[Testing]]
- [[Debugging]]
- [[Development Environment]]

Each process contributes to overall software quality.

---

# Related Documentation

## Development

- [[Coding Guidelines]]
- [[Testing]]
- [[Debugging]]
- [[Development Environment]]

---

## Architecture

- [[Contract-Versioning]]
- [[Repository-Structure]]
- [[Manifest-System]]
- [[Extension-Points]]

---

## Concepts

- [[Schema Versioning]]
- [[Runtime Configuration]]
- [[Plugin-System]]
- [[Versioning]]

---

## Deployment

- [[Development]]
- [[Intranet]]
- [[Internet]]

---

# Summary

The Release Process defines a structured and repeatable workflow for delivering new versions of Kernschmied. By combining semantic versioning, automated validation, comprehensive testing, documentation, contract verification, migration planning, and reproducible builds, every release represents a stable and traceable platform state.

Through disciplined planning, review, validation, and deployment practices, the Release Process enables Kernschmied to evolve safely while maintaining compatibility, reliability, and long-term maintainability across the entire platform.

---

Back to [[Home]].
