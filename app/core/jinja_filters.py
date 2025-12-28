# app/core/jinja_filters.py
from markupsafe import escape

def pretty_status(value: str | None) -> str:
    if not value:
        return "—"
    return escape(value.replace("_", " ").replace(".", " "))
