# ADR-0024 — Identity & Authorization (IAM)

Status: Proposed

Date: 2026-08-03

Authors: Kernschmied Architecture Team

## Overview

This ADR defines the Identity & Authorization architecture for Kernschmied. It establishes the canonical models, runtime flow, registries, contracts, APIs, and operational requirements for an enterprise-grade Identity and Access Management (IAM) layer suitable for a multi-tenant, hierarchical platform.

This document intentionally scopes _authentication_, _identity management_, _authorization (decisioning)_, _auditing_ and the _runtime effective security context_. Transport-level security and deployment hardening remain in ADR-0004.

## Motivation / Problem

Kernschmied is a platform where resources are organized in hierarchical scopes (tenant → workspace → project → chat → resource). Existing access-control approaches are inconsistent across services and often embed role checks or hard-coded permission logic. Problems we must solve:

- Provide a single source-of-truth for identities, roles, permissions and policies
- Support runtime-modifiable registries and policies (no code redeploys for policy changes)
- Support multiple identity providers (local, LDAP, OIDC, API tokens)
- Provide a low-latency, auditable permission evaluation API used by all services
- Support hierarchical scopes with inheritance and explicit denies
- Support service accounts, API clients, and machine-to-machine auth
- Provide migration paths from existing role-based systems

## Decision

We adopt a hybrid RBAC/ABAC model with the following core characteristics:

- Declarative PermissionDefinitions and ScopeDefinitions. Permissions are atomic, verb-based strings (e.g., `resource.read`).
- Roles are named sets of permissions (no embedded logic). Services must evaluate permissions, not roles.
- Policies (ABAC) can express conditional rules evaluated by a Policy Engine (JSONLogic or WASM-based). Policies are versioned runtime resources.
- A Permission Evaluator API serves as the canonical decision point for services. It accepts an `EffectiveSecurityContext` and returns an explicit allow/deny decision and reason.
- Registries (IdentityProvider, Identity, Role, Permission, Policy) are persisted and cacheable with event-driven invalidation.
- Short-lived caches are allowed, but strict invalidation and auditability are mandatory.

This ADR defines the complete contract for IAM objects and runtime flows to achieve the above.

## Architectural Principles

- Single source of truth: registries are authoritative; services consult the Permission Evaluator.
- Principle of least privilege: default deny unless explicitly allowed by permission or policy.
- Separation of concerns: Authentication ≠ Authorization; Role definitions ≠ business logic.
- Runtime configurability: changes to policies/roles/permissions take effect at runtime.
- Audit-first: every decision and registry change is recorded with immutable revision metadata.

## Design Goals

- Expressiveness: support both coarse-grained (RBAC) and fine-grained (ABAC) rules
- Performance: decision latency suitable for high-throughput services (<5ms cache hit)
- Scalability: multi-tenant support with tenant-isolation and global policies
- Extensibility: pluggable IdP adapters and policy evaluation engines
- Security: explicit deny precedence, immutable audit trails, revisioning

## Terminology

- Identity: an actor with a stable `id` (e.g., user, service account, agent)
- Principal: provider-specific identifier (email, DN)
- Credential: secret or token used for authentication
- Claim: an assertion attached to an authentication result
- Permission: atomic string describing an action (e.g., `resource.delete`)
- Role: named collection of permissions (no execution logic)
- Policy: conditional rule that can allow/deny permissions based on context
- Scope: hierarchical boundary (global, tenant, workspace, project, resource)
- EffectiveSecurityContext: resolved context used for permission evaluation
- Decision: result of evaluation `{ allowed: bool, reason: str, via: [...] }`

## Identity Model

Canonical shape (JSON-like):

```
Identity {
  id: uuid
  type: enum(local|oidc|ldap|api_client|service)
  principal: string
  display_name?: string
  metadata?: object
  created_at: timestamp
  updated_at: timestamp
}
```

Identity Provider (IdP) entry:

```
IdentityProvider {
  id: uuid
  type: enum(oidc|ldap|scim|none)
  config: object
  claim_mapping: { provider_claim: internal_claim }
  sync_enabled: bool
  created_at: timestamp
}
```

Notes:

- IdP claim mapping is used to normalize external claims (e.g., `sub` → `principal`, `groups` → `group_ids`).
- SCIM or LDAP sync is supported for provisioning users and groups into the local Identity registry.

## Authentication Architecture

Supported auth methods:

- Local username/password (hashed, salted, Argon2id)
- OAuth/OpenID Connect (OIDC) flows
- LDAP bind (for on-premise directories)
- API tokens (rotatable, hashed in DB)
- JWT-based service tokens (signed by platform keys)

AuthenticationResult (normalized):

```
AuthenticationResult {
  identity_id: uuid
  issued_at: timestamp
  expires_at: timestamp | null
  claims: map[string, any]
  auth_method: enum(password|oidc|ldap|api_key|m2m)
  raw_token_meta?: object
}
```

All downstream services must rely on normalized `AuthenticationResult` produced by an authentication middleware that validates tokens and maps claims via the IdP configuration.

## Authorization Architecture

We expose a single canonical service/library: `PermissionEvaluator`.

API contract (simplified):

```
POST /api/v1/permission-evaluation
{
  actor: { identity_id }
  permission: "resource.delete"
  scope: { level: "project", id: "proj-456" }
  context?: { resource, request, policy_input }
}

=> { allowed: bool, reason: string, via: {roles:[],policies:[],direct:[]}, evaluation_trace: [] }
```

Evaluator behavior:

- Collect role-derived permissions, direct assignments, and applicable policies.
- Evaluate policies (deny/allow) with explicit deny precedence.
- Return a detailed trace for auditing and debugging.

## Permission Model

PermissionDefinition:

```
PermissionDefinition {
  id: string // e.g., resource.delete
  description: string
  resource_kind?: string
  scope_levels: [global|tenant|workspace|project|resource]
  created_at, updated_at
}
```

Rules:

- Permissions are the smallest unit of authorization.
- Permissions are versioned and immutable per `schema_version` + `revision` semantics.

## Role Model

Role:

```
Role {
  id: uuid
  name: string
  description?: string
  permissions: [permission_id]
  metadata?: object
  schema_version: string
  revision: int
}
```

- Roles are bundles of permissions only; services must never check `role` names directly for decisions.

## Group Model

Groups provide convenient membership management; groups can be synchronized from IdPs.

```
Group { id, name, members:[identity_id], metadata }
```

Group membership contributes to the `EffectiveSecurityContext` and may carry role assignments.

## Claims Model

Claims are normalized key/value pairs derived from authentication tokens and IdP mappings. Claims may be used by policies (e.g., `claims.email_verified`). Claims are treated as ephemeral data tied to `AuthenticationResult` unless persisted by admin actions.

## Policy Model

Policy is a first-class, versioned runtime resource.

```
Policy {
  id: uuid
  name: string
  scope: { level, id | null }
  expression: JSONLogic | WASM
  effect: enum(allow|deny)
  precedence: int
  schema_version, revision
}
```

Policies can be authored via admin UI; they are tested in a sandbox before activation. Policies are evaluated in precedence order; explicit deny wins.

## Effective Security Context (ESC)

ESC is the input to the PermissionEvaluator and must be materialized before policy evaluation.

```
EffectiveSecurityContext {
  request_id: uuid
  timestamp
  tenant_id
  identity_id
  principal
  claims: map
  groups: [id]
  roles: [role_id]
  permission_overrides: [ {perm, allow|deny, scope} ]
  scope: { level, id }
  resource?: object
  capabilities?: [string]
}
```

The ESC must be canonical across services and cached per request lifecycle.

## Scope Hierarchy & Inheritance

Scopes are ordered: global > tenant > workspace > project > resource.

Inheritance rules:

- Permissions granted at higher scope are inherited by lower scopes unless an explicit deny is present.
- Locking prevents inheritance for sensitive tenants or resources.
- Scope-specific overrides can grant or deny per-scope.

## Identity Provider Registry

IdP registry stores configuration for OIDC, LDAP, SCIM, etc. Each entry includes claim mappings and provisioning configuration.

Admin API examples:

- `POST /api/v1/identity-providers` — create IdP
- `GET /api/v1/identity-providers/{id}` — read config

Provisioning flows:

- SCIM sync imports users and groups into Identity and Group registries.
- OIDC supports on-demand login mapping and optional provisioning rules.

## Credential Architecture

- Passwords stored using Argon2id or an equivalent KDF; no reversible storage.
- API tokens stored hashed (HMAC or bcrypt-like) with rotation support.
- JWKS keys for JWT verification stored in secure key store and rotated via a lifecycle policy.

## Session Architecture

Sessions (if used) are short-lived and bound to `AuthenticationResult`. Prefer stateless tokens (JWT) for scalability, but session store required for server-side invalidation (logout, revocation).

Session record:

```
Session { id, identity_id, created_at, expires_at, device_meta, revoked_at }
```

## Service Accounts & API Clients

Service accounts and API clients are identities with restricted scopes and long-lived credentials. They must use the same PermissionEvaluator API and be subject to the same audit and revision rules.

## Machine-to-Machine Authentication

Support JWT signed by platform keys, mTLS, or token exchange flows. All machine identities are registered in the Identity registry with `type: service`.

## Plugin Identities

Plugins that act on behalf of users obtain delegated identities via the Identity Provider Registry and must be tracked as separate identity entries with their own claims.

## Runtime Registries

Key registries (DB-backed):

- IdentityProviders
- Identities
- Groups
- Permissions
- Roles
- Policies
- ScopeDefinitions

Each registry exposes CRUD APIs, revisioning metadata, and publishes change events to the message bus for cache invalidation.

## Runtime Resolution Flow

Typical request flow:

1. Ingress middleware authenticates request → AuthenticationResult
2. Resolve identity_id → fetch identity, direct assignments, group membership
3. Materialize EffectiveSecurityContext with scope and resource
4. Call PermissionEvaluator with ESC and requested permission
5. Evaluator returns Decision and evaluation_trace
6. Service enforces Decision and emits audit event

Diagram (ASCII):

```
Client -> Ingress Auth Middleware -> Identity Registry
                               -> Build ESC -> PermissionEvaluator -> Decision
                                                      -> Policy Engine, Role Lookup, Group Lookup
```

## Permission Evaluation Engine

Requirements:

- Deterministic decisions with reproducible evaluation_trace
- Fast lookup of role and permission assignments (caching)
- Policy evaluation sandbox (JSONLogic or WASM) with timeouts
- Pluggable PDP backends (in-process for low-latency; remote OPA for centralized governance)

Decision precedence:

1. Explicit deny (policy or direct)
2. Explicit allow (policy)
3. Role/permission allow
4. Default deny

## Decision Cache & Invalidation

- Cache key: `(identity_id, permission, scope_id, token_revision)`
- TTL: short (default 60s), configurable per deployment
- Invalidation via pub/sub on registry changes (roles, policies, permissions)

## Audit & Revision

All actions produce audit events. Decision audit record includes:

```
{ request_id, timestamp, identity_id, permission, scope, decision, trace, registries_revision }
```

Registry changes produce revisioned events with `revision_id` and `author` metadata.

Retention: audit logs stored in append-only storage with configurable retention & export to SIEM (optional).

## Events & Integrations

- RegistryChange events: `role.updated`, `policy.published`, `permission.created`
- AuditEvent stream consumed by analytics, SIEM, and compliance

## API Contracts

Core endpoints (examples):

- `POST /api/v1/auth/login` — returns AuthenticationResult
- `POST /api/v1/permission-evaluation` — returns Decision
- `GET /api/v1/identities/{id}`
- `GET /api/v1/roles/{id}`
- `POST /api/v1/policies`

Contracts must be typed (OpenAPI) and included in the documentation/manifest.

## Administrative Interfaces

Admin UI must provide safe policy authoring with test harness, role and permission management, identity provisioning, IdP configuration, and effective permissions view.

## Deployment Profiles

- Development: relaxed TTLs, in-process policy engine, local IdP
- Production: distributed caches (Redis), external PDP option, strict TTLs and audit forwarding

## Security Rules (must)

- Never evaluate roles for authorization decisions — always evaluate permissions.
- Explicit deny has precedence.
- All registry writes are authenticated and produce audit/revision records.
- Secrets and credential material must be stored in a secure vault.

## Performance Considerations

- Optimize for cache hit paths; precompute permission matrices for service accounts.
- Evaluate policy complexity budgets (limit nested evaluations / expensive functions).

## Migration Strategy

1. Inventory existing roles and direct permissions
2. Create PermissionDefinitions for all unique actions
3. Import roles as Role objects with the mapped permissions
4. Deploy PermissionEvaluator in simulation mode (returns decision but does not enforce)
5. Run a shadow-enforcement period, inspect audit traces, adapt policies
6. Flip to enforced mode

## Alternatives Considered

- Pure RBAC: insufficient for dynamic conditions and resource-owner checks
- Pure ABAC (no roles): high operational overhead and complex policy surfaces
- Centralized OPA-only PDP: strong governance but higher latency; chosen design supports PDP as pluggable option

## Consequences

- Positive: Flexible, auditable, enterprise-grade IAM; supports future extensibility
- Negative: Operational complexity (policy management) and cache invalidation complexity

## Related ADRs

- ADR-0004 Security Profiles and Deployment Modes
- ADR-0003 Registries
- ADR-0020 Multi-Tenant Architecture
- ADR-0023 Hierarchy and Modeling

## Implementation Notes

- Define DB schema for registries with `schema_version` and `revision` fields
- Create lightweight PermissionEvaluator library (Python) and an HTTP adapter
- Provide admin UI components for role/policy management
- Add test harness for policies (unit + integration)

## Appendix: Example Workflows

1. Resource delete request (high level):

- Authenticate -> AuthenticationResult
- Build ESC for `project:proj-456`
- Evaluate `resource.delete` -> Decision {allowed: false, reason: "policy:protect-resources"}
- Return 403 and write audit entry

1. Policy rollout:

- Author policy in Admin UI
- Run tests against sample ESCs
- Publish policy (creates revision)
- Event `policy.published` invalidates caches

---

This ADR is intentionally prescriptive: roles are permission-bundles only, policies and permissions are the source of dynamic behavior, and all decisions are audited and versioned. The next step is to convert this ADR into a concrete implementation plan with DB schemas, API OpenAPI fragments, and a minimal PermissionEvaluator reference implementation.
