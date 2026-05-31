"""Backward-compatible entry point: ``python main.py`` delegates to the package."""

from ble_blockchain.app.main import main

if __name__ == "__main__":
    main()
