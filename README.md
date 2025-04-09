# Crossbook

Crossbook is a structured, browser-based knowledge interface for managing canon content across characters, locations, lore topics, factions, and more. It follows a clean Notion-inspired design and supports relationship mapping through join tables in SQLite.

---

## Project Summary

- Built using Flask, Jinja2, TailwindCSS, and SQLite.
- Clean and consistent UI for detail pages and sortable list views.
- Fully normalized schema with many-to-many relationships using join tables.
- Routes and templates are dynamically generated for all major entities:
  - Characters
  - Things
  - Factions
  - Lore Topics
  - Locations
  - Content

---

## Current Status

### Implemented

- Dynamic Flask routing for all entities: `/character`, `/thing`, `/faction`, etc.
- Dynamic detail/list templates driven by schema inspection
- Inline editing with `edit_log` tracking
- Edit history toggle on detail pages
- Relationship display using `get_related_records()` helper
- Bidirectional join table support (e.g., `character_thing`, `thing_character`)
- Logging enabled for all related-fetching logic
- Redundant join tables identified and removed (e.g., `thing_character` removed in favor of `character_thing`)
- Fully read-only schema now editable from UI
- Navigation bar restored
- All known pre-rebuild features restored and verified

### Not Yet Implemented

- Add/remove relationships through UI
- Create new records via UI
- Bulk editing
- Pagination or filtering
- README regeneration pipeline

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
│   └── db_helpers.py        # Custom logic (optional)
├── main.py                  # Flask routes and logic
└── README.md
```

---

## Development Process

### Workflow Phases

1. **Phase 1 – Read-only UI** ✅ Complete
2. **Phase 2 – Inline Editing + Logging** ✅ Complete
3. **Phase 3 – Schema Cleanup + Relationship Display** ✅ Complete
4. **Phase 4 – Relationship Editing in UI** 🔜 Planned
5. **Phase 5 – Record Creation & Bulk Tools** 🔜 Planned

---

## Next Planned Steps

1. Add/remove relationship editing components
2. Implement dropdown/lookup UI for join table entries
3. Add record creation UI
4. Extend edit logs to relationship updates
5. Begin planning for packaging and install automation

