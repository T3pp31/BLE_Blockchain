from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ble_blockchain.blockchain.persistence import ChainPersistenceError, load_chain


def merge_exports(paths: list[Path]) -> list[dict[str, Any]]:
    """Load and validate each export file; return export dicts for valid chains."""
    exports: list[dict[str, Any]] = []
    for path in paths:
        chain = load_chain(path)
        with open(path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        data["_source_path"] = str(path)
        data["_chain_length"] = len(chain.chain)
        exports.append(data)
    return exports


def select_canonical(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Select the longest valid chain; tie-break by last tran_hash lexicographic max."""
    if not candidates:
        raise ChainPersistenceError("no chain exports provided")

    def sort_key(item: dict[str, Any]) -> tuple[int, str]:
        chain = item.get("chain", [])
        length = len(chain) if isinstance(chain, list) else 0
        last_hash = ""
        if length > 0:
            header = chain[-1].get("block_header", {})
            last_hash = str(header.get("tran_hash", ""))
        return (length, last_hash)

    return max(candidates, key=sort_key)


def collect_export_paths(
    input_dir: Path,
    *,
    exclude_names: frozenset[str] | None = None,
) -> list[Path]:
    if not input_dir.is_dir():
        raise ChainPersistenceError(f"input directory not found: {input_dir}")
    paths = sorted(input_dir.glob("*.json"))
    if exclude_names:
        paths = [path for path in paths if path.name not in exclude_names]
    return paths
