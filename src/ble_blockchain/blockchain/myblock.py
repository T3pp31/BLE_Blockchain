from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from typing import Any

import pandas as pd

from ble_blockchain.config.loader import load_blockchain_config
from ble_blockchain.pipeline.delete_excess_data import filter_registered_data
from ble_blockchain.pipeline.pandas_d_encode import pandas_encode

GENESIS_PREV_HASH = (
    "747bc42088cf0b3915982af289189e8f14d3325a7d594bc2d30a7014a536cb13"
)
CHAIN_HASH_VERSION = 2


@dataclass(frozen=True)
class ValidationError:
    block_index: int
    reason: str


@dataclass
class VerifiedReceive:
    df: pd.DataFrame
    pubkey_fingerprint: str
    payload_content_hash: str


def compute_majority_threshold(verified_count: int, majority_ratio: float) -> int:
    """Return minimum reporter count required for block inclusion."""
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
        self._verified_entries: list[VerifiedReceive] = []

    @property
    def last_majority_threshold(self) -> int:
        return self._last_threshold

    @property
    def last_verified_receive_count(self) -> int:
        return self._last_verified_count

    @property
    def verified_entries(self) -> list[VerifiedReceive]:
        return list(self._verified_entries)

    def add_new_block(
        self,
        inp: dict[str, Any],
        outp: dict[str, Any],
        tran_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        new_transaction = self.__create_new_transaction(inp, outp)
        reporter_count = int(outp.get("count", 1))

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
            "tran_counter": reporter_count,
            "tran_body": new_transaction,
        }
        if tran_meta is not None:
            new_block["tran_meta"] = tran_meta
        self.chain.append(new_block)
        return new_block

    def build_from_receives(self, receive_data_list: list[list[Any]]) -> None:
        config = load_blockchain_config()
        verified_entries = self._parse_verified_receives(receive_data_list)
        self._verified_entries = verified_entries

        if len(verified_entries) < config.min_verified_receives:
            self._last_verified_count = len(verified_entries)
            self._last_threshold = 0
            return

        self._last_verified_count = len(verified_entries)
        self._last_threshold = compute_majority_threshold(
            self._last_verified_count, config.majority_ratio
        )
        threshold = self._last_threshold

        bt_addrs_seen: set[str] = set()
        for entry in verified_entries:
            for bt_addr in entry.df["bt_addrs"].astype(str).unique():
                bt_addrs_seen.add(bt_addr)

        for bt_addr in sorted(bt_addrs_seen):
            if config.one_block_per_bt_addr and any(
                block["tran_body"]["output"]["bt_addrs"] == bt_addr
                for block in self.chain
            ):
                continue

            adoption = self._compute_adoption_for_bt_addr(
                verified_entries, bt_addr, threshold, config
            )
            if adoption is None:
                continue

            gakuseki, reporter_count, reporters, content_hash, gakuseki_votes = (
                adoption
            )
            tran_meta = {
                "count": reporter_count,
                "majority_threshold": threshold,
                "content_hash": content_hash,
                "gakuseki_votes": gakuseki_votes,
                "reporters": reporters,
            }
            inp = {"gakuseki": gakuseki}
            out = {"bt_addrs": bt_addr, "count": reporter_count}
            self.add_new_block(inp, out, tran_meta=tran_meta)

    def _parse_verified_receives(
        self, receive_data_list: list[list[Any]]
    ) -> list[VerifiedReceive]:
        verified_entries: list[VerifiedReceive] = []

        for item in receive_data_list:
            if len(item) < 4 or not item[3]:
                continue
            if item[0] is None:
                continue

            df = filter_registered_data(item[0])
            if df.empty:
                continue

            if len(item) < 6:
                continue

            public_key_pem = str(item[4])
            declared_hash = str(item[5])
            encoded_hash = payload_content_hash(pandas_encode(df))
            if declared_hash != encoded_hash:
                continue

            verified_entries.append(
                VerifiedReceive(
                    df=df,
                    pubkey_fingerprint=pubkey_fingerprint(public_key_pem),
                    payload_content_hash=declared_hash,
                )
            )

        return verified_entries

    def _compute_adoption_for_bt_addr(
        self,
        verified_entries: list[VerifiedReceive],
        bt_addr: str,
        threshold: int,
        config: Any,
    ) -> tuple[str, int, list[dict[str, str]], str, dict[str, int]] | None:
        reporters_for_addr: list[VerifiedReceive] = []
        for entry in verified_entries:
            if bt_addr in entry.df["bt_addrs"].astype(str).values:
                reporters_for_addr.append(entry)

        unique_by_fingerprint: dict[str, VerifiedReceive] = {}
        for entry in reporters_for_addr:
            unique_by_fingerprint[entry.pubkey_fingerprint] = entry

        reporter_count = len(unique_by_fingerprint)
        if reporter_count < threshold:
            return None

        unique_entries = list(unique_by_fingerprint.values())
        content_hashes = {entry.payload_content_hash for entry in unique_entries}
        if config.require_content_hash_agreement and len(content_hashes) != 1:
            return None
        content_hash = next(iter(content_hashes))

        gakuseki_votes: Counter[str] = Counter()
        for entry in unique_entries:
            rows = entry.df[entry.df["bt_addrs"].astype(str) == bt_addr]
            if rows.empty:
                continue
            gakuseki_votes[str(rows.iloc[0]["gakuseki"])] += 1

        if not gakuseki_votes:
            return None

        top_count = max(gakuseki_votes.values())
        winners = [g for g, c in gakuseki_votes.items() if c == top_count]
        if len(winners) != 1:
            return None
        gakuseki = winners[0]

        reporters: list[dict[str, str]] = [
            {
                "pubkey_fingerprint": entry.pubkey_fingerprint,
                "payload_content_hash": entry.payload_content_hash,
            }
            for entry in unique_entries
        ]

        return (
            gakuseki,
            reporter_count,
            reporters,
            content_hash,
            dict(gakuseki_votes),
        )

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

    def validate_tran_meta_verbose(self) -> list[ValidationError]:
        """Validate tran_meta fields against adoption rules (no receive replay)."""
        config = load_blockchain_config()
        errors: list[ValidationError] = []

        for index, block in enumerate(self.chain):
            block_index = index + 1
            meta = block.get("tran_meta")
            if not isinstance(meta, dict):
                errors.append(
                    ValidationError(
                        block_index=block_index,
                        reason="tran_meta is missing or invalid",
                    )
                )
                continue

            count = meta.get("count")
            threshold = meta.get("majority_threshold")
            reporters = meta.get("reporters")
            content_hash = meta.get("content_hash")

            if not isinstance(count, int) or count < 1:
                errors.append(
                    ValidationError(
                        block_index=block_index,
                        reason="tran_meta.count must be a positive integer",
                    )
                )
                continue

            if not isinstance(threshold, int) or count < threshold:
                errors.append(
                    ValidationError(
                        block_index=block_index,
                        reason="tran_meta.count is below majority_threshold",
                    )
                )

            if not isinstance(reporters, list) or len(reporters) != count:
                errors.append(
                    ValidationError(
                        block_index=block_index,
                        reason="tran_meta.reporters length must match count",
                    )
                )
                continue

            fingerprints: set[str] = set()
            reporter_hashes: set[str] = set()
            for reporter in reporters:
                if not isinstance(reporter, dict):
                    errors.append(
                        ValidationError(
                            block_index=block_index,
                            reason="tran_meta.reporters entry must be an object",
                        )
                    )
                    break
                fingerprint = reporter.get("pubkey_fingerprint")
                reporter_hash = reporter.get("payload_content_hash")
                if not isinstance(fingerprint, str) or fingerprint in fingerprints:
                    errors.append(
                        ValidationError(
                            block_index=block_index,
                            reason="duplicate or invalid pubkey_fingerprint in reporters",
                        )
                    )
                    break
                fingerprints.add(fingerprint)
                if isinstance(reporter_hash, str):
                    reporter_hashes.add(reporter_hash)

            if (
                config.require_content_hash_agreement
                and len(reporter_hashes) > 1
            ):
                errors.append(
                    ValidationError(
                        block_index=block_index,
                        reason="reporters disagree on payload_content_hash",
                    )
                )

            if isinstance(content_hash, str) and reporter_hashes:
                if content_hash not in reporter_hashes:
                    errors.append(
                        ValidationError(
                            block_index=block_index,
                            reason="tran_meta.content_hash does not match reporters",
                        )
                    )

            output = block.get("tran_body", {}).get("output", {})
            if isinstance(output, dict) and output.get("count") != count:
                errors.append(
                    ValidationError(
                        block_index=block_index,
                        reason="tran_body.output.count must match tran_meta.count",
                    )
                )

        return errors

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
