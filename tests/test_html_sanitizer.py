import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.html_sanitizer import sanitize_html


def test_sanitize_removes_disallowed_tags():
    html = "<p>Hello <strong>World</strong><script>alert(1)</script></p>"
    cleaned = sanitize_html(html)
    assert "<strong>World</strong>" in cleaned
    assert cleaned.startswith("<p>")
    assert "<script>" not in cleaned


def test_sanitize_allows_basic_attributes():
    html = '<img src="/x.png" alt="pic" onclick="evil"><a href="/a" target="_blank" rel="noopener" onclick="bad">link</a>'
    cleaned = sanitize_html(html)
    assert '<img src="/x.png" alt="pic">' in cleaned
    assert '<a href="/a" target="_blank" rel="noopener">link</a>' in cleaned
    assert 'onclick' not in cleaned
