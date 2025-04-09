from flask import Flask, render_template, request, redirect, url_for
from utils.db_helpers import fetch_related
import sqlite3
import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/characters')
def characters():
    sort = request.args.get('sort', 'asc')
    next_sort = 'desc' if sort == 'asc' else 'asc'

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT id, character, race, origin, allegience
        FROM characters
        ORDER BY character {sort.upper()}
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template('characters.html', characters=rows, sort=sort, next_sort=next_sort)

@app.route('/character/<int:character_id>')
def character_detail(character_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    # Fetch main character record
    cursor.execute("""
        SELECT id, character, race, origin, allegience,
               magical, status, description, significance, notes, edit_log
        FROM characters
        WHERE id = ?
    """, (character_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return "Character not found", 404

    fields = [
        "id", "character", "race", "origin", "allegience",
        "magical", "status", "description", "significance", "notes", "edit_log"
    ]

    character = dict(zip(fields, row))

    # Fetch related records using join tables
    character['related_things'] = fetch_related(cursor, "character_things", "character_id", "things", "thing", character_id)
    character['related_factions'] = fetch_related(cursor, "character_factions", "character_id", "factions", "faction", character_id)
    character['related_locations'] = fetch_related(cursor, "character_locations", "character_id", "locations", "location", character_id)
    character['related_lore_topics'] = fetch_related(cursor, "character_lore_topics", "character_id", "lore_topics", "topic", character_id)
    character['related_content'] = fetch_related(cursor, "character_content", "character_id", "content", "content", character_id)
    conn.close()
    return render_template("character_detail.html", character=character)

@app.route('/character/<int:character_id>/update', methods=['POST'])
def update_character_field(character_id):
    from flask import redirect, request, url_for  # ✅ Required if not already at top

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    # Extract field + new value from form
    field = request.form.get('field')
    new_value = request.form.get('new_value')

    # ✅ Allow these fields to be edited inline
    allowed_fields = [
        'character', 'race', 'origin', 'allegience',
        'magical', 'status', 'description', 'significance', 'notes'
    ]
    if field not in allowed_fields:
        conn.close()
        return "Invalid field", 400

    # Get current value and existing log
    cursor.execute(f"SELECT {field}, edit_log FROM characters WHERE id = ?", (character_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return "Character not found", 404

    old_value, log = row
    log = log or ""

    # Skip update if value unchanged
    if old_value == new_value:
        conn.close()
        return redirect(url_for('character_detail', character_id=character_id))

    # Log diff
    timestamp = datetime.datetime.utcnow().isoformat()
    diff_entry = f"[{timestamp}] {field}: '{old_value}' → '{new_value}'"
    updated_log = f"{log}\n{diff_entry}".strip()

    # Update value + log
    cursor.execute(f"""
        UPDATE characters
        SET {field} = ?, edit_log = ?
        WHERE id = ?
    """, (new_value, updated_log, character_id))

    conn.commit()
    conn.close()
    return redirect(url_for('character_detail', character_id=character_id))

@app.route('/things')
def things():
    sort = request.args.get('sort', 'asc')
    next_sort = 'desc' if sort == 'asc' else 'asc'

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT id, thing, description, notes
        FROM things
        ORDER BY thing {sort.upper()}
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template('things.html', things=rows, sort=sort, next_sort=next_sort)

@app.route('/thing/<int:thing_id>')
def thing_detail(thing_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, thing, description, notes, edit_log
        FROM things
        WHERE id = ?
    """, (thing_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return "Thing not found", 404

    fields = ['id', 'thing', 'description', 'notes', 'edit_log']
    thing = dict(zip(fields, row))

    # Related entries
    thing['related_characters'] = fetch_related(cursor, "character_things", "thing_id", "characters", "character", thing_id)
    thing['related_factions'] = fetch_related(cursor, "thing_factions", "thing_id", "factions", "faction", thing_id)
    thing['related_locations'] = fetch_related(cursor, "thing_locations", "thing_id", "locations", "location", thing_id)
    thing['related_lore_topics'] = fetch_related(cursor, "thing_lore_topics", "thing_id", "lore_topics", "topic", thing_id)
    thing['related_content'] = fetch_related(cursor, "thing_content", "thing_id", "content", "content", thing_id)

    conn.close()
    return render_template("thing_detail.html", thing=thing)

@app.route("/thing/<int:thing_id>/update", methods=["POST"])
def update_thing_field(thing_id):
    field = request.form.get("field")
    new_value = request.form.get("new_value")

    if field not in {"thing", "description", "notes"}:
        return "Invalid field", 400

    conn = sqlite3.connect("data/crossbook.db")
    cursor = conn.cursor()

    # Get current value and edit log
    cursor.execute(f"SELECT {field}, edit_log FROM things WHERE id = ?", (thing_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Thing not found", 404

    old_value, current_log = row
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    log_entry = f"{timestamp} | {field} | {old_value!r} → {new_value!r}"
    updated_log = (current_log or "") + log_entry + "\n"

    cursor.execute(
        f"UPDATE things SET {field} = ?, edit_log = ? WHERE id = ?",
        (new_value, updated_log, thing_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("thing_detail", thing_id=thing_id))

@app.route('/factions')
def factions():
    sort = request.args.get('sort', 'asc')
    next_sort = 'desc' if sort == 'asc' else 'asc'

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT id, "faction", descriptions, appearance
        FROM factions
        ORDER BY "faction" {sort.upper()}
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template('factions.html', factions=rows, sort=sort, next_sort=next_sort)

@app.route('/faction/<int:faction_id>')
def faction_detail(faction_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, faction, descriptions, appearance, edit_log FROM factions WHERE id = ?", (faction_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return "Faction not found", 404

    fields = ['id', 'faction', 'descriptions', 'appearance', 'edit_log']
    faction = dict(zip(fields, row))

    faction['related_characters'] = fetch_related(cursor, "character_factions", "faction_id", "characters", "character", faction_id)
    faction['related_things'] = fetch_related(cursor, "thing_factions", "faction_id", "things", "thing", faction_id)
    faction['related_locations'] = fetch_related(cursor, "faction_locations", "faction_id", "locations", "location", faction_id)
    faction['related_lore_topics'] = fetch_related(cursor, "faction_lore_topics", "faction_id", "lore_topics", "topic", faction_id)
    faction['related_content'] = fetch_related(cursor, "faction_content", "faction_id", "content", "content", faction_id)

    conn.close()
    return render_template("faction_detail.html", faction=faction)

@app.route("/faction/<int:faction_id>/update", methods=["POST"])
def update_faction_field(faction_id):
    field = request.form.get("field")
    new_value = request.form.get("new_value")

    if field not in {"faction", "descriptions", "appearance"}:
        return "Invalid field", 400

    conn = sqlite3.connect("data/crossbook.db")
    cursor = conn.cursor()

    # Get old value + log
    cursor.execute(f"SELECT {field}, edit_log FROM factions WHERE id = ?", (faction_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Faction not found", 404

    old_value, current_log = row
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    log_entry = f"{timestamp} | {field} | {old_value!r} → {new_value!r}"
    updated_log = (current_log or "") + log_entry + "\n"

    cursor.execute(
        f"UPDATE factions SET {field} = ?, edit_log = ? WHERE id = ?",
        (new_value, updated_log, faction_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("faction_detail", faction_id=faction_id))


@app.route('/lore_topics')
def lore_topics():
    sort = request.args.get('sort', 'asc')
    next_sort = 'desc' if sort == 'asc' else 'asc'

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT id, topic, type
        FROM lore_topics
        ORDER BY topic {sort.upper()}
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template('lore_topics.html', lore_topics=rows, sort=sort, next_sort=next_sort)

@app.route('/lore_topic/<int:topic_id>')
def lore_topic_detail(topic_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, topic, type, next_steps, notes, edit_log
        FROM lore_topics
        WHERE id = ?
    """, (topic_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return "Lore Topic not found", 404

    fields = ['id', 'topic', 'type', 'next_steps', 'notes', 'edit_log']
    lore_topic = dict(zip(fields, row))

    lore_topic['related_characters'] = fetch_related(cursor, "character_lore_topics", "topic_id", "characters", "character", topic_id)
    lore_topic['related_factions']   = fetch_related(cursor, "faction_lore_topics",   "topic_id", "factions",   "faction",   topic_id)
    lore_topic['related_locations']  = fetch_related(cursor, "location_lore_topics",  "topic_id", "locations",  "location",  topic_id)
    lore_topic['related_things']     = fetch_related(cursor, "thing_lore_topics",     "topic_id", "things",     "thing",     topic_id)
    lore_topic['related_content']    = fetch_related(cursor, "content_lore_topics",   "topic_id", "content",    "content",   topic_id)

    conn.close()
    return render_template("lore_topic_detail.html", lore_topic=lore_topic)

@app.route("/lore_topic/<int:topic_id>/update", methods=["POST"])
def update_lore_topic_field(topic_id):
    field = request.form.get("field")
    new_value = request.form.get("new_value")

    if field not in {"topic", "type", "next_steps", "notes"}:
        return "Invalid field", 400

    conn = sqlite3.connect("data/crossbook.db")
    cursor = conn.cursor()

    cursor.execute(f"SELECT {field}, edit_log FROM lore_topics WHERE id = ?", (topic_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Lore topic not found", 404

    old_value, current_log = row
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    log_entry = f"{timestamp} | {field} | {old_value!r} → {new_value!r}"
    updated_log = (current_log or "") + log_entry + "\n"

    cursor.execute(
        f"UPDATE lore_topics SET {field} = ?, edit_log = ? WHERE id = ?",
        (new_value, updated_log, topic_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("lore_topic_detail", topic_id=topic_id))


@app.route('/locations')
def locations():
    sort = request.args.get('sort', 'asc')
    next_sort = 'desc' if sort == 'asc' else 'asc'

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT id, location, description
        FROM locations
        ORDER BY location {sort.upper()}
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template('locations.html', locations=rows, sort=sort, next_sort=next_sort)

@app.route('/location/<int:location_id>')
def location_detail(location_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, location, description, edit_log FROM locations WHERE id = ?", (location_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return "Location not found", 404

    fields = ['id', 'location', 'description', 'edit_log']
    location = dict(zip(fields, row))

    location['related_characters'] = fetch_related(cursor, "character_locations", "location_id", "characters", "character", location_id)
    location['related_factions'] = fetch_related(cursor, "faction_locations", "location_id", "factions", "faction", location_id)
    location['related_things'] = fetch_related(cursor, "thing_locations", "location_id", "things", "thing", location_id)
    location['related_lore_topics'] = fetch_related(cursor, "location_lore_topics", "location_id", "lore_topics", "topic", location_id)
    location['related_content'] = fetch_related(cursor, "location_content", "location_id", "content", "content", location_id)

    conn.close()
    return render_template("location_detail.html", location=location)

@app.route("/location/<int:location_id>/update", methods=["POST"])
def update_location_field(location_id):
    field = request.form.get("field")
    new_value = request.form.get("new_value")

    if field not in {"location", "description"}:
        return "Invalid field", 400

    conn = sqlite3.connect("data/crossbook.db")
    cursor = conn.cursor()

    cursor.execute(f"SELECT {field}, edit_log FROM locations WHERE id = ?", (location_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Location not found", 404

    old_value, current_log = row
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    log_entry = f"{timestamp} | {field} | {old_value!r} → {new_value!r}"
    updated_log = (current_log or "") + log_entry + "\n"

    cursor.execute(
        f"UPDATE locations SET {field} = ?, edit_log = ? WHERE id = ?",
        (new_value, updated_log, location_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("location_detail", location_id=location_id))


@app.route('/content')
def content():
    sort = request.args.get('sort', 'asc')
    next_sort = 'desc' if sort == 'asc' else 'asc'
    search_query = request.args.get('q', '').strip()
    selected_sources = request.args.getlist('source[]')

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    # Get all unique sources
    cursor.execute("SELECT DISTINCT source FROM content ORDER BY source")
    available_sources = [row[0].strip() for row in cursor.fetchall() if row[0]]

    # Start building the query
    base_query = "SELECT id, source, chapter, content FROM content WHERE 1=1"
    params = []

    # Search filter
    if search_query:
        base_query += " AND (content LIKE ? OR notes LIKE ?)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term])

    # Source filters
    if selected_sources:
        placeholders = ','.join(['?'] * len(selected_sources))
        base_query += f" AND source IN ({placeholders})"
        params.extend(selected_sources)


    base_query += f" ORDER BY id {sort.upper()} LIMIT 1000"
    cursor.execute(base_query, params)
    rows = cursor.fetchall()

    conn.close()

    return render_template(
        'content.html',
        content=rows,
        sort=sort,
        next_sort=next_sort,
        selected_sources=selected_sources,
        available_sources=available_sources
    )

@app.route('/content/<int:id>')
def content_detail(id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    # Fetch core content row
    cursor.execute("""
        SELECT id, linenumber, source, chapter, content,
               notes, tags, key_lore, characters,
               paragraph_length, dialog, "dialog.1", edit_log
        FROM content
        WHERE id = ?
    """, (id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return "Content not found", 404

    fields = [
        'id', 'linenumber', 'source', 'chapter', 'content',
        'notes', 'tags', 'key_lore', 'characters',
        'paragraph_length', 'dialog', 'dialog.1', 'edit_log'
    ]
    content_entry = dict(zip(fields, row))

    # Add related entries using fetch_related()
    content_entry['related_characters'] = fetch_related(cursor, "content_characters", "content_id", "characters", "character", id)
    content_entry['related_things']     = fetch_related(cursor, "content_things",     "content_id", "things",     "thing",     id)
    content_entry['related_factions']   = fetch_related(cursor, "content_factions",   "content_id", "factions",   "faction",   id)
    content_entry['related_locations']  = fetch_related(cursor, "content_locations",  "content_id", "locations",  "location",  id)
    content_entry['related_lore_topics']= fetch_related(cursor, "content_lore_topics","content_id", "lore_topics","topic",     id)

    conn.close()
    return render_template("content_detail.html", content=content_entry)

@app.route('/content/<int:id>/update', methods=['POST'])
def update_content_field(id):
    field = request.form.get('field')
    new_value = request.form.get('new_value')

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    # Step 1: Get old value and current log
    cursor.execute(f"SELECT {field}, edit_log FROM content WHERE id = ?", (id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Content not found", 404

    old_value, current_log = row

    # Step 2: Build new log entry
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    log_entry = f"{timestamp} | {field} | {old_value!r} → {new_value!r}"
    updated_log = (current_log or "") + log_entry + "\n"

    # Step 3: Save updated field and edit log
    cursor.execute(
        f"UPDATE content SET {field} = ?, edit_log = ? WHERE id = ?",
        (new_value, updated_log, id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('content_detail', id=id))


if __name__ == "__main__":
    app.run(debug=True)
