#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
uv run python -c "
import sys; sys.path.insert(0, 'mcp-server')
from db import reset_db, db_status
reset_db()
print(db_status())
"
