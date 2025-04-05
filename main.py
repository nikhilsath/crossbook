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
        'magical', 'status', 'description', 'significance', 'notes'
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
        SELECT id, items, description, notes
        FROM items
        ORDER BY items {sort.upper()}
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template('items.html', items=rows, sort=sort, next_sort=next_sort)


@app.route('/items/<int:item_id>')
def items_detail(item_id):
    conn = sqlite3.connect('data/crossbook.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return "Item not found", 404
    
    fields = ['id', 'items', 'description', 'notes']
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

    cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return "Group not found", 404
    
    fields = ['id', 'group', 'description', 'apperance']
    group = dict(zip(fields, row)) 

    return render_template("group_detail.html", group=group)

if __name__ == "__main__":
    app.run(debug=True)
