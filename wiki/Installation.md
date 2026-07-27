# Installation

> **Version:** 1.0  
> **Status:** Living Document

---

# Overview

This guide describes how to install and start **Kernschmied** for local development.

The project is designed to run **without Docker** and uses a modern Python and React technology stack.

---

# System Requirements

## Operating System

Recommended:

- Windows 11
- Windows 10

Supported:

- Linux
- macOS

---

## Required Software

### Backend

- Python 3.12 or newer
- pip
- virtualenv (recommended)

### Frontend

- Node.js 20+
- npm (or pnpm)

### Development

Recommended:

- Visual Studio Code
- Git
- GitHub Desktop (optional)

---

# Clone the Repository

```bash
git clone https://github.com/Thomas-Heisig/Kernschmied.git

cd Kernschmied
```

---

# Project Structure

```
Kernschmied/

backend/
frontend/
docs/
wiki/
scripts/
tests/

README.md
```

---

# Backend Installation

Change into the backend directory:

```bash
cd backend
```

Create a virtual environment:

Windows

```powershell
python -m venv .venv
```

Linux/macOS

```bash
python3 -m venv .venv
```

Activate it.

Windows

```powershell
.venv\Scripts\activate
```

Linux/macOS

```bash
source .venv/bin/activate
```

Install the dependencies.

```bash
pip install -r requirements.txt
```

---

# Frontend Installation

Open a second terminal.

```bash
cd frontend
```

Install the dependencies.

```bash
npm install
```

---

# Environment Configuration

Create a local environment file.

```
backend/.env
```

Example:

```env
APP_PROFILE=development

HOST=127.0.0.1
PORT=8000

DATABASE_URL=sqlite+aiosqlite:///./data/kernschmied.db

SECRET_KEY=CHANGE_ME
```

> **Important**
>
> The `.env` file is only used for bootstrap, infrastructure and security settings.
>
> Business configuration is stored in the database.

---

# Database

The default database is SQLite.

No additional database server is required.

Future versions support PostgreSQL without architectural changes.

---

# Running the Backend

Example:

```bash
uvicorn app.main:app --reload
```

or

```bash
python -m app.main
```

The backend is usually available at:

```
http://localhost:8000
```

---

# Running the Frontend

```bash
npm run dev
```

The frontend is usually available at:

```
http://localhost:5173
```

---

# First Startup

During the first startup the application should:

- initialize the bootstrap process
- validate configuration
- initialize registries
- prepare the database
- expose the REST API
- expose the OpenAPI documentation

---

# OpenAPI

After startup the API documentation is available at:

```
/docs
```

OpenAPI schema:

```
/openapi.json
```

---

# Development Mode

The recommended profile is

```
development
```

Characteristics:

- simplified authentication
- local database
- verbose logging
- hot reload
- developer tools enabled

---

# Production Profiles

Kernschmied supports multiple deployment profiles.

## Development

Local development.

## Intranet

Authenticated internal deployment.

## Internet

Public deployment with strict security settings.

---

# Updating Dependencies

Backend

```bash
pip install -U -r requirements.txt
```

Frontend

```bash
npm update
```

---

# Running Tests

Backend

```bash
pytest
```

Frontend

```bash
npm test
```

---

# Common Problems

## Python not found

Verify the Python installation.

```
python --version
```

---

## Node.js not found

Verify Node.js.

```
node --version
```

---

## npm not found

```
npm --version
```

---

## Virtual Environment not activated

Ensure the virtual environment is active before installing packages.

---

## Port already in use

Change the configured port or stop the conflicting process.

---

# Updating the Repository

```bash
git pull
```

If dependencies changed:

Backend

```bash
pip install -r requirements.txt
```

Frontend

```bash
npm install
```

---

# Recommended Development Tools

- Visual Studio Code
- Python Extension
- ESLint
- Prettier
- GitHub Desktop (optional)
- Ruff
- Pyright

---

# Next Steps

After installation continue with:

- [[Getting-Started]]
- [[Architecture]]
- [[Project-Principles]]

---

## Related Pages

- [[Getting-Started]]
- [[Architecture]]
- [[Backend-Overview]]
- [[Frontend-Overview]]
- [[Development]]

---

Zurück zu [[Home]].
