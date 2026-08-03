# ADR-0032: Backup and Disaster Recovery

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a long-lived, business-critical platform.

The platform stores configuration, hierarchies, conversations, documents, runtime registries, workflows and operational data that must remain available throughout the system lifecycle.

Data loss, corruption or infrastructure failures must never compromise the integrity of the platform.

Typical protected assets include:

- databases
- runtime configuration
- registries
- hierarchy definitions
- prompts
- workflows
- documents
- audit logs
- uploaded files
- AI conversations
- search indexes
- application manifests

The platform therefore requires a comprehensive Backup and Disaster Recovery Architecture.

---

# Problem

Without a dedicated backup strategy, operational failures may result in irreversible data loss.

Typical problems include:

- hardware failures
- accidental deletion
- software defects
- database corruption
- ransomware attacks
- configuration mistakes
- incomplete backups
- untested recovery procedures

As the platform grows, recovery becomes increasingly complex without standardized processes.

---

# Decision

Kernschmied adopts a **comprehensive Backup and Disaster Recovery Architecture**.

Every critical platform asset is classified according to its recovery requirements.

Backups, recovery procedures and disaster scenarios are defined as part of the platform architecture rather than operational afterthoughts.

Recovery procedures are regularly tested.

---

# Architectural Principle

> **Every critical asset is recoverable.**
>
> **Every recovery process is documented and tested.**
>
> **Backups are verified before they are trusted.**

---

# High-Level Architecture

```text
Platform

        │

        ▼

Data Classification

        │

        ▼

Backup Service

        │

        ├──────────────┐
        │              │

        ▼              ▼

Local Backup     Remote Backup

        │              │

        └──────┬───────┘

               ▼

Recovery Procedures
```

---

# Protected Assets

The platform protects all critical runtime data.

Typical assets include:

- SQL databases
- runtime configuration
- registry definitions
- hierarchy data
- prompt definitions
- workflow definitions
- uploaded files
- generated documents
- audit logs
- application manifests
- search indexes

Every protected asset has a defined recovery strategy.

---

# Backup Types

The platform supports multiple backup strategies.

Typical types include:

- full backup
- incremental backup
- differential backup
- snapshot backup
- export backup
- archive backup

The selected strategy depends on deployment requirements.

---

# Backup Frequency

Backup frequency depends on data criticality.

Typical schedules include:

- continuous replication
- hourly backups
- daily backups
- weekly backups
- monthly archives

Schedules remain configurable.

---

# Storage Locations

Backups should be stored independently from production systems.

Typical locations include:

- local storage
- network storage
- object storage
- encrypted external media
- cloud storage

Multiple storage locations improve resilience.

---

# Encryption

Sensitive backups must be encrypted.

Encryption applies to:

- databases
- uploaded files
- configuration
- credentials
- audit data

Encryption keys are managed separately from backup storage.

---

# Verification

Every backup is verified.

Verification includes:

- integrity validation
- checksum verification
- restore simulation
- completeness checks

Unverified backups are considered unreliable.

---

# Restore Procedures

Recovery procedures are documented and repeatable.

Typical restore operations include:

- complete system restore
- database restore
- configuration restore
- file restore
- registry restore
- document restore

Recovery procedures are tested regularly.

---

# Disaster Recovery

The platform supports structured disaster recovery.

Typical scenarios include:

- complete server failure
- storage corruption
- accidental deletion
- ransomware recovery
- database corruption
- application rollback

Recovery plans are documented for each deployment profile.

---

# Recovery Objectives

Recovery objectives are defined according to deployment requirements.

Typical objectives include:

- Recovery Time Objective (RTO)
- Recovery Point Objective (RPO)

Objectives may differ between:

- development
- intranet
- internet

---

# Runtime Configuration

Backup behaviour is configurable.

Typical configuration options include:

- backup schedule
- retention period
- storage locations
- encryption policy
- verification policy

Configuration follows ADR-0014.

---

# Audit

Every backup operation generates immutable audit records.

Typical audit information includes:

- execution time
- execution identity
- backup type
- backup location
- verification result
- restore operations

Audit follows ADR-0019.

---

# Monitoring

Backup operations expose operational metrics.

Typical metrics include:

- successful backups
- failed backups
- backup duration
- storage utilization
- verification failures
- restore duration

Monitoring integrates with ADR-0030.

---

# Security

Backup systems never expose:

- plaintext credentials
- encryption keys
- authentication secrets
- unrestricted personal information

Access to backup data requires explicit authorization.

---

# Multi-Tenant Support

Backups preserve tenant isolation.

Tenant-specific data remains logically separated.

Recovery operations may restore:

- complete platform
- single tenant
- individual workspace
- individual project

where supported by the storage architecture.

---

# Versioning

Backup formats evolve independently.

Version compatibility is maintained whenever possible.

Migration tools are provided for incompatible backup versions.

All contracts follow ADR-0005.

---

# API Contracts

Future APIs may include:

- Create Backup
- Restore Backup
- Verify Backup
- Backup Status
- Backup History
- Restore Simulation

All contracts are versioned.

---

# Consequences

## Positive

### Improved Reliability

Critical data remains recoverable.

---

### Business Continuity

Recovery procedures minimize operational downtime.

---

### Better Security

Encrypted backups protect sensitive information.

---

### Operational Confidence

Regular verification increases backup reliability.

---

### Platform Consistency

Every deployment profile follows standardized recovery procedures.

---

### Future Readiness

Additional storage technologies can be integrated without architectural changes.

---

## Negative

### Additional Storage Requirements

Backups require dedicated storage capacity.

---

### Operational Complexity

Backup management introduces additional operational processes.

---

### Verification Overhead

Regular testing requires additional resources.

---

### Recovery Planning

Disaster recovery procedures require continuous maintenance.

---

# Alternatives Considered

## Manual Backups

### Advantages

- Simple implementation
- Minimal automation

### Disadvantages

- Error-prone
- Inconsistent
- Difficult verification

Rejected.

---

## Database Backups Only

### Advantages

- Easy implementation

### Disadvantages

- Configuration and files are excluded
- Incomplete recovery

Rejected.

---

## Snapshot-Only Strategy

### Advantages

- Fast recovery
- Infrastructure support

### Disadvantages

- Platform dependent
- Limited portability
- Insufficient long-term retention

Rejected.

---

# Related ADRs

- ADR-0002 — Bootstrap Configuration and Runtime Initialization
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0009 — Runtime Registry Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0016 — Knowledge Architecture
- ADR-0019 — Audit and Revision Architecture
- ADR-0020 — Multi-Tenant Architecture
- ADR-0022 — Integration Architecture
- ADR-0023a — Storage Architecture
- ADR-0030 — Monitoring and Observability
- ADR-0031 — Performance and Caching

---

# Implementation Notes

The MVP initially supports automated database backups, runtime configuration exports and uploaded file backups with local storage and manual restore procedures.

Future releases may introduce encrypted remote backups, continuous replication, point-in-time recovery, cross-region redundancy, immutable backup storage, automated disaster recovery testing and self-healing recovery workflows without changing the public backup contracts.
