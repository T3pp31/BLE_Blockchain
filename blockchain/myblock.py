from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any

import pandas as pd

from config.loader import load_paths_config

GENESIS_PREV_HASH = (
    "747bc42088cf0b3915982af289189e8f14d3325a7d594bc2d30a7014a536cb13"
)


class MyBlockChain:
    def __init__(self) -> None:
        self.chain: list[dict[str, Any]] = []

    def add_new_block(self, inp: dict[str, Any], outp: dict[str, Any]) -> dict[str, Any]:
        new_transaction = self.__create_new_transaction(inp, outp)

        if len(self.chain) > 0:
            prev_hash = self.chain[-1]["block_header"]["tran_hash"]
        else:
            prev_hash = GENESIS_PREV_HASH

        new_block = {
            "block_index": len(self.chain) + 1,
            "block_time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "block_header": {
                "prev_hash": prev_hash,
                "tran_hash": self.__hash(
                    prev_hash + self.__calc_tran_hash(new_transaction)
                ),
            },
            "tran_counter": len(inp) + len(outp),
            "tran_body": new_transaction,
        }
        self.chain.append(new_block)
        return new_block

    def build_from_receives(self, receive_data_list: list[list[Any]]) -> None:
        verified_dfs: list[pd.DataFrame] = []
        for item in receive_data_list:
            if len(item) < 4 or not item[3]:
                continue
            verified_dfs.append(item[0])

        if not verified_dfs:
            return

        df = pd.concat(verified_dfs, ignore_index=True)
        df_count = df["bt_addrs"].value_counts().to_frame(name="count")
        df_count = df_count.reset_index()

        merged = pd.merge(df, df_count, on="bt_addrs", how="left")
        merged = merged.drop_duplicates(subset=["gakuseki", "bt_addrs"])
        merged = merged.sort_values("gakuseki")

        threshold = len(verified_dfs) // 2 + 1

        for _, row in merged.iterrows():
            count = int(row["count"])
            if count >= threshold:
                inp = {"gakuseki": row["gakuseki"]}
                out = {"bt_addrs": row["bt_addrs"], "count": count}
                self.add_new_block(inp, out)

    def __create_new_transaction(
        self, inp: dict[str, Any], outp: dict[str, Any]
    ) -> dict[str, Any]:
        return {"input": inp, "output": outp}

    def __calc_tran_hash(self, new_transaction: dict[str, Any]) -> str:
        tran_string = json.dumps(new_transaction, sort_keys=True).encode()
        return self.__hash(tran_string)

    def __hash(self, str_seed: str | bytes) -> str:
        return hashlib.sha256(str(str_seed).encode()).hexdigest()

    def dump(self, block_index: int = 0) -> None:
        if block_index == 0:
            print(json.dumps(self.chain, sort_keys=False, indent=2))
        else:
            print(json.dumps(self.chain[block_index], sort_keys=False, indent=2))
