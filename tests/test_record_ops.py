from unittest.mock import patch, call

from utils.record_ops import _normalize_value, update_record_field, bulk_update_records


def test_normalize_value():
    assert _normalize_value('boolean', True) == '1'
    assert _normalize_value('boolean', 'no') == '0'
    assert _normalize_value('number', '123') == '123.0'
    assert _normalize_value('number', 'bad') == '0'
    assert _normalize_value('multi_select', ['a', 'b']) == 'a, b'
    assert _normalize_value('multi_select', None) == ''


def test_update_record_field_logs_and_errors():
    schema = {'tbl': {'foo': {'type': 'text'}, 'flag': {'type': 'boolean'}}}
    prev_record = {'foo': 'old', 'flag': '0'}

    with patch('utils.record_ops.get_field_schema', return_value=schema), \
         patch('utils.record_ops.get_record_by_id', return_value=prev_record) as get_prev, \
         patch('utils.record_ops.update_field_value', return_value=True) as upd, \
         patch('utils.record_ops.append_edit_log') as log:
        result = update_record_field('tbl', 1, 'foo', 'new')
        assert result == 'new'
        upd.assert_called_once_with('tbl', 1, 'foo', 'new')
        log.assert_called_once_with('tbl', 1, 'foo', 'old', 'new')
        get_prev.assert_called_once()

    with patch('utils.record_ops.get_field_schema', return_value=schema), \
         patch('utils.record_ops.update_field_value', return_value=False):
        with patch('utils.record_ops.get_record_by_id', return_value=prev_record):
            try:
                update_record_field('tbl', 1, 'foo', 'new')
            except RuntimeError:
                pass
            else:
                assert False, 'RuntimeError not raised'


def test_bulk_update_records_logs_and_errors():
    schema = {'tbl': {'foo': {'type': 'text'}}}
    ids = [1, 2, 3]
    with patch('utils.record_ops.get_field_schema', return_value=schema), \
         patch('utils.record_ops.update_field_value', return_value=True) as upd, \
         patch('utils.record_ops.append_edit_log') as log:
        count = bulk_update_records('tbl', ids, 'foo', 'bar')
        assert count == len(ids)
        assert upd.call_count == len(ids)
        calls = [call('tbl', rid, 'foo', 'bar') for rid in ids]
        upd.assert_has_calls(calls, any_order=False)
        log_calls = [call('tbl', rid, 'foo', None, 'bar') for rid in ids]
        log.assert_has_calls(log_calls, any_order=False)

    with patch('utils.record_ops.get_field_schema', return_value=schema), \
         patch('utils.record_ops.update_field_value', side_effect=RuntimeError('boom')):
        try:
            bulk_update_records('tbl', ids, 'foo', 'bar')
        except RuntimeError:
            pass
        else:
            assert False, 'Exception not propagated'
