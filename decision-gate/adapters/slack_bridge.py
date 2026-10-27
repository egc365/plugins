"""Slack-bridge domain adapter (DG06): DRY-RUN by contract.

State source: ~/Documents/agent-bridge/mailboxes/* (on-disk agent messages,
frontmatter id/from/to/thread/ts/subject). Read-only. NOTHING is sent; the
send path (control.py via trace app) is a separate authorized lane.

Checks verify message presence/threading/ack - the evidence the executor
layer already produces - never 'the bot understood it'.
"""
from __future__ import annotations
import re
from pathlib import Path

BRIDGE = Path('/home/egc365/Documents/agent-bridge/mailboxes')
STATE_SCHEMA = 'slack-bridge/1'
FM = re.compile(r'^---\n(.*?)\n---\n', re.S)

def probe(bot=None, limit=20):
    rows = []
    if not BRIDGE.exists():
        return {'schema': STATE_SCHEMA, 'bots': [], 'error': 'bridge missing'}
    bots = sorted(d.name for d in BRIDGE.iterdir() if d.is_dir()) if BRIDGE.exists() else []
    for bot_dir in BRIDGE.iterdir():
        if not bot_dir.is_dir():
            continue
        inbox = bot_dir / 'inbox'
        acks = bot_dir / 'acks'
        inbox_n = len(list(inbox.glob('*.md'))) if inbox.exists() else 0
        ack_n = len(list(acks.glob('*.ack'))) if acks.exists() else 0
        recent = []
        if inbox.exists():
            for p in sorted(inbox.glob('*.md'), key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                try:
                    txt = p.read_text()[:400]
                except OSError:
                    continue
                m = FM.match(txt)
                meta = {}
                if m:
                    for line in m.group(1).splitlines():
                        k, _, v = line.partition(':')
                        meta[k.strip()] = v.strip()
                recent.append({'file': p.name, 'meta': {k: meta.get(k, '') for k in ('id', 'from', 'to', 'subject', 'ts')},
                               'body_head': txt[m.end():][:120] if m else txt[:120]})
        row = {'bot': bot_dir.name, 'inbox': inbox_n, 'acks': ack_n, 'recent': recent}
        if bot and bot == bot_dir.name:
            return {'schema': STATE_SCHEMA, 'bots': bots, 'target': row}
        rows.append(row)
    return {'schema': STATE_SCHEMA, 'bots': bots, 'boxes': rows[:limit]}

def outcome_checks(task):
    exp = task.get('expect') or {}
    def delivered(receipt, st):
        bot = exp.get('bot')
        target = st.get('target') or next((b for b in st.get('boxes', []) if b['bot'] == bot), None)
        if not target:
            return False, {'error': 'bot mailbox not found', 'bot': bot}
        needle = exp.get('subject_contains') or ''
        hits = [m for m in target['recent'] if needle.lower() in (m['meta'].get('subject', '') + m['meta'].get('id', '')).lower()]
        acked = target['acks'] > 0 if exp.get('require_ack') else True
        return bool(hits) and acked, {'matches': len(hits), 'acks': target['acks'], 'needle': needle}
    return {'delivered': delivered} if exp else {}
