"""Accessibility (AT-SPI) domain adapter: desktop-state proposals + checks.

State schema a11y-state/1: visible app names, window titles+counts for a
target app, focused window title, caret-widget role/name when exposed.
Read-only. Nothing here types or clicks - proposals describe; executor does.

Outcome checks read a FRESH probe (post-action), never the pre-action one.
"""
from __future__ import annotations
import json

STATE_SCHEMA = 'a11y-state/1'

def _atspi():
    import gi
    gi.require_version('Atspi', '2.0')
    from gi.repository import Atspi
    return Atspi

def probe(target_app_substring=None):
    Atspi = _atspi()
    desktop = Atspi.get_desktop(0)
    apps = []
    focused = None
    target_windows = []
    for i in range(desktop.get_child_count()):
        app = desktop.get_child_at_index(i)
        if app is None:
            continue
        name = app.get_name() or ''
        wins = []
        n_children = 0
        try: n_children = app.get_child_count()
        except Exception: n_children = 0
        for w in range(n_children):
            win = app.get_child_at_index(w)
            if win is None:
                continue
            if win.get_role() and 'frame' not in str(win.get_role()).lower() and 'window' not in str(win.get_role()).lower() and 'dialog' not in str(win.get_role()).lower():
                pass  # keep: titles still useful
            try:
                attrs = win.get_attributes() or {}
                active = str(attrs.get('active', '')).lower() == 'true'
            except Exception:
                active = False
            wins.append({'title': win.get_name() or '', 'active': active})
            if active and not focused:
                focused = {'app': name, 'title': win.get_name()}
            if target_app_substring and target_app_substring.lower() in name.lower():
                target_windows.append({'app': name, 'title': win.get_name()})
        apps.append({'name': name, 'windows': len(app.get_child_count() and range(app.get_child_count()) or []), 'window_titles': [w['title'] for w in wins][:6], 'any_active': any(w['active'] for w in wins)})
    return {'schema': STATE_SCHEMA, 'apps_n': len(apps),
            'apps': [a['name'] for a in apps][:24],
            'focused': focused,
            'target_windows': target_windows,
            'target_query': target_app_substring}

QUESTIONS = [
    {'id': 'q_window_visible', 'type': 'choice', 'options': ['yes', 'no']},
    {'id': 'q_safe_to_focus', 'type': 'choice', 'options': ['yes', 'no']},
]

def outcome_checks(task):
    exp = task.get('expect') or {}
    def window_visible(receipt, st):
        want = (exp.get('window_title_substring') or '').lower()
        if not want:
            return False, {'error': 'no criterion'}
        hits = [w for w in st.get('target_windows', []) if want in str(w.get('title', '')).lower()]
        if not hits:
            hits = [a for a in [st.get('focused') or {}] if want in str(a.get('title', '')).lower()]
        return bool(hits), {'want': want, 'target_windows': st.get('target_windows', [])[:4], 'focused': st.get('focused')}
    return {'window_visible': window_visible} if exp.get('window_title_substring') else {}
