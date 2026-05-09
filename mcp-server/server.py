#!/usr/bin/env python3
"""life-mcp: Personal life assistant MCP server.

Exposes tools for tasks, calendar events, notes, and long-term memory.
Runs as a stdio MCP server consumed by nanobot.

Usage (via uv):
    uv run python workspace/mcp-server/server.py
"""
import sys
import os

# Make db and tools importable as top-level modules
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP

from db import init_db
from tools.tasks import register as register_tasks
from tools.events import register as register_events
from tools.notes import register as register_notes
from tools.memory import register as register_memory
from tools.ledger import register as register_ledger
from tools.health import register as register_health
from tools.habits import register as register_habits

mcp = FastMCP("life-mcp")

init_db()

register_tasks(mcp)
register_events(mcp)
register_notes(mcp)
register_memory(mcp)
register_ledger(mcp)
register_health(mcp)
register_habits(mcp)

if __name__ == "__main__":
    mcp.run()
