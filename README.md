# Crossbook

Crossbook is a structured, browser-based knowledge interface for managing canon content across characters, locations, lore topics, factions, and more. It follows a clean Notion-inspired design and supports relationship mapping through join tables in SQLite.

---

## Project Summary

- Built using Flask, Jinja2, TailwindCSS, and SQLite.
- Clean and consistent UI for detail pages and sortable list views.
- Fully normalized schema with many-to-many relationships using join tables.
- Routes and templates for all major entities:
  - Characters
  - Things
  - Factions
  - Lore Topics
  - Locations
  - Content

---

## Current Status

### Implemented

- All entity tables and detail/list views
- Schema includes all needed join tables
- Relationship display via helper `fetch_related()` function
- Routes: `/characters`, `/things`, `/factions`, `/lore_topics`, `/locations`, `/content`
- Templates: detail and list views for each entity
- Fully removed all deprecated `related_*` fields from logic
- All routes validated for correct join table usage (e.g., `topic_id` for `lore_topic`)

### Not Yet Implemented

- No edit forms or update logic
- No `edit_log` columns or changelog UI
- No support for modifying relationships in the UI
- No use of `reddit_content` table yet
- No pagination or filtering

---

## Folder Structure

```
.
├── data/
│   └── crossbook.db         # SQLite database
├── templates/               # All Jinja2 templates
│   ├── *_detail.html        # One per entity
│   └── *.html               # List views
├── utils/
│   └── db_helpers.py        # Contains fetch_related()
├── main.py                  # Flask routes and logic
└── README.md
```

---

## Development Process

### Workflow Phases

1. **Phase 1 – Read-only UI** (Complete)
2. **Phase 2 – Schema Cleanup & Join Table Refactoring** (Complete)
3. **Phase 3 – Editing Support** (Planned)
4. **Phase 4 – Relationship Editing & Lookup Controls** (Planned)

---

## If Using AI – Include This In the Prompt

> You are contributing to the Crossbook project.  
> Crossbook uses Flask, SQLite, and Jinja templates with Tailwind CSS.  
> The database schema is normalized with join tables for relationships.  
> All existing `related_*` columns in the database are deprecated and must not be used.  
> For `lore_topics`, the join field is always `topic_id` (not `lore_topic_id`).  
> Join logic must use the helper `fetch_related()` already defined in `db_helpers.py`.  
> When editing templates, match the structure of `content_detail.html`.  
> Do not add new features unless explicitly requested.  
> When writing GitHub scripts, do not include comments or combine staging with directory navigation.  
> Do not assume or infer goals – only reflect what has been confirmed by the user.

---

## Next Planned Steps

1. Add `edit_log` column to all entity tables
2. Implement form-based editing for all detail views
3. Log field-level diffs in `edit_log`
4. Display collapsible edit history in the UI
5. Add UI dropdowns to manage relationships