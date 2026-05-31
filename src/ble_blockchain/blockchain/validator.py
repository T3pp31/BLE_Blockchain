"""CLI helper to validate a chain export JSON file."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ble_blockchain.blockchain.persistence import ChainPersistenceError, load_chain


def validate_export_file(path: Path) -> int:
    """Validate one chain export file; return 0 on success, 1 on failure."""
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
