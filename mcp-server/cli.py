"""life-db CLI — manage the local SQLite data layer."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db import init_db, db_status, reset_db, DB_PATH


def _cmd_init() -> None:
    init_db()
    status = db_status()
    print(f"✓ DB initialized at {DB_PATH}")
    print(f"  schema version: {status['schema_version']}")


def _cmd_status() -> None:
    if not DB_PATH.exists():
        print(f"✗ DB not found: {DB_PATH}")
        print("  Run `life-db init` to create it.")
        sys.exit(1)
    status = db_status()
    current = status["schema_version"]
    latest = status["latest_version"]
    up_to_date = "✓" if current == latest else f"⚠ (latest={latest})"
    print(f"DB: {DB_PATH}")
    print(f"Schema version: {current} {up_to_date}")
    print("Row counts:")
    for table, count in status["rows"].items():
        print(f"  {table}: {count}")


def _cmd_reset(confirm: bool = False) -> None:
    if not confirm:
        print("This will DROP all tables and re-run migrations.")
        answer = input("Type 'yes' to confirm: ").strip()
        if answer != "yes":
            print("Aborted.")
            sys.exit(0)
    reset_db()
    print("✓ DB reset complete.")


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: life-db <command>")
        print("Commands:")
        print("  init    Initialize DB and apply pending migrations")
        print("  status  Show schema version and row counts")
        print("  reset   Drop all tables and re-initialize (destructive)")
        sys.exit(0)

    cmd = args[0]
    if cmd == "init":
        _cmd_init()
    elif cmd == "status":
        _cmd_status()
    elif cmd == "reset":
        _cmd_reset("--yes" in args)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
