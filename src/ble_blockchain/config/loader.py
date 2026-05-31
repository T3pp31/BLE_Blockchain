"""Load typed configuration from JSON files under config/."""

import json
import os
from dataclasses import dataclass
from typing import Any

from ble_blockchain.paths import repo_root

CONFIG_DIR = repo_root() / "config"


def load_json_config(filename: str) -> dict[str, Any]:
    """Load a JSON object from config/<filename>."""
    path = CONFIG_DIR / filename
    with open(path, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


@dataclass(frozen=True)
class L2capConfig:
    """L2CAP socket settings."""
    psm: int
    recv_bufsize: int
    connect_timeout_sec: int


@dataclass(frozen=True)
class CryptoConfig:
    """Cryptography-related configuration."""
    aes_key_env: str
    signature_curve: str


@dataclass(frozen=True)
class PathsConfig:
    """Filesystem paths used by the pipeline."""
    preliminary_csv: str
    chain_export_dir: str


@dataclass(frozen=True)
class BlockchainConfig:
    """Blockchain majority and export rules."""
    majority_ratio: float
    one_block_per_bt_addr: bool
    export_enabled: bool
    min_verified_receives: int
    require_content_hash_agreement: bool
    min_distinct_devices_for_aggregate: int


def load_l2cap_config() -> L2capConfig:
    """Load L2CAP settings from config/l2cap.json."""
    data = load_json_config("l2cap.json")
    return L2capConfig(
        psm=int(data["psm"]),
        recv_bufsize=int(data["recv_bufsize"]),
        connect_timeout_sec=int(data["connect_timeout_sec"]),
    )


def load_crypto_config() -> CryptoConfig:
    """Load crypto settings from config/crypto.json."""
    data = load_json_config("crypto.json")
    return CryptoConfig(
        aes_key_env=str(data["aes_key_env"]),
        signature_curve=str(data["signature_curve"]),
    )


def load_paths_config() -> PathsConfig:
    """Load path settings from config/paths.json."""
    data = load_json_config("paths.json")
    return PathsConfig(
        preliminary_csv=str(data["preliminary_csv"]),
        chain_export_dir=str(data.get("chain_export_dir", "data/chains")),
    )


def load_blockchain_config() -> BlockchainConfig:
    """Load blockchain rules from config/blockchain.json."""
    data = load_json_config("blockchain.json")
    return BlockchainConfig(
        majority_ratio=float(data["majority_ratio"]),
        one_block_per_bt_addr=bool(data.get("one_block_per_bt_addr", True)),
        export_enabled=bool(data.get("export_enabled", True)),
        min_verified_receives=int(data.get("min_verified_receives", 3)),
        require_content_hash_agreement=bool(
            data.get("require_content_hash_agreement", True)
        ),
        min_distinct_devices_for_aggregate=int(
            data.get("min_distinct_devices_for_aggregate", 2)
        ),
    )


def load_aes_key() -> bytes:
    """Read the AES-256 key from the environment variable named in config."""
    crypto = load_crypto_config()
    key_hex = os.environ.get(crypto.aes_key_env, "")
    if not key_hex:
        raise ValueError(
            f"AES key not set. Export {crypto.aes_key_env} "
            f"(64 hex chars for AES-256). See .env.example."
        )
    key = bytes.fromhex(key_hex)
    if len(key) != 32:
        raise ValueError(
            f"{crypto.aes_key_env} must decode to 32 bytes, got {len(key)}"
        )
    return key
