# ADR-0011: Generic Widget Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a schema-driven platform rather than a collection of business-specific user interfaces.

The platform must support dynamic presentation of arbitrary business resources without requiring new frontend development for every business object.

Widgets provide the visual representation of business information while remaining independent of specific business domains.

The platform must support:

- dynamic user interfaces
- configurable layouts
- configurable dashboards
- configurable editors
- configurable viewers
- runtime configuration
- extensible widget types
- long-term maintainability

Widgets must therefore become first-class architectural concepts.

---

# Problem

Traditional frontend applications typically introduce dedicated React components for every business use case.

Examples include:

- CustomerEditor
- CustomerList
- ProjectOverview
- InvoiceTable
- DocumentViewer
- CalendarPage

As the application grows this creates increasing complexity.

---

## Business Logic Leaks into the Frontend

Business knowledge becomes embedded inside React components.

This duplicates logic already implemented in the backend.

---

## Poor Runtime Flexibility

Adding new visualizations often requires:

- frontend development
- deployment
- additional routing
- additional testing

instead of configuration.

---

## Code Duplication

Many business pages differ only in:

- displayed fields
- layouts
- actions
- permissions

while using nearly identical presentation logic.

---

## Difficult Extensibility

Customer-specific interfaces require application development instead of runtime configuration.

---

# Decision

Kernschmied adopts a **Generic Widget Architecture**.

Widgets are generic presentation components.

They visualize data based on schemas and configuration rather than business-specific implementations.

Business objects never determine how they are rendered.

Instead, widget definitions describe the presentation.

---

# Architectural Principle

> **Resources contain information.
>
> Widgets present information.
>
> The backend decides what should be shown.
>
> The frontend decides how it is rendered.**

---

# High-Level Architecture

```text
Resource

        │

        ▼

Widget Definition

        │

        ▼

Widget Registry

        │

        ▼

Schema Renderer

        │

        ▼

React Component
```

---

# Core Concepts

The widget architecture consists of several independent concepts.

---

## Widget Type

A Widget Type describes a reusable presentation concept.

Examples include:

- form
- properties
- table
- tree
- markdown
- gallery
- timeline
- kanban
- calendar
- chart
- preview
- graph

Widget Types are generic.

They never represent business entities.

---

## Widget Definition

A Widget Definition specifies:

- widget type
- configuration
- layout
- supported actions
- supported capabilities

Definitions are runtime configuration.

---

## Widget Instance

A Widget Instance represents a configured widget within a specific context.

Examples include:

- dashboard widget
- sidebar widget
- editor widget
- chat widget
- preview widget

Instances reference Widget Definitions.

---

## Widget Layout

Layouts determine how widgets are arranged.

Examples include:

- single column
- two columns
- grid
- tabs
- split view
- stacked panels
- dashboard regions

Layouts are independent of Widget Types.

---

## Widget Configuration

Widget configuration defines presentation behavior.

Typical configuration includes:

- visible fields
- sorting
- filtering
- grouping
- pagination
- formatting
- display options

Configuration never contains business logic.

---

# Widget Registry

All Widget Types are managed through the Widget Registry.

The registry is responsible for:

- registration
- discovery
- validation
- lifecycle
- capability metadata
- version tracking

Only registered Widget Types may be rendered.

---

# Widget Capabilities

Every Widget Type declares its capabilities.

Examples include:

- editable
- selectable
- searchable
- sortable
- filterable
- pageable
- draggable
- collapsible
- printable
- exportable
- responsive

Capabilities are declarative metadata.

---

# Widget Interaction Classes

Widgets belong to interaction classes.

Examples include:

- read_only
- structured_edit
- trigger_only
- navigation
- visualization

Interaction classes define user expectations.

---

# Generic Rendering

The frontend renders widgets through the Schema Renderer.

Rendering follows this process:

```text
Widget Definition

        │

        ▼

Schema Renderer

        │

        ▼

Widget Registry

        │

        ▼

React Component

        │

        ▼

Rendered UI
```

The renderer contains no business knowledge.

---

# Unknown Widget Types

Unknown Widget Types are never executed.

Instead the frontend displays a generic "Unsupported Widget" component.

Unknown widgets never load arbitrary JavaScript.

---

# Dynamic Extensibility

New Widget Types may be introduced through the Registry Architecture.

Adding new widgets must not require modifications to:

- Resource Types
- REST APIs
- Business Services
- Existing Widgets

Only validated Widget Definitions may become active.

---

# Widget Providers

Future versions may support Widget Providers.

Examples include:

- core widgets
- package widgets
- plugin widgets

Providers register Widget Types through the Widget Registry.

---

# Widget Actions

Widgets do not implement business operations.

Instead they invoke generic Actions.

Examples include:

- create
- edit
- archive
- delete
- export
- duplicate
- summarize

Widgets remain presentation components.

---

# Widget Events

Widgets react to versioned events.

Examples include:

- resource.updated
- resource.deleted
- context.changed
- widget.invalidated
- action.completed

Widgets never poll business services directly unless explicitly configured.

---

# Runtime Configuration

Widget Definitions are runtime configuration.

Administrators may configure:

- layouts
- visibility
- ordering
- regions
- presentation
- widget composition

without changing application code.

---

# Security

Widgets never enforce permissions.

The backend determines:

- visibility
- permissions
- available actions
- editable fields

The frontend only reflects backend decisions.

---

# Separation of Responsibilities

The backend is responsible for:

- widget definitions
- schemas
- permissions
- available actions
- layout metadata

The frontend is responsible for:

- rendering
- interaction
- animations
- accessibility
- responsive behavior

---

# Relationship to Other ADRs

This decision complements:

- ADR-0001 — Schema-Driven User Interface
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0006 — API Contracts and Versioning
- ADR-0009 — Dynamic Registry and Runtime Definitions
- ADR-0010 — Generic Resource Architecture

The Widget Architecture depends on generic resources, registries and schema-driven rendering.

---

# Consequences

## Positive

### Generic User Interface

The frontend becomes independent of business domains.

---

### Runtime Extensibility

New visualizations become available through configuration.

---

### Reduced Frontend Complexity

Business-specific React components disappear.

---

### Better Maintainability

Widgets evolve independently from business objects.

---

### Reusability

The same widget may present many different resource types.

---

### Stable Contracts

Widgets communicate through versioned contracts.

---

### Plugin Readiness

Future plugins register Widget Types instead of modifying existing code.

---

## Negative

### Higher Initial Complexity

Generic widgets require careful architectural design.

---

### Strong Schema Requirements

Poor widget schemas negatively affect usability.

---

### More Validation

Widget definitions require validation before activation.

---

### Documentation Requirements

Widget Types and capabilities must be documented consistently.

---

# Alternatives Considered

## Business-Specific React Components

### Advantages

- Simple implementation
- Familiar development

### Disadvantages

- Tight coupling
- Poor extensibility
- High maintenance
- Frequent deployments

Rejected.

---

## Runtime JavaScript Execution

Generating widgets through executable scripts.

### Advantages

- Maximum flexibility

### Disadvantages

- Security risks
- Non-deterministic behavior
- Difficult validation
- Difficult testing

Rejected.

---

## Low-Code UI Framework

### Advantages

- Visual editing
- Rapid development

### Disadvantages

- Vendor lock-in
- Limited flexibility
- Poor architectural control

Rejected.

---

# Compliance

All widget-related implementations shall comply with this ADR.

In particular:

- widget types shall be registry-managed
- widgets shall remain generic
- widget definitions shall be configuration
- widget rendering shall be schema-driven
- unknown widget types shall never execute code
- widgets shall invoke generic actions
- permissions shall always be determined by the backend
- widget contracts shall be versioned
- widget capabilities shall be declarative
- widget changes shall be auditable
- widget evolution shall occur through runtime configuration
