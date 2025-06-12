import bleach

# Define allowed tags and attributes. Quill outputs tags like <p>, <strong>, <em>,
# <u>, <ol>, <ul>, <li>, <a>, <pre>, <code>, <blockquote>, <img>, etc.
# We'll allow a basic safe subset. The set below is roughly equivalent to
# bleach.sanitizer.ALLOWED_TAGS plus some extra from Quill (h1-h6, div, span).

ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol',
    'strong', 'ul', 'p', 'br', 'pre', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'span', 'div', 'img'
]

# Allow basic attributes including href for links and src/alt for images
ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt'],
}

def sanitize_html(html: str) -> str:
    """Return cleaned HTML safe for storage/display."""
    if not html:
        return ''
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
