
# Crossbook

Crossbook is a structured, browser-based knowledge interface for managing content and its related metadata. It provides an easy way to organize and cross-reference entities (for example: books or chapters of content, and related characters, locations, factions, etc.) along with their interrelationships. The application features a clean design and uses a normalized SQLite database (with join tables) to map many-to-many relationships between entities.

## Table of Contents
- [Project Summary](#project-summary)
  - [Future Cloud Migration](#future-cloud-migration)
- [Current Status](#current-status)
- [Implemented Features](#implemented-features)
- [Project Structure](#project-structure)
- [Application Architecture and Code Overview](#application-architecture-and-code-overview)
  - [Main Application – `main.py`](#main-application-mainpy)
    - [Field Schema Injection](#field-schema-injection)
    - [Record Fetching](#record-fetching)
    - [Update Logic](#update-logic)
  - [Functions in `main.py`](#functions-in-mainpy)
  - [Front-End Scripts – `static/js/`](#front-end-scripts-staticjs)
    - [column_visibility.js](#columnvisibilityjs)
    - [relations.js](#relationsjs)
  - [Templates – `templates/`](#templates-templates)
    - [base.html](#basehtml)
    - [index.html](#indexhtml)
    - [list_view.html](#listviewhtml)
    - [detail_view.html](#detailviewhtml)
    - [macros/fields.html](#macrosfieldshtml)
  - [Import Workflow](#import-workflow)

## Project Summary

* **Tech Stack:** Python 3.x, Flask (web framework), Jinja2 (templating), Tailwind CSS (styling via CDN), SQLite (relational database). JavaScript libraries include custom JavaScript for layout editing and custom scripts under `static/js/` for validation and UI behavior.
* **Dynamic UI Generation:** Automated list and detail views based on database schema introspection.
* **Search & Visibility Controls:** Text-based search filters and toggleable columns for list views, with filter controls implemented via Jinja macros.
* **Navigation:** Centralized in `templates/base.html`, providing consistent header navigation and action buttons across all entity pages.
* **Database Layer:** Abstracted in the `db/` package (`database.py`, `schema.py`, `records.py`, `relationships.py`) for connection handling, schema loading, CRUD operations, and relationship management.
* **Logging:** Python’s `logging` module tracks errors and activity. Flask session is not currently used.

### Future Cloud Migration

* **Move from SQLite to a managed cloud database** (e.g. PostgreSQL) to support scalability and multi-instance deployments.
* **Integrate a task queue** (e.g. Google Cloud Tasks) for any long-running or background jobs (CSV import, relationship syncing, etc.).
* **Adjust configuration and deployment** to read credentials and connection strings from environment variables or secret stores.

## Current Status

* **Detail View Layout Editor:** drag-and-drop and resizing are fully functional and layouts save via the `/<table>/layout` endpoint.
* **Setup Wizard:** `/wizard/` walks through choosing or creating a database, adjusting settings, adding an initial table, and optionally importing a CSV.

## Implemented Features

* **List View with Search:** Each entity list page allows filtering records by text-based fields with a search box (`list_view.html`).
* **Column Visibility:** Columns can be shown or hidden on the fly using the **Columns** dropdown (`column_visibility.js`).
* **Detail View & Inline Edit:** Displays all fields on the detail page with inline editing via text inputs, date pickers, checkboxes, or textareas. Numeric field changes now save via AJAX and append to the edit log without reloading the page.
* **Relationship Management:** Displays related records and allows adding/removing relationships through a modal interface (+ to add, ✖ to remove), using AJAX to update join tables dynamically.
* **Rich Text Support:** Textareas are enhanced with [Quill](https://quilljs.com/) for WYSIWYG editing.
* **Edit History:** Tracks each record’s modifications in an `edit_log`, viewable via an expandable history section. Individual entries now include an **Undo** link to revert that change.
* **Navigation Bar:** A consistent top navigation (`base.html`) links to Home and all base table sections.
* **Bulk Edit Modal:** Select rows in a list view and update a single field across all of them at once.
* **Supported Field Types:** text, number, date, select, multi-select, foreign-key, boolean, textarea, and url, each rendered with the appropriate input control.
* **Field Type Registry:** New types can register their SQL storage, validation function, default layout size, and rendering macro.
* **Filter Macros:** Reusable Jinja macros for boolean, select, text, and multi-select filters (`templates/macros/filter_controls.html`).
* **Text Filter Operators:** `contains`, `equals`, `starts_with`, `ends_with`, `not_contains`, and `regex` operators are available when filtering text fields. Regex matching requires database support and falls back to a normal `LIKE` search if unavailable.
* **Field Schema Editing:** New endpoints allow adding or removing columns at runtime (`/<table>/<id>/add-field`, `/<table>/<id>/remove-field`) and counting non-null values (`/<table>/count-nonnull`).
* **Admin Dashboard & Configuration:** The `/admin` section includes a configuration editor and placeholder pages for user management and automation.
* **Layout Defaults from DB:** Field width and height defaults are loaded from the `config` table instead of being hardcoded.
* **Layout Editor Persistence:** detail page layouts save to the database via the `/<table>/layout` endpoint.
* **Automatic Dashboard Widget Placement:** New widgets are inserted at the next
  available row in the grid without specifying `row_start`.
* **Dashboard Charts:** Pie, bar and line chart widgets rely on Flowbite Charts. The repo ships a placeholder `flowbite-charts.min.js`; download the real library for production use.
* **Table Widget:** Displays simple tabular data such as base table record counts.
* **Select Value Counts:** Table widget option that shows counts of each choice for a select or multi-select field.
* **Top/Bottom Numeric:** Table widget listing records with the highest or lowest values for a numeric field.
* **Filtered Records Widget:** Table widget showing records from any table matching a search filter, with optional sort and limit.
* **Dashboard Grid Editing:** Widgets can be dragged, resized, and saved using `/dashboard/layout`.
* **Numerical Summaries:** `/<table>/sum-field` returns the sum for numeric columns, used by dashboard charts.
* **List API:** `/api/<table>/list` provides ID and label data for dropdowns.
* **CSV Import Workflow:** Upload a CSV on `/import`, map fields, then start a background job via `/import-start` and poll `/import-status` for progress.

## Project Structure

```text
/
├── README.md                        # Project documentation and setup instructions
├── main.py                          # Application entrypoint; Flask app setup and routes
├── logging_setup.py                 # Logging configuration helper
├── requirements.txt                 # Python dependencies
├── db/                              # Database layer modules
│   ├── config.py                    # Configuration helpers (get_config_rows, update_config)
│   ├── database.py                  # Connection and session management
│   ├── schema.py                    # Schema introspection and migrations
│   ├── records.py                   # CRUD operations
│   ├── relationships.py             # Many-to-many join helpers
│   ├── validation.py                # Field and data validation logic
│   └── edit_fields.py               # Field schema editing utilities
├── imports/                         # CSV helpers and background tasks
│   ├── import_csv.py                # parse_csv reads uploaded files into memory
│   └── tasks.py                     # Huey tasks for processing imports
├── static/                          # Front-end assets
│   ├── css/
│   │   ├── overrides.css            # Tailwind override styles
│   │   └── styles.css               # Additional global styles
│   ├── js/
│   │   ├── add_table.js             # Create new tables dynamically
│   │   ├── bulk_edit_modal.js       # Bulk edit modal logic
│   │   ├── column_visibility.js     # Column toggle logic
│   │   ├── dashboard_modal.js       # Dashboard widgets
│   │   ├── edit_fields.js           # Client-side field schema editing
│   │   ├── editor.js                # Initialize Quill editors
│   │   ├── field_ajax.js            # Inline updates via fetch
│   │   ├── filter_visibility.js     # Show/hide filter controls
│   │   ├── layout_editor.js         # Drag/drop & layout persistence
│   │   ├── dashboard_grid.js       # Drag and resize dashboard widgets
│   │   ├── dashboard_charts.js     # Render charts from field data
│   │   ├── config_admin.js         # Helpers for editing config JSON
│   │   ├── undo_edit.js            # Undo actions via AJAX
│   │   ├── relations.js             # AJAX for add/remove relationships
│   │   └── tag_selector.js          # Multi-select tag UI helper
│   └── imports/
│       ├── import_start.js          # Import page bootstrap (unused)
│       ├── progress_bar.js          # Progress bar helper (unused)
│       ├── validation_UI.js         # Client-side validation widgets
│       ├── match_logic.js           # CSV field matcher
│       └── validation.py            # Import form validation helpers
├── templates/                       # Jinja2 view templates
│   ├── base.html
│   ├── admin.html                   # Admin landing page
│   ├── admin_automation.html        # Placeholder automation page
│   ├── admin_users.html             # Placeholder user management
│   ├── bulk_edit_modal.html         # Modal for bulk edits
│   ├── config_admin.html            # Configuration editor
│   ├── dashboard.html               # (WIP) summary page
│   ├── edit_fields_modal.html       # Modal partial for field editing
│   ├── import_view.html             # CSV import workflow
│   ├── index.html
│   ├── list_view.html
│   ├── new_record.html
│   ├── detail_view.html
│   └── macros/
│       ├── fields.html              # Field rendering macros
│       └── filter_controls.html     # Filter UI macros
├── views/                           # Flask blueprints
│   ├── admin.py                     # Admin and dashboard routes
│   ├── records.py                   # CRUD and list/detail endpoints
│   └── wizard.py                    # Setup wizard workflow
├── utils/                           # Shared helper modules
│   ├── field_registry.py            # Field type registry and defaults
│   ├── html_sanitizer.py            # Sanitize editor HTML
│   └── validation.py                # CSV import validation functions
├── tests/                           # Automated tests
│   ├── test_api_records.py
│   ├── test_import_jobs.py
│   ├── test_wizard_database.py
│   └── test_wizard_skip.py
└── data/                            # Runtime data directory
    ├── crossbook.db                # Main application SQLite database
    └── huey.db                     # Task queue persistence database
```

## Import Workflow

1. **Start the worker**: run `huey_consumer.py imports.tasks.huey` from the project root so background jobs are processed.
2. **Upload a CSV**: visit `/import`, choose a base table, and upload your CSV file. All rows are loaded into memory and shown for mapping.
3. **Kick off the import**: after matching columns, click **Import Records** or POST to `/import-start`.

   ```json
   {
     "table": "character",
     "rows": [{"name": "Gandalf"}]
   }
   ```
4. **Monitor progress**: poll `/import-status?importId=<id>`.

   ```json
   {
     "status": "in_progress",
     "totalRows": 1,
     "importedRows": 0,
     "errorCount": 0,
     "errors": []
   }
   ```

Large files are not streamed—they are fully loaded into memory during parsing, so extremely big uploads may exhaust memory.

## Application Architecture and Code Overview

* **Routing & Views:** Defined in `main.py` using Flask decorators; routes handle list, detail, new record, and error pages. A context processor (`@app.context_processor`) injects the `field_schema`—the in-memory representation of all table fields, types, options, and layout—into all templates and front-end scripts for dynamic form generation and validation. Error handlers (e.g., `@app.errorhandler(404)`) and `abort()` calls manage invalid requests.

* **Configuration & Environment:** Dependencies listed in `requirements.txt`. The SQLite database path defaults to `data/crossbook.db` and is stored in the `db_path` row of the `config` table.

* **Database Layer:** Uses Python’s built-in `sqlite3` in `db/database.py` for connection management. Schema introspection and migrations occur in `db/schema.py`. CRUD operations reside in `db/records.py`; many-to-many join logic in `db/relationships.py`. Validation rules live in `db/validation.py`, and field schema editing utilities in `db/edit_fields.py`.

* **Background Tasks:** Huey is initialized in `imports/tasks.py` and provides the `process_import` task used by the import workflow. Start a worker with `huey_consumer.py imports.tasks.huey`.

* **Frontend Interaction:** Dynamic behaviors powered by JavaScript modules in `static/js/`:

  * `add_table.js` for creating new tables
  * `bulk_edit_modal.js` for multi-record editing
  * `column_visibility.js` to toggle table columns
  * `dashboard_modal.js` for dashboard widgets
  * `edit_fields.js` for client-side schema and field editing
  * `editor.js` initializes Quill editors for textarea fields (see the [Quill documentation](https://quilljs.com/docs/quickstart/) for editor usage)
  * `field_ajax.js` for inline field updates without page reloads (imported by `detail_view.html`)
  * `filter_visibility.js` for showing/hiding filter controls
  * `layout_editor.js` for drag-and-drop and grid persistence
  * `relations.js` for AJAX-based add/remove relationships
  * `tag_selector.js` (multi-select dropdown UI)
  * `dashboard_charts.js` renders Flowbite charts using field counts and sums
  * `dashboard_grid.js` enables dashboard drag & resize
  * `config_admin.js` processes layout defaults forms
  * `undo_edit.js` allows reverting edits via AJAX

* **Static Assets & Styling:** Tailwind is loaded via CDN in `templates/base.html`. Global rules live in `static/css/styles.css`, while `static/css/overrides.css` contains Tailwind tweaks used by the layout editors. Update these files to change colors, spacing or other visual details.

* **Templating & Macros:** Jinja2 templates in `templates/` include the core pages (`base.html`, `index.html`, `list_view.html`, `detail_view.html`, `new_record.html`, `dashboard.html`) plus admin and import views. Partial templates like `edit_fields_modal.html` and `bulk_edit_modal.html` are used for modals. Reusable macros live in `templates/macros/fields.html` and `filter_controls.html`.

* **Logging & Monitoring:** Logging is configured via `logging_setup.py` and values stored in the database. Both Flask and root handlers are cleared, then a rotating or timed file handler is attached. Only error-level messages appear in the console. Werkzeug request logs are disabled. Logs capture errors and user actions.
* **Utility Helpers:** Helper modules in `utils/` include field type registration, HTML sanitization and the CSV import validator.

* **Data Directory:** Runtime files under `data/`: `crossbook.db` (primary database) and `huey.db` (task queue store). The `db_path` entry in the `config` table can point the application at a different database file.






### **Main Application – `main.py`**

This is the core of the Flask application. It defines the web routes, handles database interactions, and implements the logic for listing records, showing details, editing fields, and managing relationships. The application uses a single Flask app instance and a single SQLite database file.

**Global configuration and variables in `main.py`:**

- **Flask App Initialization:** The Flask app is created with `static_url_path='/static'` so that files in the `static/` directory are served at the `/static` URL path.
- **`DB_PATH`:** Path to the SQLite database file. Defaults to `data/crossbook.db` but is updated from the `db_path` value stored in the `config` table. All modules obtain a connection using `with get_connection()` from `db/database.py`.
- **`BASE_TABLES`:** Derived from the `config_base_tables` table via `load_base_tables()`. It contains all entity table names and is used to validate route parameters.
- **`FIELD_SCHEMA`:** Retrieved via `get_field_schema()` whenever needed. It returns a dictionary in the form `{table: {field: {"type": ..., "options": [...], "foreign_key": ..., "layout": {...}, "styling": {...}}}}` describing how each field should be treated in the UI. The `styling` key contains any JSON-parsed styling instructions.
- **`field_options`:** A `field_options` column in the `field_schema` table contains a JSON-encoded list of options for select fields (e.g., `["Elf", "Human"]`). These options are resolved on demand using the helper `get_field_options()`.
 - Instead, templates call the `get_field_options(table, field)` helper to fetch options at render time.

#### Field Schema Injection
The context processor `inject_field_schema` loads the field schema and navigation card data before rendering templates, exposing them and `update_foreign_field_options` globally.

#### Record Fetching
`list_view` builds filter and operator dictionaries from query parameters and then calls `get_all_records`. `detail_view` obtains a record with `get_record_by_id`, gathers relationships via `get_related_records`, and loads layout info from the schema.

#### Update Logic
`update_field` interprets the field type, handles lists for multi-select and foreign keys, coerces booleans and numbers, writes changes with `update_field_value`, and appends a note to `edit_log` when a value changes.

### Functions in `main.py`:

The following functions encapsulate the application logic:

| Function & Signature                          | Purpose                                                             |
|-----------------------------------------------|----------------------------------------------------------------------|
| `get_connection()`                            | Context manager that yields a connection to the SQLite database using `DB_PATH`. The path is loaded from the `db_path` setting in the `config` table. Use `with get_connection()` to ensure it closes automatically. |
| `load_field_schema()`                         | Queries the database for all defined fields in the `field_schema` table and returns a nested dict of `{table: {field: {"type": ..., "options": [...], "foreign_key": ..., "layout": {...}}}}`. |
| `get_field_options(table, field)`             | Retrieves a list of options for a given `select` field from the `field_schema` table. Returns a list parsed from the `field_options` column (assumed to be valid JSON), or an empty list if none is present or if parsing fails. Used at render time only inside templates that need it. |
| `get_all_records(table, search=None)`         | Retrieves up to 1000 records from the specified table. If a `search` string is provided, it filters the results to those where any text-like field contains the search substring (case-insensitive). Only fields of type *text, textarea, select,* or *multi select* are searched. Returns a list of records as dictionaries (each dict maps field names to values). Logs the SQL query and catches any errors (returning an empty list on error). |
| `get_record_by_id(table, record_id)`          | Fetches a single record by its ID from the specified table. Returns a dictionary of field names to values for that record, or `None` if not found. This uses `sqlite3.Row`-like logic by first retrieving the table’s column names (via `PRAGMA table_info`) and then zipping with the fetched row tuple. |
| `get_related_records(source_table, record_id)` | Gathers related records for a given record (by looking at join tables). It scans the database’s table names for any join table involving `source_table`. For each join table found (e.g., `character_location` or `location_character`), it figures out the *other* table and then selects the related records from that table. Returns a dictionary where each key is a related table name and each value is an object with a human-readable label and a list of related items (each item has an `id` and a `name`). Only the first field of the related table (assumed to be the name/title field, often the same name as the table) is used as the display name. Any errors in querying a particular join table are caught and simply skipped (so a broken or missing join table will not crash the whole function). |
| `home()`                                      | **Route:** GET `/` – Renders the **home page** (`index.html`). This page is a simple overview with links to each section of the site. |
| `list_view(table)`                            | **Route:** GET `/<table>` – Renders the **list view page** for a given entity type. If the `<table>` parameter is not one of the `BASE_TABLES`, it returns 404. Otherwise, it uses `get_field_schema()` to determine which fields to display (all except those marked hidden or internal), gets an optional `search` query param from the request to filter results, and calls `get_all_records`. It then renders `list_view.html`, passing in the table name, the list of fields, the list of record dicts, and the `request` object (for access to query params in the template). |
| `inject_field_schema()`                       | **Context Processor:** Injects the current field schema and the `get_field_options` helper function into all template contexts. This makes `field_schema[...]` (including layout and styling info) and `get_field_options(table, field)` available to macros and templates. Templates use `get_field_options` to dynamically render dropdowns for fields of type `select` using options defined in the `field_schema` table. |
| `detail_view(table, record_id)`               | **Route:** GET `/<table>/<int:record_id>` – Renders the **detail view page** for a single record. If the table is not in `BASE_TABLES`, or the record with that ID doesn’t exist, it aborts with 404. Otherwise, it fetches the record via `get_record_by_id` and all related records via `get_related_records`. It then renders `detail_view.html`, providing the table name, the record dict, and the related records dict to the template. |
| `update_field(table, record_id)`              | **Route:** POST `/<table>/<int:record_id>/update` – Handles inline edits from the detail page. This is called when a user submits a field edit form. It first ensures the table is valid and the record exists. It then reads `field` (the field name to update) and the new value from the form data (`new_value` or `new_value_override`). Certain fields are protected: attempting to edit the primary `id` or the `edit_log` directly will result in a 403 Forbidden. For other fields, it determines the expected data type from the field schema and **coerces** the input accordingly: booleans are converted to "1" or "0", numbers to int (default 0 if parse fails), and all other types are treated as strings. It then executes an `UPDATE ... SET field = ?` query to save the new value. If the value changed, it appends a timestamped entry describing the change to the record’s `edit_log` field (this is done by concatenating text). After updating, it commits the transaction and redirects the user back to the detail view page for that record. |
| `manage_relationship()`                       | **Route:** POST `/relationship` – AJAX endpoint for adding or removing a relationship (join table entry) between two records. It expects a JSON payload with `table_a`, `id_a`, `table_b`, `id_b`, and an `action` ("add" or "remove"). The two table names are sorted alphabetically to determine the join table name (e.g., `character` + `thing` -> join table **character_thing**). Depending on the action, it either inserts a new row (with the two IDs) into the join table or deletes the matching row. It uses `INSERT OR IGNORE` for adds (to avoid duplicates) and a straightforward DELETE for removal. On success, returns JSON `{"success": True}` (HTTP 200). If the join table doesn’t exist or another database error occurs, it returns an error message JSON with status 500. If required fields are missing or an invalid action is given, it returns a 400 error. *(Note: This function uses a direct sqlite3 connection separate from `get_connection()` for convenience and does not explicitly reuse the app’s global connection helper.)* |
| `dashboard()` | **Route:** GET `/dashboard` – Displays the dashboard page with draggable widgets.
| `api_list(table)` | **Route:** GET `/api/<table>/list` – Returns JSON with `id` and `label` values for dropdowns. |

| `add_field_route(table, record_id)` | **Route:** POST `/<table>/<int:record_id>/add-field` – Adds a new column to the table and updates the field schema. |
| `remove_field_route(table, record_id)` | **Route:** POST `/<table>/<int:record_id>/remove-field` – Removes a column from the table and refreshes the schema. |
| `count_nonnull(table)` | **Route:** GET `/<table>/count-nonnull?field=<name>` – Returns a JSON count of non-null values for the specified field. |
| `field_distribution(table)` | **Route:** GET `/<table>/field-distribution?field=<name>` – Returns JSON counts of each value for the given field. |

| `sum_field(table)` | **Route:** GET `/<table>/sum-field?field=<name>` – Returns the sum of a numeric field. |

| `update_layout(table)` | **Route:** POST `/<table>/layout` – Saves grid coordinates for fields on the detail page. |
| `dashboard_create_widget()` | **Route:** POST `/dashboard/widget` – Creates a new dashboard widget. |
| `dashboard_update_layout()` | **Route:** POST `/dashboard/layout` – Saves the positions of dashboard widgets. |
| `add_table()` | **Route:** POST `/add-table` – Adds a new base table and join tables. |
All routes and functions above are actively used by the application (there is no dead code in `main.py`). When run directly, the app simply calls `update_foreign_field_options()` and then starts with `app.run(debug=True)`.

### **Front-End Scripts – `static/js/`

#### 📄 **`column_visibility.js`**

**Purpose:** Controls the dynamic visibility of table columns on list view pages, allowing the user to hide or show columns for better readability.

**Key Functions/Behaviors:**

- `checkboxes()`: Helper that selects all DOM checkbox inputs with class `.column-toggle` (the column toggles in the Columns dropdown).
- `getSelectedFields()`: Gathers the values of all checked column toggle checkboxes. These values correspond to field names (all lower-case).
- `updateVisibility()`: Shows or hides table columns based on selected fields. It iterates through all table header cells (`<th>`) and body cells (`<td>`) and toggles their CSS `display` style. If a column’s field name is unchecked, that column’s cells are hidden. This function is called whenever a checkbox state changes.
- Event Listeners: The script attaches interactive behavior:
  - A click on the "Columns" button (`#toggle-columns`) will toggle the visibility of the dropdown menu that contains the checkboxes.
  - A click anywhere outside the dropdown closes the dropdown (by adding the `hidden` class back).
  - Clicking on any checkbox calls `updateVisibility()` immediately.
  - On page load, `updateVisibility()` runs once to enforce the default state (initially all columns are checked/shown).

**Relevant DOM Elements:**

- **Columns Dropdown Button:** `#toggle-columns` – the button that shows/hides the columns checklist.
- **Dropdown Container:** `#column-dropdown` – the `<div>` that contains the list of column toggles (checkboxes). It is shown/hidden by toggling a `hidden` CSS class.
- **Column Checkboxes:** Inputs with class `.column-toggle` – each corresponds to a field. These are generated by the template for each non-internal field.
- **Table Headers & Cells:** The script assumes each `<th>` in the `<thead>` has text matching the field name, and each `<td>` in the `<tbody>` has a `data-field` attribute set to the field name (in lower-case). This way, `updateVisibility()` can match checkbox values to column cells.

#### 📄 **`relations.js`**

**Purpose:** Manages the relationship-addition modal on detail pages and handles sending add/remove requests for relationships. This script enables users to link existing records together without leaving the detail view.

As of April 2025, `field_ajax.js` includes `submitMultiSelectAuto(form)` to autosave changes from `multi_select` fields and update the selected tags without a full page reload. Dropdowns still close automatically when clicking outside them (handled in `relations.js`).

**Exported Functions:**

- `openAddRelationModal(tableA, idA, tableB)`: Opens the "Add Relation" modal to link a record from **tableA** (with id **idA**, the current record) to some record in **tableB**. When called, it:
  - Stores the source and target info in a `modalData` object.
  - Displays the modal dialog (removes the `hidden` class from the overlay).
  - Initiates a fetch request to `/<tableB>` (the list page for the target entity type) to get the HTML of the list of existing records for that type.
  - Parses the returned HTML to extract the list of records: it looks at the table rows and pulls out the first two columns (expecting the ID and a name/title). Those are turned into options in the modal’s dropdown (`#relationOptions`).
  - If the target table is not "content", it sorts the options alphabetically by label (for easier selection). Content is left unsorted or sorted by ID, assuming content might not have a meaningful short name.
  - Populates the dropdown select with the retrieved options (record id and name).
- `closeModal()`: Closes/hides the relationship modal dialog by adding back the `hidden` class to the overlay. Allows the user to cancel the add relation process.
- `submitRelation()`: Reads the selected option from the dropdown, then sends a POST request to the `/relationship` endpoint to **add** a relationship. It uses the data in `modalData` (which was set by `openAddRelationModal`) to know the source table and IDs, and takes the selected target record ID from the dropdown. The request payload includes `action: "add"`. On success (or once the request is done), the page is reloaded to show the updated list of related items.
- `removeRelation(tableA, idA, tableB, idB)`: Sends a POST request to `/relationship` to **remove** a relationship. It is called when the user clicks the ✖ button next to an existing related item. It sends `table_a`, `id_a`, `table_b`, `id_b` and `action: "remove"`. After the request, it reloads the page to reflect the removal.

**How it’s used in the app:** These functions are imported as a module in `detail_view.html`. The template then exposes them to the global `window` object so that the inline HTML buttons (`onclick` handlers on the + and ✖ buttons) can call them. The modal’s dropdown is populated by `openAddRelationModal` and the form submission is handled entirely via JavaScript (no separate form element is used for adding relations, just the JS function).

**Relevant DOM Elements:**

- **Modal Container:** `#relationModal` – the overlay `<div>` that contains the relationship form. Hidden by default, it’s made visible when adding a relation.
- **Dropdown Select:** `#relationOptions` – the `<select>` inside the modal where options (target records to link) are populated.
- **Add Button (in modal):** Calls `submitRelation()` – in the HTML, this is a button that triggers the JS function to add the selected relation.
- **Cancel Button (in modal):** Calls `closeModal()` – hides the modal without making changes.
- **Plus Button (on detail page):** Each related section has a + button that calls `openAddRelationModal(currentTable, currentId, targetTable)`, telling the script what relation to add.
- **Remove (✖) Button:** Next to each related item in the list, calls `removeRelation(currentTable, currentId, relatedTable, relatedId)` to unlink those two records.

*(Note: The approach of fetching an entire HTML page and parsing it to get record options is a bit unorthodox. It works for now, but a future improvement could be to provide a JSON endpoint to retrieve records more efficiently.)*

### **Templates – `templates/`**

The Flask Jinja2 templates define the structure of the HTML pages. The templates use Tailwind CSS for styling and rely on the data passed from `main.py` (and global context processors) to render dynamic content. The templates are designed to be generic, working for any table/record given the schema information.

#### 📄 **`base.html`**

**Purpose:** Base layout template that all other pages extend. It defines the overall HTML structure, including the `<head>` (where Tailwind CSS is included via CDN) and a consistent header/navigation bar.

**Layout and Features:**

- **Tailwind Inclusion:** Loads Tailwind CSS from the official CDN for styling. No separate CSS files are used; styles are from Tailwind utility classes.
- **Navigation Bar:** A responsive `<nav>` bar at the top lists sections from the `config_base_tables` table (plus Home). This means new tables automatically appear in the nav with their configured display names.
- **Content Block:** Uses Jinja `{% block content %}{% endblock %}` to define where child templates insert their page-specific content. Similarly, a `{% block title %}` sets the `<title>` tag for each page (so pages can specify a custom title, like “Characters List” or “Character 5”). The base provides a padded container `<div class="p-6">` around the content block for consistent spacing.
- **Global Context:** Thanks to the `inject_field_schema` context processor, every template extending base.html automatically has access to `field_schema` (the schema dict) as well as other Flask globals like `request`. This base does not itself display dynamic data (aside from the nav links), but it provides the framework within which other templates render their content.

#### 📄 **`index.html`**

**Purpose:** Home page, providing a quick entry point to each section of the application.

**Content:** The index extends `base.html` and renders a grid of cards. A static dashboard card links to `/dashboard`, followed by cards loaded from the `config_base_tables` table. Each table card specifies a `display_name`, `description`, and links to `/<table>`. New rows added to this table automatically appear on the home page.

#### 📄 **`list_view.html`**

**Purpose:** Generic list page template for any entity table. It displays a table of records (with columns as fields) and provides search and column visibility controls.

**Key Elements:**

- **Header and Title:** Shows the capitalized table name plus "List". For example, if viewing the `character` table, it will display "Characters" as a header.
- **Search Form:** At the top of the list, there's a search input and submit button. It preserves the current search query in the input field (using `request.args.get('search', '')`). Submitting the form reloads the page with a query parameter to filter results (handled in the route logic).
- **Column Visibility Dropdown:** A button labeled "Columns" toggles a checklist of all fields. By default, each field (except internal ones starting with `_`) is listed with a checked checkbox. This uses the structure defined in the template to generate inputs with class `.column-toggle` and value equal to the field name. The `column_visibility.js` script (included at the bottom of this template) controls the show/hide behavior based on these checkboxes. This feature lets users hide columns that they aren't interested in to reduce clutter.
- **Bulk Edit Button:** Rows include checkboxes so multiple records can be selected. The **Bulk Edit** button opens a modal to update one field for all selected rows.
- **Records Table:** The records are displayed in a table (`<table>` element):
  - The header row `<thead>` is generated by looping through the `fields` list passed from the view. Each field is shown as a table heading (`<th>`), with the field name capitalized. 
  - The body `<tbody>` contains one row per record. Each row is generated by looping through the same fields list. Table cells `<td>` display the field’s value for that record. The template adds `data-field="{{ field|lower }}"` attribute to each cell to facilitate the column toggle script.
  - Special case: If the field is `edit_log`, the template only displays the first line of the log (usually the oldest entry or a summary) to keep the table compact. (The full edit log is available on the detail page.)
  - Each table row has an `onclick` handler that navigates to the detail page for that record (`window.location.href='/<table>/<id>'`), making the entire row clickable as a shortcut.
- **No Records Message:** If the `records` list is empty (either no data or no match for the search), the template shows a friendly message "No records found."
- **Scripts:** At the end of the content, the template includes the `column_visibility.js` script via a `<script src="{{ url_for('static', filename='js/column_visibility.js') }}"></script>` tag. This is what enables the column toggle functionality described above.

#### 📄 **`detail_view.html`**

**Purpose:** Generic detail page for a single record of any entity. This template is the most complex, as it handles dynamic field display, inline editing forms, and related items section.

**Layout Overview:** The page is divided into two main sections side by side:
- **Left side** – the main details of the record (all fields and the edit log).
- **Right side** – the related records (links to other entities connected via join tables) and the Add Relationship modal trigger.

Key features of the detail view:

- **Title and Identifier:** At the top of the left panel, the record’s primary name is displayed in a large heading. By convention, the first field of each table (often named after the table itself, e.g., a `character` table might have a `character` field that holds the name) is used as the title. Next to it, the record’s ID is shown for reference.
- **Fields Table:** Below the title, the template iterates over `record.items()` (each field name and value in the record dict) and generates a two-column table of field names and values:
  - It looks up the field’s type via `field_schema[table][field]` to decide how to display it. If the field’s type is `'hidden'`, it skips rendering that field entirely (this allows certain fields to exist in the data but not show up in the UI).
  - For each visible field, it sets `field_type` accordingly (stripping any whitespace just in case).
  - The field name is displayed as a table header cell (with proper capitalization).
  - The field value is displayed in a table data cell. However, instead of directly outputting the value, the template calls a macro to handle rendering. It uses `{% import "macros/fields.html" as fields %}` at the top, and here it calls `fields.render_editable_field(...)`, passing in all relevant context:
    - `field` (the name of the field),
    - `value` (the current value),
    - `record.id`, `table` (to identify which record to update if editing),
    - `detail_endpoint='detail_view'` and `update_endpoint='update_field'` (the Flask endpoint names for viewing and updating, used to generate URLs),
    - `id_param='record_id'` (the URL parameter name for the record ID in those endpoints),
    - `field_type` (the type of the field, e.g., text, number, boolean, etc. as determined from schema),
    - `request` (to check query parameters, specifically if an edit is in progress).
  - The macro `render_editable_field` (defined in **`macros/fields.html`**, explained below) will either display the field value or an edit form input depending on whether the user is currently editing that field (indicated by a query param like `?edit=fieldname` in the URL).
- **Edit / View Mode:** The `render_editable_field` macro uses `request.args.get('edit')` to see if the current field is the one being edited. 
  - If yes, it outputs a `<form>` with the appropriate input for that field type, pre-filled with the current value. Inputs save automatically via AJAX on change. For example:
    - Text fields -> a simple text input.
    - Number fields -> a number input.
    - Date fields -> an HTML date picker.
    - Textarea (long text) -> a Quill-powered editor for HTML content.
    - Boolean fields -> a toggle checkbox input.
    - `multi_select` fields now render as searchable dropdowns with checkboxes and tag-style badges for selected values. Users can filter options live, deselect tags with ✖, and all changes autosave automatically. A Tailwind-styled dropdown appears inline with live filtering and closing behavior.
  - If the field is **not** in edit mode, the macro will display the value in a read-only format:
    - For textarea (HTML content) fields: it wraps the content in a `<div class="prose">` to apply typographic styling to the HTML content (and uses `|safe` to allow rendering HTML).
    - For boolean fields: it shows a colored badge with "Yes" or "No". Actually, for booleans, the macro provides a special case: even when not explicitly in edit mode, the boolean is shown as a clickable form (the colored badge is a submit button that immediately flips the boolean value). This design allows one-click toggling of true/false fields without needing the separate edit step.
    - For foreign key fields: currently just displays the value in italic blue text (as a visual cue that it’s a reference) – but it’s not a link. This is a placeholder for future functionality.
    - All other fields: displayed as plain text.
    - In all non-edit cases (except booleans which have their own form), an edit ✏️ icon link is provided next to the value. Clicking this link reloads the page with the `?edit=<fieldname>` query parameter, thus switching that field into edit mode.
- **Edit Log:** If the `record.edit_log` field is present and not empty, the template shows an **Edit History** section below the fields table. Each entry includes an **Undo** button which posts back to revert that particular change. The section is implemented with a `<details>` element containing a list of the past changes.
- **Related Records (Right Panel):** On the right side, the template shows **Related Pages**:
  - It loops over the `related` dictionary (from `get_related_records`). Each entry corresponds to a related table, with a label (e.g., "Locations") and a list of related items.
  - For each related table section, it displays a heading (the label) and a **+ button**. The + button triggers the `openAddRelationModal(table, id, related_table)` JavaScript function (with the current record’s table and ID, and the target related table).
  - Under that, if there are any related items:
    - It lists each item with a link to that item’s detail page (using the item’s name, or the ID if the related table is "content" – because content might be large text, the app uses ID to avoid showing a huge string).
    - Beside each item is a small ✖ button that triggers the `removeRelation(currentTable, currentId, relatedTable, relatedId)` function to remove that link.
  - If there are no related items for that category, it simply shows "None" in gray.
- **Add Relation Modal:** The HTML for the modal dialog is included at the bottom of this template (but by default it’s hidden with CSS). It consists of a centered box with:
  - A dropdown `<select id="relationOptions">` which will be populated with options via `relations.js`.
  - An "Add" button that calls `submitRelation()` and a "Cancel" button that calls `closeModal()`.
  - This modal is only made visible when the user clicks one of the + buttons, via the JS functions described earlier.
- **Scripts:** At the very end, the template includes the `relations.js` module via a `<script type="module">`. It imports the needed functions and then attaches them to the global `window` object so that the inline onclick handlers in the HTML can access them. This script enables the interactive add/remove relationship functionality described above.

Overall, `detail_view.html` works in tandem with `macros/fields.html` and the JS modules to provide an interactive detail page that not only displays data but also allows editing and relationship management.

#### 📄 **`macros/fields.html`**

**Purpose:** Defines a Jinja2 macro that encapsulates the logic for rendering a field either in view mode or edit mode. This avoids repeating a lot of conditional template code for each field in the detail view.

**Key Macro:**

- **`render_editable_field(field, value, record_id, request, detail_endpoint, update_endpoint, id_param, field_type, table)`** – This macro, when called in the context of a record detail page, will output the appropriate HTML for that field. It uses the parameters to form the correct form action URLs and determine how to display the value.

**Behavior:**

- If the current request’s query param `edit` matches this field’s name, it means the user is editing this field. The macro will produce an `<form>` element targeting the `update_field` route (using `url_for(update_endpoint, table=..., record_id=...)`). 
  - It always includes a hidden `<input name="field">` with the field’s name (so the backend knows which field to update).
  - Then, depending on `field_type`, it renders an appropriate input:
    - **textarea:** Uses a Quill editor with the HTML stored in a hidden `new_value` input.
    - **boolean:** Renders a checkbox input (styled as a toggle switch via CSS classes). It’s checked if the current value is truthy ( "1", 1, or True). This lets the user change the boolean value. (Note: in edit mode, this is a single checkbox inside the form; in view mode, booleans are handled differently as described below).
    - **number:** Renders a numeric input (`<input type="number">`) with the current value.
    - **date:** Renders a date picker (`<input type="date">`) with the current value.
    - **default (text):** Renders a basic text input for any other field type (e.g., simple text or unrecognized types).
    - For number fields, the input’s `onchange` handler calls `field_ajax.js` to save the new value via `fetch`, displaying a short “Saved” indicator without refreshing the page.
- If the field is **not** being edited (normal display mode):
  - For **textarea** fields (which contain HTML content), it wraps the value in a `<div class="prose">` and marks it safe, so the HTML formatting is rendered. This nicely displays paragraphs, links, etc., with Tailwind’s typography styles.
  - For **select** fields: the chosen option is shown as plain text. **multi_select** and **foreign_key** values appear as blue tag badges. When in edit mode these fields use searchable dropdowns with checkboxes.
  - For **date** fields: simply display the stored date string.
  - For **foreign_key** fields: displays the value in a span with italic, blue styling as a hint that it’s a reference. (This is a placeholder; ideally it would be a link to that related record’s page, but that requires additional context which is not yet provided to the template.)
  - For **boolean** fields: Instead of a plain text "True/False", it provides a quick toggle UI even in view mode. It renders a small form with a hidden field specifying the field name and another hidden field `new_value_override` flipping the boolean (if current value is true, `new_value_override` is "0", otherwise "1"). It then shows a button that is green and labeled "Yes" if true (or red and "No" if false). Clicking this button submits the form to the `update_field` route, toggling the value immediately. This design means booleans can be toggled without entering an edit state.
  - For all other fields (text, number, etc.): it simply displays the value in a span.
  - When a field is edited via the `?edit=<field>` query parameter, the macro now logs `[DEBUG: field → field_type]` to the Flask logger. This provides helpful context without cluttering the rendered page.

By using this macro in `detail_view.html`, the template stays cleaner and any changes to how fields are rendered (view or edit) can be made in one place. If new field types are introduced later, this macro can be extended to render them appropriately without touching the main template logic.

## Styling

The UI relies on Tailwind utility classes with a small set of custom overrides. If you want to modify the look and feel:

1. Edit `static/css/styles.css` for additional rules.
2. Adjust `static/css/overrides.css` to tweak layout editor styles or Tailwind utilities.
3. Tailwind itself is loaded via CDN in `templates/base.html`, so you can reference any Tailwind class directly in the templates.

Reload the browser after making changes to see your updates.

## License

This software is provided for evaluation and internal use only.
Modification, redistribution, or commercial deployment is prohibited without written permission.


## Acknowledgements

This project uses [Flowbite](https://github.com/themesberg/flowbite) and Flowbite Charts under the MIT License.
