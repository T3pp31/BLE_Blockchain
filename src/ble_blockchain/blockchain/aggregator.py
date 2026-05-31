from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ble_blockchain.blockchain.persistence import ChainPersistenceError
from ble_blockchain.blockchain.sync import (
    collect_export_paths,
    merge_exports,
    select_canonical,
)
from ble_blockchain.config.loader import load_blockchain_config, load_paths_config


def _distinct_device_ids(candidates: list[dict]) -> set[str]:
    device_ids: set[str] = set()
    for item in candidates:
        device_id = item.get("device_id")
        if isinstance(device_id, str) and device_id:
            device_ids.add(device_id)
    return device_ids


def aggregate_chains(
    input_dir: Path, output_path: Path, *, strict: bool = False
) -> dict:
    paths = collect_export_paths(
        input_dir, exclude_names=frozenset({output_path.name})
    )
    if not paths:
        raise ChainPersistenceError(f"no JSON exports found in {input_dir}")

    candidates = merge_exports(paths)
    config = load_blockchain_config()
    distinct_devices = _distinct_device_ids(candidates)
    if len(distinct_devices) < config.min_distinct_devices_for_aggregate:
        message = (
            f"only {len(distinct_devices)} distinct device_id(s) in exports; "
            f"need at least {config.min_distinct_devices_for_aggregate}"
        )
        if strict:
            raise ChainPersistenceError(message)
        print(message, file=sys.stderr)

    canonical = select_canonical(candidates)
    canonical.pop("_source_path", None)
    canonical.pop("_chain_length", None)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as json_file:
        json.dump(canonical, json_file, sort_keys=False, indent=2)
    return canonical


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate validated chain exports into a canonical chain"
    )
    paths_config = load_paths_config()
    default_output = f"{paths_config.chain_export_dir}/canonical.json"
    parser.add_argument(
        "--input-dir",
        default=None,
        help=(
            "Directory containing chain export JSON files "
            f"(default: {paths_config.chain_export_dir} from config/paths.json)"
        ),
    )
    parser.add_argument(
        "--output",
        default=None,
        help=f"Output path for the canonical chain JSON (default: {default_output})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when fewer than min_distinct_devices_for_aggregate exports",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir or paths_config.chain_export_dir)
    output_path = Path(args.output or default_output)
    try:
        canonical = aggregate_chains(input_dir, output_path, strict=args.strict)
    except ChainPersistenceError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}), file=sys.stderr)
        sys.exit(1)

    print(
        json.dumps(
            {
                "status": "ok",
                "blocks": len(canonical.get("chain", [])),
                "output": str(output_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
