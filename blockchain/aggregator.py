from __future__ import annotations

import argparse
import json
from pathlib import Path

from blockchain.persistence import ChainPersistenceError
from blockchain.sync import collect_export_paths, merge_exports, select_canonical
from config.loader import load_paths_config


def aggregate_chains(input_dir: Path, output_path: Path) -> dict:
    paths = collect_export_paths(
        input_dir, exclude_names=frozenset({output_path.name})
    )
    if not paths:
        raise ChainPersistenceError(f"no JSON exports found in {input_dir}")

    candidates = merge_exports(paths)
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
    args = parser.parse_args()

    input_dir = Path(args.input_dir or paths_config.chain_export_dir)
    output_path = Path(args.output or default_output)
    canonical = aggregate_chains(input_dir, output_path)
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
