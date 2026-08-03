# Getting Started

> **Version:** 1.0
> **Status:** Living Document

---

## Welcome

Welcome to **Kernschmied**.

This guide provides a quick introduction to the project and helps new developers understand the architecture, install the application, and begin contributing.

If this is your first time working with Kernschmied, this page is the recommended starting point.

---

## What is Kernschmied?

Kernschmied is a **modular, schema-driven AI platform** built with **FastAPI**, **React**, and **TypeScript**.

Unlike traditional business applications, Kernschmied separates **business logic** from **infrastructure** and **presentation**.

The backend describes:

- data
- hierarchy
- forms
- actions
- permissions
- layouts

The frontend renders generic UI components from these descriptions.

---

## Project Goals

Kernschmied focuses on five long-term goals:

- Stable public contracts
- Dynamic business configuration
- Generic frontend architecture
- Secure-by-default design
- Long-term maintainability

These principles allow the platform to evolve without requiring architectural redesigns.

---

## Architecture at a Glance

```text
		  +-----------------------+
		  |      React UI         |
		  | Generic Components    |
		  +-----------+-----------+
				|
			REST / SSE
				|
		  +-----------v-----------+
		  |      FastAPI API      |
		  | Contracts & Services  |
		  +-----------+-----------+
				|
		  +-----------v-----------+
		  | Business Services     |
		  | Registries            |
		  | Configuration         |
		  +-----------+-----------+
				|
		  +-----------v-----------+
		  | SQLite / PostgreSQL   |
		  +-----------------------+

```

---

## Before You Begin

Recommended knowledge:

- Python
- FastAPI
- React
- TypeScript
- Git
- REST APIs

Helpful but optional:

- SQLAlchemy
- Pydantic v2
- Tailwind CSS
- Server-Sent Events (SSE)

---

## Install the Project

Follow the installation guide:

→ [[Installation]]

---

## Clone the Repository

```bash
git clone https://github.com/Thomas-Heisig/Kernschmied.git

cd Kernschmied
```

---

## Project Structure

```text
Kernschmied/

backend/
frontend/
docs/
wiki/
tests/
scripts/

README.md
LICENSE
CHANGELOG.md

```

---

## Start the Backend

```bash
cd backend

uvicorn app.main:app --reload
```

Default address:

```text
http://localhost:8000

```

---

## Start the Frontend

```bash
cd frontend

npm install

npm run dev
```

Default address:

```text
http://localhost:5173

```

---

## Verify the Installation

Open:

```text
http://localhost:8000/docs

```

You should see the automatically generated OpenAPI documentation.

Then open the frontend:

```text
http://localhost:5173

```

---

## Read These Documents Next

New contributors should read the following pages in order.

## 1. Project Principles

The most important document.

→ [[Project-Principles]]

---

## 2. Architecture

Overall system architecture.

→ [[Architecture]]

---

## 3. Backend Overview

Backend responsibilities and structure.

→ [[Backend-Overview]]

---

## 4. Frontend Overview

Frontend architecture.

→ [[Frontend-Overview]]

---

## 5. Coding Guidelines

Coding standards.

→ [[Coding-Guidelines]]

---

## Understanding the Project

The project consists of several major subsystems.

## Backend

Responsible for:

- business logic
- API
- validation
- authorization
- persistence
- AI providers
- registries

---

## Frontend

Responsible for:

- rendering
- interaction
- local state
- accessibility

The frontend never contains business logic.

---

## Configuration

Kernschmied distinguishes between:

Infrastructure configuration

↓

`.env`

Business configuration

↓

Database

---

## Registries

Dynamic resources are managed through registries.

Examples:

- Model Registry
- Tool Registry
- Component Registry
- Action Registry

Registries ensure that unknown resources cannot be executed automatically.

---
