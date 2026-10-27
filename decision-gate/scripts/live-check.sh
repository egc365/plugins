#!/bin/sh
# Live-lane runner: dg01-* cases drive the CLI; receipts to stdout+file.
set -e
cd "$(dirname "$0")/.."
CASE=$1
OUT=receipts/DG01/$(echo "$CASE" | tr -d '_').json
mkdir -p receipts/DG01
case "$CASE" in
  dg01-valid-proposal)
    python3 dg.py proposal --task t1 --app shell --goal "list files" --op ls | tee "$OUT";;
  dg01-missing-goal)
    if python3 dg.py proposal --task t1 --app shell --goal "" >"$OUT" 2>/dev/null; then exit 1; else echo '{"case":"dg01-missing-goal","result":"rejected-at-boundary"}' | tee "$OUT"; fi;;
  dg01-bad-probability)
    if python3 dg.py decision --hash abc --model m --p 1.5 --outcome accept >"$OUT" 2>/dev/null; then exit 1; else echo '{"case":"dg01-bad-probability","result":"rejected"}' | tee "$OUT"; fi;;
  dg01-missing-check|dg01-inventory|dg01-private-manifest|dg01-expired-proposal|dg01-schema-version|dg01-hash-binding|dg01-budget-reservation)
    python3 dg.py "$CASE" | tee "$OUT";;
  *) echo "unknown case $CASE"; exit 2;;
esac
