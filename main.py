import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from ble.discover import scan
from ble.l2cap_server import l2cap_server
from ble.message_codec import MessagePayload, pack, unpack
from ble.start_discoverable import start_discoverable
from blockchain.myblock import MyBlockChain
from cipher.aes_cipher import decrypt_payload, encrypt_payload
from cipher.cipher import (
    judge_signature,
    make_key,
    make_signature,
    public_key_from_pem,
    public_key_to_pem,
)
from delete_excess_data import delete_excess_data
from pandas_d_encode import pandas_decode, pandas_encode
from send_and_receive import SEND

RUNTIME_PROFILES_PATH = Path("config/runtime_profiles.json")


def load_settings(settings_path: str) -> tuple[list[str], str]:
    with open(settings_path, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)

    profile = json_data.get("profile", "device1")
    tanmatsu_bt_addrs = [
        value for key, value in json_data.items() if key != "profile"
    ]
    return tanmatsu_bt_addrs, profile


def load_runtime_profile(profile_name: str) -> dict[str, Any]:
    with open(RUNTIME_PROFILES_PATH, "r", encoding="utf-8") as json_file:
        profiles = json.load(json_file)

    if profile_name not in profiles:
        raise ValueError(f"Unknown profile: {profile_name}")

    return profiles[profile_name]


def build_send_payload() -> bytes:
    secret_key, public_key = make_key()

    bt_addrs, device_name = asyncio.run(scan())
    df = pd.DataFrame(
        list(zip(bt_addrs, device_name)), columns=["bt_addrs", "device_name"]
    )
    df = delete_excess_data(df)

    plaintext = pandas_encode(df)
    signature = make_signature(secret_key, plaintext)
    ciphertext, nonce = encrypt_payload(plaintext)

    payload = MessagePayload(
        ciphertext=ciphertext,
        nonce=nonce,
        public_key_pem=public_key_to_pem(public_key),
        signature=signature,
    )
    return pack(payload)


def run_communication_steps(
    profile: dict[str, Any],
    tanmatsu_bt_addrs: list[str],
    payload_bytes: bytes,
    receive_data_list: list[Any],
) -> None:
    defaults = {"sleep_seconds": 30}
    if RUNTIME_PROFILES_PATH.exists():
        with open(RUNTIME_PROFILES_PATH, "r", encoding="utf-8") as json_file:
            file_data = json.load(json_file)
            defaults = file_data.get("defaults", defaults)

    for step in profile["steps"]:
        action = step["action"]

        if action == "discoverable":
            start_discoverable()
        elif action == "send":
            SEND(tanmatsu_bt_addrs, payload_bytes)
        elif action == "receive":
            receive_data_list.append(process_received_payload(l2cap_server()))
        elif action == "sleep":
            time.sleep(step.get("seconds", defaults["sleep_seconds"]))
        else:
            raise ValueError(f"Unknown step action: {action}")


def process_received_payload(raw: bytes) -> list[Any]:
    payload = unpack(raw)
    public_key = public_key_from_pem(payload.public_key_pem)
    plaintext = decrypt_payload(payload.ciphertext, payload.nonce)
    df = pandas_decode(plaintext)
    verified = judge_signature(payload.signature, plaintext, public_key)
    if verified:
        print("署名が正しいです")
    else:
        print("署名が正しくありません")
    return [df, public_key, payload.signature, verified]


def run_pipeline(settings_path: str) -> None:
    tanmatsu_bt_addrs, profile_name = load_settings(settings_path)
    profile = load_runtime_profile(profile_name)

    print(tanmatsu_bt_addrs)

    payload_bytes = build_send_payload()
    receive_data_list: list[Any] = []

    run_communication_steps(
        profile, tanmatsu_bt_addrs, payload_bytes, receive_data_list
    )

    chain = MyBlockChain()
    chain.build_from_receives(receive_data_list)
    chain.dump()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="BLE scan, sign, exchange, and blockchain pipeline"
    )
    parser.add_argument(
        "--settings",
        default="settings1.json",
        help="Path to device settings JSON (default: settings1.json)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.settings)
