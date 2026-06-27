#!/bin/bash
set -euo pipefail

# Run from the script directory so package imports resolve without editable installs.
cd "$(dirname "$0")"

# Seed best-effort; app should still boot even if the DB is temporarily unavailable.
python3 -m fastapi_app.seed_data || echo "Seed step failed; starting app anyway"

exec python3 -m gunicorn fastapi_app:app -c gunicorn.conf.py
