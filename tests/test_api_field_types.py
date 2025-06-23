EXPECTED_KEYS = {
    "sql_type",
    "default_width",
    "default_height",
    "numeric",
    "allows_options",
    "allows_foreign_key",
    "searchable",
    "allows_multiple",
    "is_textarea",
    "is_boolean",
    "is_url",
}

def test_api_field_types_returns_serializable_data(client):
    resp = client.get('/api/field-types')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert 'text' in data
    meta = data['text']
    assert isinstance(meta, dict)
    assert meta.get('sql_type') == 'TEXT'
    assert meta.get('allows_options') is False


def test_api_field_types_exposes_only_serializable_keys(client):
    resp = client.get('/api/field-types')
    data = resp.get_json()

    for meta in data.values():
        # ensure only expected keys are returned
        assert set(meta.keys()) == EXPECTED_KEYS
        # and no callable values slipped through
        assert not any(callable(v) for v in meta.values())
