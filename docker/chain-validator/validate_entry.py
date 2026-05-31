#!/usr/bin/env python3
"""Validate a chain export JSON file. Exit 0 on success, 1 on failure."""

import sys

from ble_blockchain.blockchain.validator import validate_export_file


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: validate_entry.py <chain_export.json>", file=sys.stderr)
        sys.exit(2)
    sys.exit(validate_export_file(sys.argv[1]))


if __name__ == "__main__":
    main()
