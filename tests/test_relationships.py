import sqlite3
from db.relationships import get_related_records


def test_add_get_remove_relationship(client, db_path):
    # ensure starting state has no character 1 -> location 1 relationship
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "DELETE FROM relationships WHERE table_a=? AND id_a=? AND table_b=? AND id_b=?",
            ('character', 1, 'location', 1),
        )
        conn.commit()

    resp = client.post(
        '/relationship',
        json={
            'table_a': 'character',
            'id_a': 1,
            'table_b': 'location',
            'id_b': 1,
            'action': 'add',
        },
    )
    assert resp.status_code == 200
    assert resp.get_json()['success']

    related = get_related_records('character', 1)
    assert 'location' in related
    assert any(item['id'] == 1 for item in related['location']['items'])

    resp = client.post(
        '/relationship',
        json={
            'table_a': 'character',
            'id_a': 1,
            'table_b': 'location',
            'id_b': 1,
            'action': 'remove',
        },
    )
    assert resp.status_code == 200
    assert resp.get_json()['success']

    related = get_related_records('character', 1)
    assert not related.get('location') or not any(
        item['id'] == 1 for item in related['location']['items']
    )


def test_edit_history_for_relationship_changes(client, db_path):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "DELETE FROM relationships WHERE table_a=? AND id_a=? AND table_b=? AND id_b=?",
            ("character", 1, "location", 1),
        )
        conn.execute(
            "DELETE FROM edit_history WHERE table_name IN ('character','location') AND record_id=1 AND field_name LIKE 'relation_%'"
        )
        max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM edit_history").fetchone()[0]
        conn.commit()

    resp = client.post(
        "/relationship",
        json={
            "table_a": "character",
            "id_a": 1,
            "table_b": "location",
            "id_b": 1,
            "action": "add",
        },
    )
    assert resp.status_code == 200
    assert resp.get_json()["success"]

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT table_name, record_id, field_name, old_value, new_value FROM edit_history WHERE id > ? ORDER BY id",
            (max_id,),
        ).fetchall()
        assert len(rows) == 2
        assert ("character", 1, "relation_location", None, "1") in rows
        assert ("location", 1, "relation_character", None, "1") in rows
        max_id = conn.execute("SELECT MAX(id) FROM edit_history").fetchone()[0]

    resp = client.post(
        "/relationship",
        json={
            "table_a": "character",
            "id_a": 1,
            "table_b": "location",
            "id_b": 1,
            "action": "remove",
        },
    )
    assert resp.status_code == 200
    assert resp.get_json()["success"]

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT table_name, record_id, field_name, old_value, new_value FROM edit_history WHERE id > ? ORDER BY id",
            (max_id,),
        ).fetchall()
        assert len(rows) == 2
        assert ("character", 1, "relation_location", "1", None) in rows
        assert ("location", 1, "relation_character", "1", None) in rows

