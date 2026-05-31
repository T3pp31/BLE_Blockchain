#!/usr/bin/env python3
"""Generate per-device ECDSA keys and update settings1-4.json with public keys."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from cipher.cipher import make_key, public_key_to_pem

KEYS_DIR = REPO_ROOT / "keys"
DEVICES = ("device1", "device2", "device3", "device4")
SETTINGS_FILES = (
    "settings1.json",
    "settings2.json",
    "settings3.json",
    "settings4.json",
)


def main() -> None:
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    public_keys: dict[str, str] = {}

    for device in DEVICES:
        secret_key, public_key = make_key()
        private_path = KEYS_DIR / f"{device}_private.pem"
        public_path = KEYS_DIR / f"{device}_public.pem"
        private_path.write_bytes(secret_key.to_pem())
        public_pem = public_key_to_pem(public_key)
        public_path.write_text(public_pem, encoding="utf-8")
        public_keys[device] = public_pem
        print(f"wrote {private_path} and {public_path}")

    for index, settings_name in enumerate(SETTINGS_FILES, start=1):
        device = f"device{index}"
        settings_path = REPO_ROOT / settings_name
        with open(settings_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        peer_public_keys = {
            peer: public_keys[peer]
            for peer in DEVICES
            if peer != device
        }
        data["signing_key_path"] = f"keys/{device}_private.pem"
        data["public_key_pem"] = public_keys[device]
        data["peer_public_keys"] = peer_public_keys

        with open(settings_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
            json_file.write("\n")
        print(f"updated {settings_path}")


if __name__ == "__main__":
    main()
