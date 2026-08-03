# ADR-0021: Search Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is intended to become a knowledge-centric platform where users can efficiently locate information regardless of where it is stored.

Search is not a single feature but a platform capability used by nearly every subsystem.

Examples include:

- hierarchy navigation
- chats
- messages
- resources
- prompts
- documentation
- knowledge base
- uploaded files
- AI models
- tools
- workflows
- configuration
- audit records
- future integrations

As the amount of information grows, traditional keyword search alone becomes insufficient.

The architecture therefore requires a search system capable of supporting multiple search strategies while remaining extensible and secure.

---

# Problem

Many applications implement independent search functions for each module.

Typical problems include:

- duplicated search logic
- inconsistent ranking
- different query syntaxes
- poor scalability
- difficult maintenance
- no unified search experience
- hardcoded search implementations

Adding semantic search later often requires major architectural changes.

---

# Decision

Kernschmied adopts a **Provider-Based Search Architecture**.

Search is implemented as an independent platform capability.

The application communicates only with the Search Service.

The Search Service delegates execution to registered search providers.

Different search technologies may coexist without changing business services.

---

# Architectural Principle

> **Business services request search results.**
>
> **Search providers determine how results are produced.**
>
> **Search implementations remain replaceable.**

---

# High-Level Architecture

```text
Application

        │

        ▼

Search Service

        │

        ▼

Search Registry

        │

 ┌──────┼──────────┬──────────┐
 │      │          │          │
 ▼      ▼          ▼          ▼

Keyword  Fulltext  Semantic  Hybrid
Provider Provider  Provider  Provider
```

---

# Search Service

The Search Service represents the only public entry point for search operations.

Business services never communicate directly with search engines.

Responsibilities include:

- query validation
- authorization
- provider selection
- ranking
- filtering
- result aggregation
- response normalization

---

# Search Providers

Every search implementation is represented by a provider.

Examples include:

- keyword search
- SQL full-text search
- SQLite FTS
- PostgreSQL full-text search
- vector search
- embedding search
- hybrid search
- external enterprise search

Providers are registered through the Search Registry.

---

# Search Registry

The Search Registry manages available providers.

Responsibilities include:

- registration
- validation
- discovery
- capability metadata
- lifecycle management

Providers become available only after successful registration.

---

# Search Targets

Search operates on logical resource types rather than database tables.

Examples include:

- hierarchy nodes
- chats
- messages
- resources
- prompts
- workflows
- documentation
- knowledge
- files
- audit records
- configuration

New search targets can be introduced without modifying the Search Service.

---

# Search Types

The architecture supports multiple search strategies.

Examples include:

## Keyword Search

Exact word matching.

Suitable for:

- identifiers
- names
- configuration
- commands

---

## Full-Text Search

Natural language document search.

Suitable for:

- documentation
- notes
- chat history
- knowledge

---

## Semantic Search

Meaning-based retrieval using embeddings.

Suitable for:

- AI knowledge
- documentation
- similar conversations
- context retrieval

---

## Hybrid Search

Combination of:

- keyword search
- full-text search
- semantic search

Results are merged and ranked.

---

# Query Processing

Every search request follows the same processing pipeline.

```text
User Query

        │

        ▼

Validation

        │

        ▼

Authorization

        │

        ▼

Search Service

        │

        ▼

Provider

        │

        ▼

Ranking

        │

        ▼

Results
```

---

# Search Contracts

Search requests remain implementation independent.

Typical request information includes:

- query
- search scope
- target types
- filters
- pagination
- sorting
- capabilities

Providers may extend implementation details internally.

---

# Search Results

All providers return normalized results.

Typical information includes:

- identifier
- object type
- title
- description
- relevance score
- location
- highlights
- metadata

The frontend renders results generically.

---

# Ranking

Ranking is provider independent.

Factors may include:

- textual relevance
- semantic similarity
- recency
- popularity
- hierarchy context
- user context

Ranking algorithms may evolve without changing public contracts.

---

# Authorization

Every search request is evaluated against the effective authorization context.

Users only receive results they are permitted to access.

Authorization is performed before results are returned.

The frontend never filters unauthorized results.

---

# Tenant Isolation

Search always operates within the active tenant context.

Future cross-tenant search requires explicit administrative permissions.

No provider may bypass tenant isolation.

---

# Hierarchy Integration

Hierarchy context influences search.

Examples include:

- current workspace
- current project
- current chat
- subtree search
- global search

The hierarchy defines the effective search scope.

---

# Knowledge Integration

Knowledge search uses the same architecture.

Possible providers include:

- document search
- embedding search
- vector databases
- hybrid retrieval

Knowledge providers remain interchangeable.

---

# AI Integration

AI features may request search results through the same Search Service.

Examples include:

- Retrieval-Augmented Generation (RAG)
- context retrieval
- prompt augmentation
- similar conversation lookup

AI models never access search engines directly.

---

# Caching

Search providers may cache:

- parsed queries
- indexes
- embeddings
- ranking data

Caching remains internal to each provider.

Public contracts remain unchanged.

---

# Index Management

Search indexes are implementation details.

Possible index types include:

- SQL indexes
- FTS indexes
- vector indexes
- inverted indexes

The Search Service remains independent of index technology.

---

# Event Integration

Search indexes react to platform events.

Examples include:

- resource.created
- resource.updated
- resource.deleted
- chat.completed
- hierarchy.changed

Providers update indexes asynchronously when appropriate.

---

# Plugin Integration

Additional search providers may be installed through packages.

Examples include:

- Elasticsearch
- OpenSearch
- PostgreSQL
- SQLite FTS
- Qdrant
- Milvus
- Weaviate

The application core remains unchanged.

---

# Performance

Large datasets require scalable indexing.

Possible optimizations include:

- incremental indexing
- background indexing
- cached embeddings
- provider-specific optimization

Performance improvements do not affect public contracts.

---

# Security

Search providers must never expose:

- unauthorized data
- secrets
- internal prompts
- hidden configuration
- deleted objects
- archived objects without permission

Security policies are enforced before results leave the backend.

---

# Consequences

## Positive

### Unified Search Architecture

Every subsystem uses the same search interface.

---

### Replaceable Providers

Search technologies remain interchangeable.

---

### Future Semantic Search

Vector search integrates without architectural changes.

---

### Better Maintainability

Search logic remains centralized.

---

### Improved User Experience

Users receive consistent search behavior across the platform.

---

### AI Ready

Future RAG capabilities integrate naturally.

---

## Negative

### Additional Infrastructure

Provider abstraction increases implementation complexity.

---

### Ranking Complexity

Result ranking requires continuous refinement.

---

### Index Maintenance

Indexes require synchronization and monitoring.

---

### Provider Validation

Every provider must implement consistent contracts.

---

# Alternatives Considered

## Module-Specific Search

Advantages

- Simple implementation

Disadvantages

- Duplicate logic
- Inconsistent behavior
- Poor scalability

Rejected.

---

## Database Queries Only

Advantages

- Minimal infrastructure

Disadvantages

- Limited search capabilities
- No semantic search
- Difficult ranking

Rejected.

---

## Single External Search Engine

Advantages

- Powerful indexing

Disadvantages

- External dependency
- Vendor lock-in
- Reduced flexibility

Rejected.

---

## Direct AI Search

Advantages

- Natural language interaction

Disadvantages

- Expensive
- Non-deterministic
- Poor precision for structured queries

Rejected.

---

# Related ADRs

- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0007 — Generic Hierarchy and Context Architecture
- ADR-0009 — Runtime Registry Architecture
- ADR-0010 — Generic Resource Architecture
- ADR-0013 — Event Architecture
- ADR-0015 — Chat and Conversation Architecture
- ADR-0016 — Knowledge Architecture
- ADR-0018 — Plugin and Package Architecture
- ADR-0020 — Multi-Tenant Architecture
- ADR-0022 — Integration Architecture
- ADR-0028 — AI Model Architecture
- ADR-0030 — Monitoring and Observability
- ADR-0031 — Performance and Caching

---

# Implementation Notes

The MVP initially provides a simple keyword and SQL-based search implementation.

The architecture is intentionally designed so that full-text search, semantic search, hybrid retrieval and Retrieval-Augmented Generation (RAG) can be introduced later as additional providers without changing public contracts or business services.
