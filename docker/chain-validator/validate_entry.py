from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blockchain.validator import validate_export_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a BLE chain export JSON file")
    parser.add_argument(
        "chain_file",
        help="Path to chain export JSON (e.g. /data/canonical.json)",
    )
    args = parser.parse_args()
    sys.exit(validate_export_file(Path(args.chain_file)))


if __name__ == "__main__":
    main()
