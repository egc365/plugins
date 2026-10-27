#!/bin/sh
# Unit checks per DG. Missing implementation => nonzero.
set -e
cd "$(dirname "$0")/.."
DG=${2:-DG01}
python3 -m pytest tests/ -q -k "$DG" 2>&1 | tail -5
