#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -d ".venv" ]; then
  # Use the project virtualenv when it exists.
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

exec uvicorn src.main:app --reload --host 127.0.0.1 --port 8100
