from flask import Blueprint, jsonify
import os
import json
from db.config import get_config_rows, update_config

crawler_bp = Blueprint('crawler', __name__)


def _load_folders():
    rows = get_config_rows()
    cfg = {row['key']: row['value'] for row in rows}
    folders_raw = cfg.get('crawler_folders', '[]')
    try:
        folders = json.loads(folders_raw)
        if isinstance(folders, dict):
            folders = [{"path": p, "enabled": e} for p, e in folders.items()]
    except Exception:
        folders = []
    file_count = int(cfg.get('crawler_file_count') or 0)
    return folders, file_count


@crawler_bp.route('/crawler')
def crawler_status():
    _, count = _load_folders()
    return jsonify({'file_count': count})


@crawler_bp.route('/crawler/scan', methods=['POST'])
def crawler_scan():
    folders, _ = _load_folders()
    total = 0
    for folder in folders:
        if not folder.get('enabled'):
            continue
        path = folder.get('path')
        if path and os.path.isdir(path):
            for _, _, files in os.walk(path):
                total += len(files)
    update_config('crawler_file_count', str(total))
    return jsonify({'file_count': total})
