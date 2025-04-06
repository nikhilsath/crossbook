from flask import Flask, render_template, request
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

    cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return "Character not found", 404

    fields = [
        'id', 'character', 'race', 'origin', 'allegience',
        'magical', 'status', 'description', 'significance', 'notes',
        'related_items', 'related_groups', 'related_locations',
        'related_lore', 'related_content'
    ]
    character = dict(zip(fields, row))

    return render_template("character_detail.html", character=character)


@app.route('/items')
def items():
    sort = request.args.get('sort', 'asc')
    next_sort = 'desc' if sort == 'asc' else 'asc'

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT id, object_name, description, notes
        FROM objects
        ORDER BY items {sort.upper()}
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template('items.html', items=rows, sort=sort, next_sort=next_sort)

@app.route('/items/<int:item_id>')
def items_detail(item_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, object_name, description, notes,
               related_characters, related_groups,
               related_locations, related_lore, related_content
        FROM objects WHERE id = ?
    """, (item_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return "Item not found", 404

    fields = [
        'id', 'object_name', 'description', 'notes',
        'related_characters', 'related_groups',
        'related_locations', 'related_lore', 'related_content'
    ]
    item = dict(zip(fields, row))
    
    return render_template("item_detail.html", item=item)


@app.route('/groups')
def groups():
    sort = request.args.get('sort', 'asc')
    next_sort = 'desc' if sort == 'asc' else 'asc'

    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT id, "group", descriptions, apperance
        FROM groups
        ORDER BY "group" {sort.upper()}
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template('groups.html', groups=rows, sort=sort, next_sort=next_sort)

@app.route('/groups/<int:group_id>')
def group_detail(group_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, "group", descriptions, apperance,
           related_characters, related_items, related_locations,
           related_lore_topics, related_content
    FROM groups
    WHERE id = ?
    """, (group_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return "Group not found", 404

    fields = [
        'id', 'group', 'descriptions', 'apperance',
        'related_characters', 'related_items', 'related_locations',
        'related_lore_topics', 'related_content'
    ]
    group = dict(zip(fields, row))

    return render_template("group_detail.html", group=group)


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
        SELECT id, topic, type, related_content, next_steps, notes,
               related_characters, related_groups, related_items, related_locations
        FROM lore_topics WHERE id = ?
    """, (topic_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return "Lore topic not found", 404

    fields = [
        'id', 'topic', 'type', 'related_content', 'next_steps', 'notes',
        'related_characters', 'related_groups', 'related_items', 'related_locations'
    ]
    lore_topic = dict(zip(fields, row))

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
               related_characters, related_groups,
               related_items, related_lore_topics, related_content
        FROM locations WHERE id = ?
    """, (location_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return "Location not found", 404

    fields = [
        'id', 'location', 'description',
        'related_characters', 'related_groups',
        'related_items', 'related_lore_topics', 'related_content'
    ]
    location = dict(zip(fields, row))

    # Helper: fetch name by ID from any table
    def fetch_labels(table, id_list, label_column):
        placeholders = ','.join(['?'] * len(id_list))
        # Only quote label_column if it is a reserved keyword (like "group").
        # Do NOT quote normal column names like items, topic, character — it breaks the query.
        quoted_column = f'"{label_column}"' if label_column in ["group"] else label_column
        cursor.execute(f"SELECT id, {quoted_column} FROM {table} WHERE id IN ({placeholders})", id_list)
        return {str(row[0]): row[1] for row in cursor.fetchall()}



    # Parse ID fields
    def parse_ids(field):
        return [id.strip() for id in location.get(field, '').split(',') if id.strip().isdigit()]

    # Resolve labels
    related = {
        'characters': fetch_labels("characters", parse_ids("related_characters"), "character"),
        'groups': fetch_labels("groups", parse_ids("related_groups"), "group"),
        'object_labels': fetch_labels("objects", parse_ids("related_items"), "object_name"),
        'lore_topics': fetch_labels("lore_topics", parse_ids("related_lore_topics"), "topic"),
        'content': fetch_labels("content", parse_ids("related_content"), "id")  
    }
    print("[DEBUG] Object labels from DB:", related["object_labels"])
    conn.close()
    print("Related Items:", related["object_labels"])
    print("Related items debug:", related["object_labels"])
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

    cursor.execute("""
        SELECT id, linenumber, source, chapter, content,
               notes, tags, key_lore, characters,
               paragraph_length, dialog, "dialog.1",
               related_characters, related_items,
               related_groups, related_locations, related_lore_topics
        FROM content
        WHERE id = ?
    """, (id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return "Content not found", 404

    fields = [
        'id', 'linenumber', 'source', 'chapter', 'content',
        'notes', 'tags', 'key_lore', 'characters',
        'paragraph_length', 'dialog', 'dialog.1',
        'related_characters', 'related_items',
        'related_groups', 'related_locations', 'related_lore_topics'
    ]
    content_entry = dict(zip(fields, row))

    return render_template("content_detail.html", content=content_entry)



if __name__ == "__main__":
    app.run(debug=True)
