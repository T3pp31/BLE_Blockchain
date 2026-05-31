from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union


@dataclass(frozen=True)
class DeviceSettings:
    profile: str
    tanmatsu_bt_addrs: list[str]
    signing_key_path: str
    public_key_pem: str
    trusted_peer_pems: frozenset[str]


def load_device_settings(settings_path: Union[str, Path]) -> DeviceSettings:
    path = Path(settings_path)
    with open(path, "r", encoding="utf-8") as json_file:
        data: dict[str, Any] = json.load(json_file)

    profile = str(data.get("profile", "device1"))
    tanmatsu_bt_addrs = [
        str(value)
        for key, value in data.items()
        if key.startswith("addr")
    ]

    signing_key_path = str(data.get("signing_key_path", ""))
    public_key_pem = str(data.get("public_key_pem", ""))
    if not signing_key_path or not public_key_pem:
        raise ValueError(
            f"{path}: signing_key_path and public_key_pem are required"
        )

    peer_keys = data.get("peer_public_keys", {})
    if not isinstance(peer_keys, dict):
        raise ValueError(f"{path}: peer_public_keys must be an object")

    trusted_peer_pems = frozenset(str(pem) for pem in peer_keys.values() if pem)

    return DeviceSettings(
        profile=profile,
        tanmatsu_bt_addrs=tanmatsu_bt_addrs,
        signing_key_path=signing_key_path,
        public_key_pem=public_key_pem,
        trusted_peer_pems=trusted_peer_pems,
    )
