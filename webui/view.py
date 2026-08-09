"""Shared Jinja2Templates instance, set by app.py at startup. Routers import
`templates` from here instead of constructing their own, so template globals
(url_for, etc.) stay consistent across the app."""
templates = None  # assigned in app.py
