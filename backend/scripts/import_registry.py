"""Import ЄДР data (JSON) into the local registry DB.

Usage:
    python scripts/import_registry.py path/to/file.json --type legal|fop
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.registry.importer import (  # noqa: E402
    import_individual_entrepreneurs,
    import_legal_entities,
)


def main() -> None:
    args = [a for a in sys.argv[1:]]
    if not args:
        print("Usage: python scripts/import_registry.py <file.json> [--type legal|fop]")
        sys.exit(1)

    path = Path(args[0])
    kind = "legal"
    if "--type" in args:
        kind = args[args.index("--type") + 1]

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        for key in ("results", "data", "records"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list):
        print("Expected a JSON list of records.")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if kind == "fop":
            count = import_individual_entrepreneurs(db, data)
        else:
            count = import_legal_entities(db, data)
        print(f"Imported {count} records ({kind}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
