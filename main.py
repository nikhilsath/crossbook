from flask import Flask, render_template, request
from utils.db_helpers import fetch_related
import sqlite3


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
               magical, status, description, significance, notes
        FROM characters
        WHERE id = ?
    """, (character_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return "Character not found", 404

    fields = [
        'id', 'character', 'race', 'origin', 'allegience',
        'magical', 'status', 'description', 'significance', 'notes'
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
    
@app.route('/things/<int:thing_id>')
def thing_detail(thing_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    # Fetch main thing record
    cursor.execute("""
        SELECT id, thing, description, notes
        FROM things
        WHERE id = ?
    """, (thing_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return "Thing not found", 404

    fields = ['id', 'thing', 'description', 'notes']
    thing = dict(zip(fields, row))

    # Fetch related records using join tables
    thing['related_characters']    = fetch_related(cursor, "character_things",    "thing_id", "characters",    "character", thing_id)
    thing['related_factions']      = fetch_related(cursor, "faction_things",      "thing_id", "factions",      "faction",   thing_id)
    thing['related_locations']     = fetch_related(cursor, "location_things",     "thing_id", "locations",     "location",  thing_id)
    thing['related_lore_topics']   = fetch_related(cursor, "thing_lore_topics",   "thing_id", "lore_topics",   "topic",     thing_id)
    thing['related_content']       = fetch_related(cursor, "content_things",      "thing_id", "content",       "content",   thing_id)

    conn.close()
    return render_template("thing_detail.html", thing=thing)


@app.route('/factions')
def factions():
    sort = request.args.get('sort', 'asc')
    next_sort = 'desc' if sort == 'asc' else 'asc'

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT id, "faction", descriptions, apperance
        FROM factions
        ORDER BY "faction" {sort.upper()}
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template('factions.html', factions=rows, sort=sort, next_sort=next_sort)

@app.route('/factions/<int:faction_id>')
def faction_detail(faction_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, faction, descriptions, apperance
        FROM factions
        WHERE id = ?
    """, (faction_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return "Faction not found", 404

    fields = ['id', 'faction', 'descriptions', 'appearance']
    faction = dict(zip(fields, row))

    faction['related_characters'] = fetch_related(cursor, "character_factions", "faction_id", "characters", "character", faction_id)
    faction['related_things']     = fetch_related(cursor, "faction_things",     "faction_id", "things",     "thing",     faction_id)
    faction['related_locations']  = fetch_related(cursor, "faction_locations",  "faction_id", "locations",  "location",  faction_id)
    faction['related_lore_topics']= fetch_related(cursor, "faction_lore_topics","faction_id", "lore_topics","topic",     faction_id)
    faction['related_content']    = fetch_related(cursor, "faction_content",    "faction_id", "content",    "content",   faction_id)

    conn.close()
    return render_template("faction_detail.html", faction=faction)


@app.route('/lore_topics')
def lore_topics():
    sort = request.args.get('sort', 'asc')
    next_sort = 'desc' if sort == 'asc' else 'asc'

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT id, topic, type, related_content
        FROM lore_topics
        ORDER BY topic {sort.upper()}
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template('lore_topics.html', lore_topics=rows, sort=sort, next_sort=next_sort)

@app.route('/lore_topics/<int:topic_id>')
def lore_topic_detail(topic_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, topic, type, next_steps, notes
        FROM lore_topics
        WHERE id = ?
    """, (topic_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return "Lore Topic not found", 404

    fields = ['id', 'topic', 'type', 'next_steps', 'notes']
    lore_topic = dict(zip(fields, row))

    lore_topic['related_characters'] = fetch_related(cursor, "character_lore_topics", "topic_id", "characters", "character", topic_id)
    lore_topic['related_factions']   = fetch_related(cursor, "faction_lore_topics",   "topic_id", "factions",   "faction",   topic_id)
    lore_topic['related_locations']  = fetch_related(cursor, "location_lore_topics",  "topic_id", "locations",  "location",  topic_id)
    lore_topic['related_things']     = fetch_related(cursor, "thing_lore_topics",     "topic_id", "things",     "thing",     topic_id)
    lore_topic['related_content']    = fetch_related(cursor, "content_lore_topics",   "topic_id", "content",    "content",   topic_id)

    conn.close()
    return render_template("lore_topic_detail.html", lore_topic=lore_topic)


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

@app.route('/locations/<int:location_id>')
def location_detail(location_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    # Main record
    cursor.execute("""
        SELECT id, location, description,
               related_characters, related_factions,
               related_things, related_lore_topics, related_content
        FROM locations WHERE id = ?
    """, (location_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return "Location not found", 404

    fields = [
        'id', 'location', 'description',
        'related_characters', 'related_factions',
        'related_things', 'related_lore_topics', 'related_content'
    ]
    location = dict(zip(fields, row))

    # Helper: fetch name by ID from any table
    def fetch_labels(table, id_list, label_column):
        placeholders = ','.join(['?'] * len(id_list))
        # Only quote label_column if it is a reserved keyword (like "faction").
        # Do NOT quote normal column names like things, topic, character — it breaks the query.
        quoted_column = f'"{label_column}"' if label_column in ["faction"] else label_column
        cursor.execute(f"SELECT id, {quoted_column} FROM {table} WHERE id IN ({placeholders})", id_list)
        return {str(row[0]): row[1] for row in cursor.fetchall()}



    # Parse ID fields
    def parse_ids(field):
        return [id.strip() for id in location.get(field, '').split(',') if id.strip().isdigit()]

    # Resolve labels
    related = {
        'characters': fetch_labels("characters", parse_ids("related_characters"), "character"),
        'factions': fetch_labels("factions", parse_ids("related_factions"), "faction"),
        'thing_labels': fetch_labels("things", parse_ids("related_things"), "thing"),
        'lore_topics': fetch_labels("lore_topics", parse_ids("related_lore_topics"), "topic"),
        'content': fetch_labels("content", parse_ids("related_content"), "id")  
    }
    print("[DEBUG] thing labels from DB:", related["thing_labels"])
    conn.close()
    print("Related things:", related["thing_labels"])
    print("Related things debug:", related["thing_labels"])
    return render_template("location_detail.html", location=location, related=related)



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
               paragraph_length, dialog, "dialog.1"
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
        'paragraph_length', 'dialog', 'dialog.1'
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



if __name__ == "__main__":
    app.run(debug=True)
