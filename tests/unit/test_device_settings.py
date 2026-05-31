import json
from pathlib import Path

import pytest

from config.device_settings import load_device_settings


def test_load_device_settings_reads_peer_keys(tmp_path: Path) -> None:
    # Given: settings with signing key path and peer public keys
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "profile": "device1",
                "signing_key_path": "keys/device1_private.pem",
                "public_key_pem": "pem-self",
                "peer_public_keys": {
                    "device2": "pem-2",
                    "device3": "pem-3",
                },
                "addr2": "E4:5F:01:25:11:B6",
            }
        ),
        encoding="utf-8",
    )

    # When: loading
    settings = load_device_settings(settings_path)

    # Then: peer PEMs available for trust check
    assert settings.profile == "device1"
    assert settings.tanmatsu_bt_addrs == ["E4:5F:01:25:11:B6"]
    assert settings.trusted_peer_pems == frozenset({"pem-2", "pem-3"})


def test_load_device_settings_requires_key_fields(tmp_path: Path) -> None:
    # Given: settings missing public_key_pem
    settings_path = tmp_path / "bad.json"
    settings_path.write_text(
        json.dumps({"profile": "device1", "addr2": "AA"}),
        encoding="utf-8",
    )

    # When/Then
    with pytest.raises(ValueError, match="signing_key_path"):
        load_device_settings(settings_path)
