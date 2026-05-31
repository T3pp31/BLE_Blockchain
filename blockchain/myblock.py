from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

import pandas as pd

from config.loader import load_blockchain_config
from delete_excess_data import filter_registered_data

GENESIS_PREV_HASH = (
    "747bc42088cf0b3915982af289189e8f14d3325a7d594bc2d30a7014a536cb13"
)
CHAIN_HASH_VERSION = 2


@dataclass(frozen=True)
class ValidationError:
    block_index: int
    reason: str


def compute_majority_threshold(verified_count: int, majority_ratio: float) -> int:
    """Return minimum bt_addrs report count required for block inclusion."""
    if verified_count <= 0:
        return 1
    if majority_ratio == 0.5:
        return max(1, verified_count // 2 + 1)
    return max(1, math.ceil(verified_count * majority_ratio))


def pubkey_fingerprint(public_key_pem: str) -> str:
    return hashlib.sha256(public_key_pem.encode("utf-8")).hexdigest()


def payload_content_hash(plaintext: bytes) -> str:
    return hashlib.sha256(plaintext).hexdigest()


class MyBlockChain:
    def __init__(self) -> None:
        self.chain: list[dict[str, Any]] = []
        self._last_threshold: int = 0
        self._last_verified_count: int = 0

    @property
    def last_majority_threshold(self) -> int:
        return self._last_threshold

    @property
    def last_verified_receive_count(self) -> int:
        return self._last_verified_count

    def add_new_block(
        self,
        inp: dict[str, Any],
        outp: dict[str, Any],
        tran_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        new_transaction = self.__create_new_transaction(inp, outp)

        if len(self.chain) > 0:
            prev_hash = self.chain[-1]["block_header"]["tran_hash"]
        else:
            prev_hash = GENESIS_PREV_HASH

        new_block: dict[str, Any] = {
            "block_index": len(self.chain) + 1,
            "block_time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "block_header": {
                "prev_hash": prev_hash,
                "tran_hash": self.__hash_bytes(
                    (prev_hash + self.__calc_tran_hash(new_transaction)).encode(
                        "utf-8"
                    )
                ),
            },
            "tran_counter": len(inp) + len(outp),
            "tran_body": new_transaction,
        }
        if tran_meta is not None:
            new_block["tran_meta"] = tran_meta
        self.chain.append(new_block)
        return new_block

    def build_from_receives(self, receive_data_list: list[list[Any]]) -> None:
        config = load_blockchain_config()
        verified_entries: list[dict[str, Any]] = []

        for item in receive_data_list:
            if len(item) < 4 or not item[3]:
                continue
            df = filter_registered_data(item[0])
            if df.empty:
                continue
            entry: dict[str, Any] = {"df": df}
            if len(item) >= 6:
                public_key_pem = str(item[4])
                content_hash = str(item[5])
                entry["pubkey_fingerprint"] = pubkey_fingerprint(public_key_pem)
                entry["payload_content_hash"] = content_hash
            verified_entries.append(entry)

        if not verified_entries:
            return

        verified_dfs = [entry["df"] for entry in verified_entries]
        self._last_verified_count = len(verified_dfs)
        self._last_threshold = compute_majority_threshold(
            self._last_verified_count, config.majority_ratio
        )

        df = pd.concat(verified_dfs, ignore_index=True)
        df_count = df["bt_addrs"].value_counts().to_frame(name="count")
        df_count = df_count.reset_index()

        merged = pd.merge(df, df_count, on="bt_addrs", how="left")
        merged = merged.drop_duplicates(subset=["gakuseki", "bt_addrs"])
        merged = merged.sort_values("gakuseki")

        threshold = self._last_threshold
        seen_bt_addrs: set[str] = set()

        for _, row in merged.iterrows():
            count = int(row["count"])
            bt_addr = str(row["bt_addrs"])
            if count < threshold:
                continue
            if config.one_block_per_bt_addr and bt_addr in seen_bt_addrs:
                continue

            reporters = self._collect_reporters(verified_entries, bt_addr)
            tran_meta = {
                "count": count,
                "majority_threshold": threshold,
                "reporters": reporters,
            }
            inp = {"gakuseki": row["gakuseki"]}
            out = {"bt_addrs": bt_addr, "count": count}
            self.add_new_block(inp, out, tran_meta=tran_meta)
            seen_bt_addrs.add(bt_addr)

    def validate_chain(self) -> bool:
        return len(self.validate_chain_verbose()) == 0

    def validate_chain_verbose(self) -> list[ValidationError]:
        errors: list[ValidationError] = []
        prev_tran_hash = GENESIS_PREV_HASH

        for index, block in enumerate(self.chain):
            block_index = index + 1
            expected_index = block.get("block_index")
            if expected_index != block_index:
                errors.append(
                    ValidationError(
                        block_index=block_index,
                        reason=(
                            f"block_index mismatch: expected {block_index}, "
                            f"got {expected_index}"
                        ),
                    )
                )

            header = block.get("block_header", {})
            prev_hash = header.get("prev_hash")
            if prev_hash != prev_tran_hash:
                errors.append(
                    ValidationError(
                        block_index=block_index,
                        reason="prev_hash does not match previous block tran_hash",
                    )
                )

            tran_body = block.get("tran_body")
            if not isinstance(tran_body, dict):
                errors.append(
                    ValidationError(
                        block_index=block_index,
                        reason="tran_body is missing or invalid",
                    )
                )
                prev_tran_hash = header.get("tran_hash", prev_tran_hash)
                continue

            expected_tran_hash = self.__hash_bytes(
                (
                    str(prev_hash)
                    + self.__calc_tran_hash(tran_body)
                ).encode("utf-8")
            )
            actual_tran_hash = header.get("tran_hash")
            if actual_tran_hash != expected_tran_hash:
                errors.append(
                    ValidationError(
                        block_index=block_index,
                        reason="tran_hash does not match recomputed value",
                    )
                )

            prev_tran_hash = str(actual_tran_hash)

        return errors

    def _collect_reporters(
        self,
        verified_entries: list[dict[str, Any]],
        bt_addr: str,
    ) -> list[dict[str, str]]:
        reporters: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()

        for entry in verified_entries:
            if "pubkey_fingerprint" not in entry:
                continue
            df = entry["df"]
            if bt_addr not in df["bt_addrs"].values:
                continue
            fingerprint = str(entry["pubkey_fingerprint"])
            content_hash = str(entry["payload_content_hash"])
            key = (fingerprint, content_hash)
            if key in seen:
                continue
            seen.add(key)
            reporters.append(
                {
                    "pubkey_fingerprint": fingerprint,
                    "payload_content_hash": content_hash,
                }
            )
        return reporters

    def __create_new_transaction(
        self, inp: dict[str, Any], outp: dict[str, Any]
    ) -> dict[str, Any]:
        return {"input": inp, "output": outp}

    def __calc_tran_hash(self, new_transaction: dict[str, Any]) -> str:
        tran_string = json.dumps(new_transaction, sort_keys=True).encode("utf-8")
        return self.__hash_bytes(tran_string)

    @staticmethod
    def __hash_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def dump(self, block_index: int = 0) -> None:
        if block_index == 0:
            print(json.dumps(self.chain, sort_keys=False, indent=2))
        else:
            print(json.dumps(self.chain[block_index - 1], sort_keys=False, indent=2))
