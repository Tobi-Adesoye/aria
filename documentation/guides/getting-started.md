# Getting Started

## Prerequisites

- Python 3.11 or higher
- Git
- A ServiceNow developer instance (for integration tests — not required for unit tests)
- An Anthropic API key (for Agent 1 and Agent 3 LLM calls)

## Clone and set up

```bash
git clone https://github.com/aria-aiops/aria.git
cd aria
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

The `.env.example` file lists all required variables with descriptions. At a minimum you need:

- `ANTHROPIC_API_KEY` — for LLM calls in Agent 1 and Agent 3
- `SNOW_INSTANCE`, `SNOW_USER`, `SNOW_PASSWORD` — for the ServiceNow connector

No credentials should ever appear in code or be committed to the repository.

## Run unit tests

Unit tests require no external services or credentials:

```bash
pytest tests/unit/
```

All unit tests use in-memory stubs. They should pass in any environment.

## Run integration tests

Integration tests connect to real external services. They require valid credentials in your `.env` file and are triggered manually:

```bash
pytest tests/integration/
```

!!! warning
    Integration tests are designed to run against a **development** instance only. Never run them against a production ServiceNow instance.

## Build the documentation

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

Open `http://127.0.0.1:8000` in your browser. The site hot-reloads as you edit files in `documentation/`.

## Project layout

```
aria/
├── core/              # Agents, interfaces, models, exceptions
├── implementations/   # Concrete implementations of core interfaces
├── api/               # FastAPI REST layer
├── tests/
│   ├── unit/          # No credentials needed
│   └── integration/   # Real external services
└── documentation/     # MkDocs source (this site)
```
