import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

import blockchain.myblock
from ble.discover import scan
from ble.l2cap_server import l2cap_server
from ble.start_discoverable import start_discoverable
from cipher.cipher import judge_signature, make_key, make_signature
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


def build_send_data() -> list[Any]:
    secret_key, public_key = make_key()

    bt_addrs, device_name = asyncio.run(scan())
    df = pd.DataFrame(
        list(zip(bt_addrs, device_name)), columns=["bt_addrs", "device_name"]
    )
    df = delete_excess_data(df)

    bytes_df = pandas_encode(df)
    signature = make_signature(secret_key, df)

    return [bytes_df, public_key, signature]


def run_communication_steps(
    profile: dict[str, Any],
    tanmatsu_bt_addrs: list[str],
    send_data_list: list[Any],
    receive_data_list: list[Any],
) -> None:
    defaults = {"sleep_seconds": 30}
    if RUNTIME_PROFILES_PATH.exists():
        with open(RUNTIME_PROFILES_PATH, "r", encoding="utf-8") as json_file:
            defaults = json.load(json_file).get("defaults", defaults)

    for step in profile["steps"]:
        action = step["action"]

        if action == "discoverable":
            start_discoverable()
        elif action == "send":
            SEND(tanmatsu_bt_addrs, send_data_list)
        elif action == "receive":
            receive_data_list.append(l2cap_server())
        elif action == "sleep":
            time.sleep(step.get("seconds", defaults["sleep_seconds"]))
        else:
            raise ValueError(f"Unknown step action: {action}")


def verify_signatures(
    receive_data_list: list[Any], decode_before_verify: bool
) -> None:
    count = 0
    for item in receive_data_list:
        if decode_before_verify:
            item[0] = pandas_decode(item[0])
        result = judge_signature(item[2], item[0], item[1])
        receive_data_list[count].append(result)
        count = count + 1
        print(result)


def run_pipeline(settings_path: str) -> None:
    tanmatsu_bt_addrs, profile_name = load_settings(settings_path)
    profile = load_runtime_profile(profile_name)

    print(tanmatsu_bt_addrs)

    send_data_list = build_send_data()
    receive_data_list: list[Any] = []

    run_communication_steps(
        profile, tanmatsu_bt_addrs, send_data_list, receive_data_list
    )

    verify_signatures(
        receive_data_list, profile.get("decode_before_verify", False)
    )

    blockchain = blockchain.myblock.MyBlockChain()
    blockchain.myblock.make_blockchain(receive_data_list)
    blockchain.dump()


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
