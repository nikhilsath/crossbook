def test_api_list_search_limit(client):
    resp = client.get('/api/character/list', query_string={'search': 'Aji', 'limit': 1})
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]['label'].startswith('Aji')


