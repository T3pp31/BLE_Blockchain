from __future__ import annotations

import json
import sys
from pathlib import Path

from blockchain.persistence import ChainPersistenceError, load_chain


def validate_export_file(path: Path) -> int:
    try:
        chain = load_chain(path)
    except (ChainPersistenceError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "blocks": len(chain.chain),
                "path": str(path),
            }
        )
    )
    return 0
