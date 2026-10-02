#!/usr/bin/env python3
"""Cursor hooks that hold every agent reply to the unslop skill.

capture (afterAgentResponse): saves the reply text for the stop hook.
check (stop): lints the saved reply with the mechanical unslop rules and the
vendored STE linter. On a hard finding it returns a followup_message that asks
the agent for one corrected reply. hooks.json sets loop_limit 1, and this
script also skips loop_count > 0, so a correction is never checked again.

State: $CURSOR_PROJECT_DIR/.cursor/unslop/last-response-<conversation_id>.txt
Opt out: set UNSLOP_HOOK=off, or create $CURSOR_PROJECT_DIR/.cursor/unslop/off.
Tune: UNSLOP_DISABLE=long-sentence,synonym-rotation silences rules by id.
      UNSLOP_MAX_WORDS=30 raises the sentence cap (default 25, STE descriptive).

Any error exits 0 with no output, so a broken hook never blocks a reply.
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(os.environ.get("CURSOR_PROJECT_DIR", "."), ".cursor", "unslop")
MAX_LISTED = 10

FENCE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")
URL = re.compile(r"\(?https?://\S+\)?")

# (rule id, unslop rule number, pattern, fix). Only patterns that are wrong in
# every context belong here. Judgment rules stay in the skill.
UNSLOP_RULES = [
    ("em-dash", 13, re.compile(r"—|\s–\s|\s--\s"),
     "Use a period or a comma instead of a dash."),
    ("ai-vocabulary", 7, re.compile(
        r"\b(additionally|crucial(?:ly)?|delv(?:e|es|ed|ing)|enduring|enhanc(?:e|es|ed|ing|ement)"
        r"|foster(?:s|ed|ing)?|garner(?:s|ed|ing)?|interplay|intricate|pivotal"
        r"|showcas(?:e|es|ed|ing)|testament|underscor(?:e|es|ed|ing)|vibrant)\b", re.I),
     "Replace with a plain word."),
    ("is-substitute", 8, re.compile(r"\b(serves? as|stands? as|boasts?)\b", re.I),
     "Say \"is\" or \"has\"."),
    ("not-just-but", 9, re.compile(r"\bnot (?:just|only|merely)\b[^.!?\n]{1,80}?\bbut\b", re.I),
     "State the point directly."),
    ("curly-quote", 19, re.compile(r"[“”‘’]"),
     "Use straight quotes."),
    ("chatbot-phrase", 20, re.compile(
        r"(I hope this helps|let me know if|\bof course!|\bcertainly!|smoking gun)", re.I),
     "Delete the phrase."),
    ("sycophancy", 22, re.compile(
        r"\b(great question|excellent question|you'?re absolutely right|you are absolutely right)\b", re.I),
     "Respond directly."),
    ("filler", 23, re.compile(
        r"\b(in order to|due to the fact that|it is important to note that|it'?s worth noting)\b", re.I),
     "Cut the filler (\"in order to\" becomes \"to\")."),
    ("plain-word", 31, re.compile(
        r"\b(utiliz(?:e|es|ed|ing)|leverag(?:e|es|ed|ing)|facilitat(?:e|es|ed|ing)|numerous|in the event that)\b", re.I),
     "Use the plain word (use, help, many, if)."),
]

# STE rules (unslop 34 to 41) from the vendored linter that count as hard.
STE_HARD = {"semicolon", "phrasal-verb", "marketing-adjective", "nominalization",
            "long-sentence", "synonym-rotation", "dangling-conjunction"}


def load_ste_lint():
    path = os.path.join(HERE, "vendor", "ste-lint.py")
    spec = importlib.util.spec_from_file_location("ste_lint", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prose_only(text):
    """Remove code blocks, inline code, and URLs, keeping line numbers."""
    text = FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    text = INLINE_CODE.sub(" ", text)
    return URL.sub(" ", text)


def find_violations(text, ste_lint, disabled, max_words):
    findings = []
    prose = prose_only(text)
    for lineno, line in enumerate(prose.splitlines(), 1):
        for rule_id, number, pattern, fix in UNSLOP_RULES:
            if rule_id in disabled:
                continue
            for m in pattern.finditer(line):
                findings.append((lineno, f"unslop {number} {rule_id}", m.group(0), fix))
    ste_lint.MAX_WORDS = max_words
    ste_findings, _ = ste_lint.lint(prose)
    for f in ste_findings:
        if f["rule"] in STE_HARD and f["rule"] not in disabled:
            findings.append((f["line"], f"STE {f['rule']}", f["match"], f["message"]))
    findings.sort(key=lambda f: f[0])
    return findings


def followup(findings):
    lines = [f"- line {n}, {rule}: \"{match.strip()}\". {fix}" for n, rule, match, fix in findings[:MAX_LISTED]]
    more = len(findings) - MAX_LISTED
    if more > 0:
        lines.append(f"- {more} more.")
    return ("[unslop] Your last reply broke the unslop skill (unslop rules plus "
            "about 80% of ASD-STE100). Findings:\n" + "\n".join(lines) +
            "\nSend the corrected reply in full. Keep every fact, hedge, and code block. "
            "Do not mention this check. If a finding is a false positive, keep that text as it is.")


def state_file(conversation_id):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", conversation_id or "default")
    return os.path.join(STATE_DIR, f"last-response-{safe}.txt")


def enabled():
    if os.environ.get("UNSLOP_HOOK", "").lower() in ("off", "0", "false"):
        return False
    return not os.path.exists(os.path.join(STATE_DIR, "off"))


def capture(payload):
    text = payload.get("text") or ""
    if not text.strip():
        return
    os.makedirs(STATE_DIR, exist_ok=True)
    ignore = os.path.join(STATE_DIR, ".gitignore")
    if not os.path.exists(ignore):
        with open(ignore, "w", encoding="utf-8") as fh:
            fh.write("*\n")
    with open(state_file(payload.get("conversation_id")), "w", encoding="utf-8") as fh:
        fh.write(text)


def check(payload):
    path = state_file(payload.get("conversation_id"))
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    os.remove(path)
    if payload.get("status") != "completed" or int(payload.get("loop_count") or 0) > 0:
        return
    disabled = {r.strip() for r in os.environ.get("UNSLOP_DISABLE", "").split(",") if r.strip()}
    max_words = int(os.environ.get("UNSLOP_MAX_WORDS") or 25)
    findings = find_violations(text, load_ste_lint(), disabled, max_words)
    if findings:
        print(json.dumps({"followup_message": followup(findings)}))


def selftest():
    ste_lint = load_ste_lint()
    bad = ("Great question! Additionally, the build serves as a check — it is crucial; "
           "we spin up the job in order to test it.")
    rules = {rule for _, rule, _, _ in find_violations(bad, ste_lint, set(), 25)}
    for expected in ("unslop 22 sycophancy", "unslop 7 ai-vocabulary", "unslop 8 is-substitute",
                     "unslop 13 em-dash", "STE semicolon", "STE phrasal-verb", "unslop 23 filler"):
        assert expected in rules, (expected, rules)
    clean = ("The build runs the tests. If a test fails, the build stops.\n\n"
             "```\nx = a; y = b  # crucial — code is skipped\n```\n"
             "Run `a; b` to see it. The request may have failed. Read https://example.com/a;b for details.")
    assert find_violations(clean, ste_lint, set(), 25) == [], find_violations(clean, ste_lint, set(), 25)
    assert find_violations("We spin up the job.", ste_lint, {"phrasal-verb"}, 25) == []
    long_sentence = " ".join(["word"] * 28) + "."
    assert find_violations(long_sentence, ste_lint, set(), 25)
    assert not find_violations(long_sentence, ste_lint, set(), 30)
    print("selftest OK")


def main(argv):
    if argv[:1] == ["--selftest"]:
        selftest()
        return
    if not argv or argv[0] not in ("capture", "check") or not enabled():
        return
    payload = json.loads(sys.stdin.read() or "{}")
    capture(payload) if argv[0] == "capture" else check(payload)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as err:  # fail open: a hook bug must not block replies
        if sys.argv[1:2] == ["--selftest"]:
            raise
        print(f"unslop hook skipped: {err}", file=sys.stderr)
    sys.exit(0)
