
# Crossbook

Crossbook is a structured, browser-based knowledge interface for managing content and its related metadata. It provides an easy way to organize and cross-reference entities (for example: books or chapters of content, and related characters, locations, factions, etc.) along with their interrelationships. The application features a clean design and uses a normalized SQLite database (with join tables) to map many-to-many relationships between entities.

## Project Summary

* **Tech Stack:** Python 3.x, Flask (web framework), Jinja2 (templating), Tailwind CSS (styling via CDN), SQLite (relational database). JavaScript libraries include InteractJS for drag-and-drop layout editing and custom scripts under `static/js/` for validation and UI behavior.
* **Dynamic UI Generation:** Automated list and detail views based on database schema introspection.
* **CSV Import & Validation:** Import CSV files with field-matching dropdowns and instant client-side validation (`static/imports/match_logic.js`) plus server-side verification (`imports.import_csv.parse_csv`).
* **Search & Visibility Controls:** Text-based search filters and toggleable columns for list views, with filter controls implemented via Jinja macros.
* **Navigation:** Centralized in `templates/base.html`, providing consistent header navigation and action buttons across all entity pages.
* **Database Layer:** Abstracted in the `db/` package (`database.py`, `schema.py`, `records.py`, `relationships.py`) for connection handling, schema loading, CRUD operations, and relationship management.
* **Session Management & Logging:** Utilizes Flask session for stateful workflows and Python’s `logging` module for error and activity tracking.

### Future Cloud Migration

* **Move from SQLite to a managed cloud database** (e.g. PostgreSQL) to support scalability and multi-instance deployments.
* **Integrate a task queue** (e.g. Google Cloud Tasks) for any long-running or background jobs (CSV import, relationship syncing, etc.).
* **Adjust configuration and deployment** to read credentials and connection strings from environment variables or secret stores.

## Current Status

* **CSV Import & Field Mapping (In Progress):** refining dropdown matching logic, enhancing client/server validation feedback, and improving import performance.
* **Detail View Resizing & Layout Editor (In Progress):** improving drag-and-drop interactions, grid responsiveness across screen sizes, and persisting custom layouts immediately on change.

## Implemented Features

* **List View with Search:** Each entity list page allows filtering records by text-based fields with a search box (`list_view.html`).
* **Column Visibility:** Columns can be shown or hidden on the fly using the **Columns** dropdown (`column_visibility.js`).
* **Detail View & Inline Edit:** Displays all fields on the detail page with inline editing via text input, date picker, checkbox, or rich text editor; edits are saved via POST and appended to the edit log.
* **Relationship Management:** Displays related records and allows adding/removing relationships through a modal interface (+ to add, ✖ to remove), using AJAX to update join tables dynamically.
* **Rich Text Support:** Textarea fields support basic formatting with buttons: Bold, Italic, Underline, Link.
* **Edit History:** Tracks each record’s modifications in an `edit_log`, viewable via an expandable history section.
* **Navigation Bar:** A consistent top navigation (`base.html`) links to Home and all core entity sections.
* **Supported Field Types:** text, number, date, select, multi-select, foreign-key, boolean, and textarea, each rendered with the appropriate input control.
* **Filter Macros:** Reusable Jinja macros for boolean, select, text, and multi-select filters (`templates/macros/filter_controls.html`).
* **CSV Import (In Progress):** Validation logic (dropdown matching and error feedback) implemented; full import processing and record creation still under development.

## Project Structure

```text
/
├── README.md                        # Project documentation and setup instructions
├── main.py                          # Application entrypoint; Flask app setup and routes
├── requirements.txt                 # Python dependencies
├── db/                              # Database layer modules
│   ├── database.py                  # Connection and session management
│   ├── schema.py                    # Schema introspection and migrations
│   ├── records.py                   # CRUD operations
│   ├── relationships.py             # Many-to-many join helpers
│   ├── validation.py                # Field and data validation logic
│   └── edit_fields.py               # Field schema editing utilities
├── imports/                         # Import and background task definitions
│   ├── import_csv.py                # CSV parsing, validation, and import routines
│   └── tasks.py                     # Background job definitions (e.g., Huey tasks)
├── static/                          # Front-end assets
│   ├── css/
│   │   ├── overrides.css            # Tailwind override styles
│   │   └── styles.css               # Additional global styles
│   ├── js/
│   │   ├── column_visibility.js     # Column toggle logic
│   │   ├── editor.js                # Rich-text editor integration
│   │   ├── edit_fields.js           # Client-side field schema editing
│   │   ├── filter_visibility.js     # Show/hide filter controls
│   │   ├── layout_editor.js         # Drag/drop & layout persistence
│   │   ├── relations.js             # AJAX for add/remove relationships
│   │   └── tag_selector.js          # Multi-select tag UI helper
│   └── imports/
│       └── match_logic.js           # Client-side CSV validation logic
├── templates/                       # Jinja2 view templates
│   ├── base.html
│   ├── index.html
│   ├── new_record.html
│   ├── import_view.html
│   ├── list_view.html
│   ├── detail_view.html
│   └── macros/
│       ├── fields.html              # Field rendering macros
│       ├── filter_controls.html     # Filter UI macros
│       └── tag_selector.html        # Multi-select tag macros
└── data/                            # Runtime and uploaded data
    ├── crossbook.db                # Main application SQLite database
    ├── huey.db                     # Task queue persistence database
    └── uploads/                    # Imported CSV file storage
```

## Application Architecture and Code Overview

* **Routing & Views:** Defined in `main.py` using Flask decorators; routes handle list, detail, new record, import, and error pages. A context processor (`@app.context_processor`) injects the `field_schema`—the in-memory representation of all table fields, types, options, and layout—into all templates and front-end scripts for dynamic form generation and validation. Error handlers (e.g., `@app.errorhandler(404)`) and `abort()` calls manage invalid requests.

* **Configuration & Environment:** Dependencies listed in `requirements.txt`. Application configuration loads from environment variables or a `.env` file via `python-dotenv`. A `config.py` module organizes settings for development, testing, and production.

* **Database Layer:** Uses Python’s built-in `sqlite3` in `db/database.py` for connection management. Schema introspection and migrations occur in `db/schema.py`. CRUD operations reside in `db/records.py`; many-to-many join logic in `db/relationships.py`. Validation rules live in `db/validation.py`, and field schema editing utilities in `db/edit_fields.py`.

* **Validation & Import Pipeline:** CSV parsing and server-side validation in `imports/import_csv.py`, complemented by client-side matching logic in `static/imports/match_logic.js`. Field matching errors are surfaced back to the user before final import.

* **Background Tasks:** Long-running jobs (e.g., CSV row processing) are defined as Huey tasks in `imports/tasks.py`. Tasks are queued and executed asynchronously to keep request-response cycles performant.

* **Frontend Interaction:** Dynamic behaviors powered by JavaScript modules in `static/js/`:

  * `layout_editor.js` for drag-and-drop and grid persistence
  * `column_visibility.js` to toggle table columns
  * `relations.js` for AJAX-based add/remove relationships
  * `filter_visibility.js` for showing/hiding filter controls
  * `tag_selector.js` (multi-select dropdown UI)
  * `edit_fields.js` for client-side schema and field editing
  * `editor.js` for rich-text formatting integration

* **Static Assets & Styling:** Global styles in `static/css/styles.css`, with Tailwind overrides in `static/css/overrides.css`.

* **Templating & Macros:** Jinja2 templates in `templates/` include `base.html`, `index.html`, `new_record.html`, `import_view.html`, `list_view.html`, and `detail_view.html`. Reusable macros live in `templates/macros/fields.html`, `filter_controls.html`, and `tag_selector.html`.

* **Logging & Monitoring:** Basic logging configured via Python’s `logging` module in `main.py`. Logs capture errors, import operations, and user actions.

* **Data Directory:** Runtime files under `data/`: `crossbook.db` (primary database), `huey.db` (task queue store), and `uploads/` for storing imported CSV files.






### **Main Application – `main.py`**

This is the core of the Flask application. It defines the web routes, handles database interactions, and implements the logic for listing records, showing details, editing fields, and managing relationships. The application uses a single Flask app instance and a single SQLite database file.

**Global configuration and variables in `main.py`:**

- **Flask App Initialization:** The Flask app is created with `static_url_path='/static'` so that files in the `static/` directory are served at the `/static` URL path.
- **`DB_PATH`:** Path to the SQLite database file, set to `data/crossbook.db`. (This is currently hardcoded; the database must reside at this path relative to the app.)
- **`CORE_TABLES`:** A list of the primary entity tables in the database: `["character", "thing", "location", "faction", "topic", "content"]`. This list is used to validate route parameters and to build navigation links. *(If new core tables are added to the database, this list must be updated in code for the app to recognize them.)*
- **`FIELD_SCHEMA`:** A global dictionary that will hold the schema definition for fields of each table. It’s populated at startup by reading the `field_schema` table from the database. The structure is: `FIELD_SCHEMA = { table_name: { field_name: field_type, ... }, ... }`. This lets the templates and logic know how to treat each field (e.g., as text, number, boolean, etc., and whether to render it or hide it).
- **`field_options`:** A field_options column in the field_schema table contains a JSON-encoded list of options for select fields (e.g., ["Elf", "Human"]).
- These options are not loaded into FIELD_SCHEMA.
- Instead, the app uses a dynamic template-accessible helper:


### Functions in `main.py`:

The following functions encapsulate the application logic:

| Function & Signature                          | Purpose                                                             |
|-----------------------------------------------|----------------------------------------------------------------------|
| `get_connection()`                            | Returns a new connection to the SQLite database at `DB_PATH`. This is a small helper to avoid repeating the connect call. |
| `load_field_schema()`                         | Queries the database for all defined fields (table `field_schema`) and loads the `FIELD_SCHEMA` global. It builds a nested dict of `{table: {field: field_type}}` for use in templates and validation. This is called once at startup to initialize the schema info. |
| `get_field_options(table, field)`             | Retrieves a list of options for a given `select` field from the `field_schema` table. Returns a list parsed from the `field_options` column (assumed to be valid JSON), or an empty list if none is present or if parsing fails. Used at render time only inside templates that need it. |
| `get_all_records(table, search=None)`         | Retrieves up to 1000 records from the specified table. If a `search` string is provided, it filters the results to those where any text-like field contains the search substring (case-insensitive). Only fields of type *text, textarea, select,* or *multi select* are searched. Returns a list of records as dictionaries (each dict maps field names to values). Logs the SQL query and catches any errors (returning an empty list on error). |
| `get_record_by_id(table, record_id)`          | Fetches a single record by its ID from the specified table. Returns a dictionary of field names to values for that record, or `None` if not found. This uses `sqlite3.Row`-like logic by first retrieving the table’s column names (via `PRAGMA table_info`) and then zipping with the fetched row tuple. |
| `get_related_records(source_table, record_id)` | Gathers related records for a given record (by looking at join tables). It scans the database’s table names for any join table involving `source_table`. For each join table found (e.g., `character_location` or `location_character`), it figures out the *other* table and then selects the related records from that table. Returns a dictionary where each key is a related table name and each value is an object with a human-readable label and a list of related items (each item has an `id` and a `name`). Only the first field of the related table (assumed to be the name/title field, often the same name as the table) is used as the display name. Any errors in querying a particular join table are caught and simply skipped (so a broken or missing join table will not crash the whole function). |
| `home()`                                      | **Route:** GET `/` – Renders the **home page** (`index.html`). This page is a simple overview with links to each section of the site. |
| `list_view(table)`                            | **Route:** GET `/<table>` – Renders the **list view page** for a given entity type. If the `<table>` parameter is not one of the `CORE_TABLES`, it returns 404. Otherwise, it uses `FIELD_SCHEMA` to determine which fields to display (all except those marked hidden or internal), gets an optional `search` query param from the request to filter results, and calls `get_all_records`. It then renders `list_view.html`, passing in the table name, the list of fields, the list of record dicts, and the `request` object (for access to query params in the template). |
| `inject_field_schema()`                       | **Context Processor:** Injects the `FIELD_SCHEMA` global and the `get_field_options` helper function into all template contexts. This makes `field_schema[...]` and `get_field_options(table, field)` available to macros and templates. Templates use `get_field_options` to dynamically render dropdowns for fields of type `select` using options defined in the `field_schema` table. |
| `detail_view(table, record_id)`               | **Route:** GET `/<table>/<int:record_id>` – Renders the **detail view page** for a single record. If the table is not in `CORE_TABLES`, or the record with that ID doesn’t exist, it aborts with 404. Otherwise, it fetches the record via `get_record_by_id` and all related records via `get_related_records`. It then renders `detail_view.html`, providing the table name, the record dict, and the related records dict to the template. |
| `update_field(table, record_id)`              | **Route:** POST `/<table>/<int:record_id>/update` – Handles inline edits from the detail page. This is called when a user submits a field edit form. It first ensures the table is valid and the record exists. It then reads `field` (the field name to update) and the new value from the form data (`new_value` or `new_value_override`). Certain fields are protected: attempting to edit the primary `id` or the `edit_log` directly will result in a 403 Forbidden. For other fields, it determines the expected data type from `FIELD_SCHEMA` and **coerces** the input accordingly: booleans are converted to "1" or "0", numbers to int (default 0 if parse fails), and all other types are treated as strings. It then executes an `UPDATE ... SET field = ?` query to save the new value. If the value changed, it appends a timestamped entry describing the change to the record’s `edit_log` field (this is done by concatenating text). After updating, it commits the transaction and redirects the user back to the detail view page for that record. |
| `manage_relationship()`                       | **Route:** POST `/relationship` – AJAX endpoint for adding or removing a relationship (join table entry) between two records. It expects a JSON payload with `table_a`, `id_a`, `table_b`, `id_b`, and an `action` ("add" or "remove"). The two table names are sorted alphabetically to determine the join table name (e.g., `character` + `thing` -> join table **character_thing**). Depending on the action, it either inserts a new row (with the two IDs) into the join table or deletes the matching row. It uses `INSERT OR IGNORE` for adds (to avoid duplicates) and a straightforward DELETE for removal. On success, returns JSON `{"success": True}` (HTTP 200). If the join table doesn’t exist or another database error occurs, it returns an error message JSON with status 500. If required fields are missing or an invalid action is given, it returns a 400 error. *(Note: This function uses a direct sqlite3 connection separate from `get_connection()` for convenience and does not explicitly reuse the app’s global connection helper.)* |



All routes and functions above are actively used by the application (there is no dead code in `main.py`). The file concludes by calling `load_field_schema()` and then `app.run(debug=True)` if executed directly, to initialize the schema and start the development server.

### **Front-End Scripts – `static/js/`

#### 📄 `editor.js`

**Purpose:** Initializes rich text formatting controls for `textarea` fields rendered as contenteditable HTML blocks.

**Key Features:**
- Hooks up toolbar buttons (`B`, `I`, `U`) to `execCommand(...)`
- Keeps a hidden `<input>` in sync with the editor’s `.innerHTML`
- Uses `initRichTextEditor(field)` called inline by the template

**How it’s used in the app:** This module is imported in `fields.html` whenever a `textarea` field is edited.
**

The front-end JavaScript files enhance the user experience by adding interactivity for column toggling and relationship management. They are written as modular ES6 modules and are imported in the templates where needed.

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

As of April 2025, `relations.js` also includes `submitMultiSelectAuto(form)` to support autosaving changes from `multi_select` fields, and logic to automatically close dropdowns when clicking outside them.

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
- **Navigation Bar:** A responsive `<nav>` bar at the top contains links to Home and each core section. These links are currently hardcoded to the known sections: Home (`/`), Content, Characters, Things, Factions, Locations, Lore Topics (each link goes to the list view of the respective table). The link labels are prettified (e.g., `"Lore Topics"` for `topic`). *(In the current implementation, this nav does not auto-update if `CORE_TABLES` changes; it must be edited manually to add new sections.)*
- **Content Block:** Uses Jinja `{% block content %}{% endblock %}` to define where child templates insert their page-specific content. Similarly, a `{% block title %}` sets the `<title>` tag for each page (so pages can specify a custom title, like “Characters List” or “Character 5”). The base provides a padded container `<div class="p-6">` around the content block for consistent spacing.
- **Global Context:** Thanks to the `inject_field_schema` context processor, every template extending base.html automatically has access to `field_schema` (the schema dict) as well as other Flask globals like `request`. This base does not itself display dynamic data (aside from the nav links), but it provides the framework within which other templates render their content.

#### 📄 **`index.html`**

**Purpose:** Home page, providing a quick entry point to each section of the application.

**Content:** The index extends `base.html` and fills the content block with a title and a grid of cards linking to each entity’s list page. Each card has:
- A heading (e.g., "Characters", "Locations") and 
- A brief description or tagline (e.g., "View all known characters in Alagaesia" for Characters, or "Important places throughout the land" for Locations). These descriptions are specific to the example dataset (Alagaësia lore) and can be adjusted for other use cases.
- The cards are wrapped in anchor `<a>` tags linking to the respective list view (e.g., `/character`).

This page is static in content (no dynamic looping; the sections are explicitly written out for the core tables).

#### 📄 **`list_view.html`**

**Purpose:** Generic list page template for any entity table. It displays a table of records (with columns as fields) and provides search and column visibility controls.

**Key Elements:**

- **Header and Title:** Shows the capitalized table name plus "List". For example, if viewing the `character` table, it will display "Characters" as a header.
- **Search Form:** At the top of the list, there's a search input and submit button. It preserves the current search query in the input field (using `request.args.get('search', '')`). Submitting the form reloads the page with a query parameter to filter results (handled in the route logic).
- **Column Visibility Dropdown:** A button labeled "Columns" toggles a checklist of all fields. By default, each field (except internal ones starting with `_`) is listed with a checked checkbox. This uses the structure defined in the template to generate inputs with class `.column-toggle` and value equal to the field name. The `column_visibility.js` script (included at the bottom of this template) controls the show/hide behavior based on these checkboxes. This feature lets users hide columns that they aren't interested in to reduce clutter.
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
  - If yes, it outputs a `<form>` with the appropriate input for that field type, pre-filled with the current value, and Save/Cancel controls. For example:
    - Text fields -> a simple text input.
    - Number fields -> a number input.
    - Date fields -> an HTML date picker.
    - Textarea (long text) -> a rich text editor area (actually an editable `<div>` with formatting toolbar, plus a hidden field to capture the formatted content as HTML).
    - Boolean fields -> a toggle checkbox input.
    - `multi_select` fields now render as searchable dropdowns with checkboxes and tag-style badges for selected values. Users can filter options live, deselect tags with ✖, and all changes autosave automatically. A Tailwind-styled dropdown appears inline with live filtering and closing behavior.
  - If the field is **not** in edit mode, the macro will display the value in a read-only format:
    - For textarea (HTML content) fields: it wraps the content in a `<div class="prose">` to apply typographic styling to the HTML content (and uses `|safe` to allow rendering HTML).
    - For boolean fields: it shows a colored badge with "Yes" or "No". Actually, for booleans, the macro provides a special case: even when not explicitly in edit mode, the boolean is shown as a clickable form (the colored badge is a submit button that immediately flips the boolean value). This design allows one-click toggling of true/false fields without needing the separate edit step.
    - For foreign key fields: currently just displays the value in italic blue text (as a visual cue that it’s a reference) – but it’s not a link. This is a placeholder for future functionality.
    - All other fields: displayed as plain text.
    - In all non-edit cases (except booleans which have their own form), an edit ✏️ icon link is provided next to the value. Clicking this link reloads the page with the `?edit=<fieldname>` query parameter, thus switching that field into edit mode.
- **Edit Log:** If the `record.edit_log` field is present and not empty, the template shows an **Edit History** section below the fields table. This is implemented with a `<details>` element that can be expanded to reveal the full log (each entry on a new line, preserved with whitespace via `<pre>`). This allows developers to see all past changes to the record’s fields.
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
    - **textarea:** It creates a rich text editor interface. Instead of a plain `<textarea>`, it uses a contenteditable `<div>` (with id `editor_<field>`), and a hidden input `new_value`. It also injects a small toolbar with buttons (Bold, Italic, Underline, Link) that use `document.execCommand` to format the content in the editable div. A script is included in this macro to handle the toolbar actions and to copy the edited HTML into the hidden input whenever changes occur. The current value (which is HTML) is inserted into the editable div for editing. This allows the user to format text and the formatted HTML is sent on form submit.
    - **boolean:** Renders a checkbox input (styled as a toggle switch via CSS classes). It’s checked if the current value is truthy ( "1", 1, or True). This lets the user change the boolean value. (Note: in edit mode, this is a single checkbox inside the form; in view mode, booleans are handled differently as described below).
    - **number:** Renders a numeric input (`<input type="number">`) with the current value.
    - **date:** Renders a date picker (`<input type="date">`) with the current value.
    - **default (text):** Renders a basic text input for any other field type (e.g., simple text or unrecognized types).
  - After the input, a "Save" submit button and a "Cancel" link are provided. The Cancel link leads back to the detail view of the record (without the `edit` param), effectively canceling edit mode.
- If the field is **not** being edited (normal display mode):
  - For **textarea** fields (which contain HTML content), it wraps the value in a `<div class="prose">` and marks it safe, so the HTML formatting is rendered. This nicely displays paragraphs, links, etc., with Tailwind’s typography styles.
  - For **select/multi_select** (if they were to be used), and **date** fields: it simply displays the value in a span. (Currently select fields have no special behavior because support is not implemented yet, so they just show whatever value is stored.)
  - For **foreign_key** fields: displays the value in a span with italic, blue styling as a hint that it’s a reference. (This is a placeholder; ideally it would be a link to that related record’s page, but that requires additional context which is not yet provided to the template.)
  - For **boolean** fields: Instead of a plain text "True/False", it provides a quick toggle UI even in view mode. It renders a small form with a hidden field specifying the field name and another hidden field `new_value_override` flipping the boolean (if current value is true, `new_value_override` is "0", otherwise "1"). It then shows a button that is green and labeled "Yes" if true (or red and "No" if false). Clicking this button submits the form to the `update_field` route, toggling the value immediately. This design means booleans can be toggled without entering an edit state.
  - For all other fields (text, number, etc.): it simply displays the value in a span.
  - In addition, for any non-boolean field in view mode, an edit icon link (✏️) is shown after the value. Clicking this link reloads the page with the `?edit=<field>` parameter to activate the edit form (as described above).
- The macro also prints a small debug line in edit mode (`[DEBUG: field → field_type]` in gray, small text) to show the field name and type. This is helpful for developers to see what type the system thinks the field is. (This line could be removed or hidden in a production setting if desired.)

By using this macro in `detail_view.html`, the template stays cleaner and any changes to how fields are rendered (view or edit) can be made in one place. For example, when select fields are implemented, the macro can be updated to handle `field_type == "select"` differently (perhaps render a dropdown with options) without having to touch the main template logic.
