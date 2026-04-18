# Crossbook

Crossbook is a schema-driven Flask application for building structured knowledge databases (characters, locations, chapters, inventory, or any custom entities) without hardcoding forms per table.

It combines:

- **Dynamic database-backed schema** (`field_schema`) for rendering forms and filters.
- **Table list/detail UI** with inline edits, undo history, and relationship links.
- **Admin tools** for database/configuration, import jobs, dashboards, and automation rules.
- **Wizard-first setup** for initializing a new database and first base table.

---

## Table of Contents

- [What Crossbook Does](#what-crossbook-does)
- [Core Features](#core-features)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Local Development](#local-development)
  - [Requirements](#requirements)
  - [Run the app](#run-the-app)
  - [Run background worker](#run-background-worker)
  - [Run tests](#run-tests)
- [Runtime Concepts](#runtime-concepts)
  - [Wizard gating](#wizard-gating)
  - [Field types](#field-types)
  - [Relationships](#relationships)
  - [Dashboard widgets](#dashboard-widgets)
  - [Import jobs](#import-jobs)
  - [Automation rules](#automation-rules)
- [HTTP Endpoints (high-level)](#http-endpoints-high-level)
- [Operational Notes](#operational-notes)

---

## What Crossbook Does

Crossbook stores metadata about your base tables in SQLite and uses that metadata to drive both backend behavior and frontend rendering. The same schema powers:

- list views,
- detail forms,
- filter controls,
- dashboard data sources,
- import validation and mapping.

This means adding/changing fields at runtime (including options, foreign keys, and layout metadata) updates UI behavior without requiring template rewrites.

---

## Core Features

### Dynamic records UI

- List view per base table (`/<table>`) with:
  - text search,
  - structured filters and operators,
  - pagination,
  - sort direction,
  - export of filtered/all/selected records (`/<table>/export`).
- Detail view (`/<table>/<id>`) with:
  - inline field editing,
  - edit history + per-entry undo,
  - field-level styling and layout persistence,
  - relationship visibility controls.

### Runtime schema editing

- Add or remove fields from existing base tables.
- Validate and convert field types through admin routes.
- Toggle readonly/title behavior in `field_schema` via admin routes.

### Relationships

- Uses a single `relationships` table (instead of per-table join tables).
- Supports add/remove relationship actions and optional two-way links.

### Import pipeline

- CSV upload and mapping UI at `/import`.
- Validation preview via `/trigger-validation`.
- Asynchronous import jobs tracked in `import_status` with:
  - `/import-start`
  - `/import-status?importId=<id>`
- Import completion can trigger automation rules configured to run on import.

### Dashboard system

- Dashboard view with widgets grouped by `group`.
- Widget types: `value`, `table`, `chart`.
- Drag/resize persistence via `/dashboard/layout`.
- Data helper endpoints for counts, top/bottom numeric values, and filtered records.

### Automation rules

- CRUD API for rules under `/admin/api/automation/rules`.
- Manual run/reset/log routes.
- Scheduled rules are queued through Huey (`daily` / `always`).

---

## Architecture Overview

### App composition

`main.py` creates the Flask app, checks whether setup is complete, conditionally redirects to the wizard, registers blueprints, and injects runtime schema data into all templates via a context processor.

Registered blueprints:

- `views.records.record_views.records_bp`
- `views.wizard.wizard_bp`
- `views.admin.admin_bp`
- `views.api.api_bp`

### Persistence model

Crossbook uses SQLite and stores global/system metadata in core tables created by `db/bootstrap.py`, including:

- `config`
- `config_base_tables`
- `field_schema`
- `dashboard_widget`
- `edit_history`
- `automation_rules`
- `relationships`

### Module responsibilities

- `db/`: low-level data access and schema operations.
- `views/`: Flask routes split by domain (records/admin/wizard/api).
- `imports/`: CSV parsing + Huey background jobs.
- `automation/`: rule execution and task triggering.
- `utils/`: field registry, record/list helpers, validation/sanitization.
- `templates/` + `static/`: Jinja UI and browser-side interactions.

---

## Project Structure

```text
crossbook/
├── main.py
├── logging_setup.py
├── requirements.txt
├── data/                     # runtime SQLite files (app DB + huey queue DB)
├── db/                       # schema/config/records/dashboard/relationships/automation helpers
├── views/
│   ├── records/              # list/detail/record APIs
│   ├── admin/                # config, fields, dashboard, imports, automation
│   ├── wizard.py             # first-run flow
│   └── api/                  # lightweight API endpoints
├── imports/                  # CSV parser + Huey tasks
├── automation/               # automation engine
├── utils/                    # field registry + validation + helper utilities
├── templates/                # Jinja templates and partials
├── static/                   # CSS/JS assets
└── tests/                    # pytest suite
```

---

## Local Development

### Requirements

- Python 3.11+ recommended
- SQLite (bundled with Python)

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the app

```bash
python main.py
```

Open: `http://127.0.0.1:5000`

If setup is incomplete, requests are redirected to `/wizard/` until configuration and initial table setup are completed.

### Run background worker

In a second terminal (same virtualenv):

```bash
huey_consumer.py imports.tasks.huey
```

This worker processes import jobs and scheduled automation tasks.

### Run tests

```bash
pytest
```

If you want faster feedback, run a targeted subset first, for example:

```bash
pytest tests/test_wizard_routes.py tests/test_import_jobs.py tests/test_admin_dashboard_views.py
```

---

## Runtime Concepts

### Wizard gating

Before setup is complete, `before_request` redirects non-wizard routes to `/wizard/`. Wizard steps cover:

1. database file selection/creation,
2. required settings,
3. initial table(s) and field definitions,
4. optional CSV import.

### Field types

Field behavior is centralized in the type registry (`utils.field_registry` + `utils.validation`). Built-in types are:

- `text`
- `number`
- `date`
- `select`
- `multi_select`
- `foreign_key`
- `boolean`
- `textarea`
- `url`

Each type can define:

- SQL storage type,
- validation function,
- default layout width/height,
- render macro,
- filter macro,
- value normalizer,
- capabilities (`searchable`, `numeric`, `allows_options`, etc.).

### Relationships

Relationships are stored as row pairs in `relationships` with:

- `table_a`, `id_a`
- `table_b`, `id_b`
- `two_way`

The record detail page composes related-record groups from this table and applies per-table visibility config.

### Dashboard widgets

Widgets are persisted in `dashboard_widget` and can be created/updated/deleted through admin routes. Layout and style updates are posted as JSON and persisted server-side.

### Import jobs

`imports/tasks.py` uses `SqliteHuey` (`data/huey.db`) and tracks job progress in `import_status`.

Import flow:

1. enqueue job,
2. set status `queued` → `in_progress` → `complete`/`failed`,
3. accumulate row-level errors,
4. trigger import-based automation rules.

### Automation rules

Rules store:

- condition field/operator/value,
- action field/value,
- run mode (`run_on_import`, `schedule`).

Rules can be:

- run immediately,
- triggered after imports,
- enqueued on schedule via Huey task dispatch.

---

## HTTP Endpoints (high-level)

### Core / bootstrap

- `GET /` home
- `GET/POST /wizard/*` setup workflow
- `GET /api/base-tables` navigation metadata

### Records

- `GET /<table>` list
- `GET /<table>/<id>` detail
- `GET|POST /<table>/new`
- `POST /<table>/<id>/update`
- `POST /<table>/<id>/delete`
- `POST /<table>/bulk-update`
- `POST /<table>/<id>/undo/<edit_id>`
- `POST /relationship`
- `POST /<table>/layout`
- `POST /<table>/style`
- `POST /<table>/relationships`
- `GET /<table>/count-nonnull`
- `GET /<table>/sum-field`
- `GET /<table>/field-distribution`
- `GET /<table>/export`
- `GET /api/<table>/list`
- `GET /api/<table>/records`

### Admin

- `GET /admin`
- `GET /admin/config`
- `GET /admin/database`
- `GET /admin/fields`
- `GET /dashboard`
- `GET|POST /import`
- `POST /trigger-validation`
- `POST /import-start`
- `GET /import-status`
- automation routes under `/admin/api/automation/*`

---

## Operational Notes

- **When system tables change**, update bootstrap table creation in `db/bootstrap.py` so new databases get the latest schema.
- **`data/` is runtime state**; treat `.db` files as environment-specific, not source of truth.
- Logging behavior is configurable through values stored in `config` and applied through `logging_setup.py`.
- For production deployments, provide a strong `SECRET_KEY` via environment variable.

