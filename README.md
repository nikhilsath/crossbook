# 📘 Crossbook

Crossbook/
├── data/
│   └── crossbook.db            # Main SQLite3 database
├── templates/
│   ├── base.html               # Common layout with nav bar
│   ├── index.html              # Home page
│   ├── characters.html         # List of characters
│   ├── character_detail.html   # Detail view for characters
│   ├── items.html              # List of items
│   ├── item_detail.html        # Detail view for items
│   ├── groups.html             # List of groups
│   ├── group_detail.html       # Detail view for groups
│   ├── locations.html          # List of locations
│   ├── location_detail.html    # Detail view for locations
│   ├── lore_topics.html        # List of lore topics
│   └── lore_topic_detail.html  # Detail view for lore topics
└── main.py     

**Crossbook** is a lightweight, browser-based CMS designed to manage canon content from a fantasy universe, starting with read-only access and a clean UI for navigating characters, items, groups, locations, and lore topics.

---

## 🚀 Features (Phase 1 Complete)

### ✅ Foundation – Read-Only UI
- 🌐 **Homepage Navigation**
  - Landing page with grid-style navigation to Characters, Items, Groups, Locations, and Lore Topics.
  - TailwindCSS-powered UI.

- 📋 **List Views**
  - Sortable tables for each category (e.g., sort characters by name).
  - Toggleable ascending/descending sort for the primary column.
  - Navigation bar included on all list views.

- 🧾 **Detail Views**
  - Dedicated pages for each entry using a unique `id`.
  - Displays key fields for each table.
  - Placeholder section for related content.
  - Clean formatting and error handling for missing entries.

---

## 🗂️ Tables Currently Supported

All tables include a newly added `id` (INTEGER PRIMARY KEY AUTOINCREMENT):

- **Characters**
  - Fields: `character`, `race`, `origin`, `allegience`, `magical`, `status`, `description`, `significance`, `notes`

- **Items**
  - Fields: `items`, `description`, `notes`

- **Groups**
  - Fields: `group`, `descriptions`, `apperance`

- **Locations**
  - Fields: `name`, `location`, `significance`, `notes`

- **Lore Topics**
  - Fields: `topic`, `type`, `related_content`, `next_steps`, `notes`

---

## 🧱 Tech Stack

- **Backend:** Flask (Python 3)
- **Frontend:** HTML + Jinja + TailwindCSS
- **Database:** SQLite3 (`crossbook.db`)

---

## 🧪 Setup & Run

### 1. Clone & Setup

```bash
git clone <your_repo_url>
cd Crossbook
python3 -m venv venv
source venv/bin/activate
pip install flask

2. Run the App
bash
Copy
Edit
python main.py
Then visit http://localhost:5000 in your browser.

