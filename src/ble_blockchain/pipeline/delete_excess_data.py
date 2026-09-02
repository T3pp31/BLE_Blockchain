"""Filter scan and receive DataFrames against preliminary registration data."""

from __future__ import annotations

import pandas as pd

from ble_blockchain.config.loader import (
    DataSchema,
    load_blockchain_config,
    load_paths_config,
)


def _resolve_schema(
    schema: DataSchema | None = None,
) -> DataSchema:
    """Return the supplied schema or the configured default."""
    if schema is not None:
        return schema
    return load_blockchain_config().data_schema


def _load_preliminary_data(
    schema: DataSchema | None = None,
) -> pd.DataFrame:
    resolved = _resolve_schema(schema)
    paths = load_paths_config()
    preliminary_data = pd.read_csv(paths.preliminary_csv)
    return preliminary_data.rename(columns=resolved.csv_identity_rename)


def _load_registered_bt_addrs(
    schema: DataSchema | None = None,
) -> set[str]:
    preliminary_data = _load_preliminary_data(schema)
    return set(preliminary_data[_resolve_schema(schema).bt_addr_column].astype(str))


def _merge_with_preliminary(
    df: pd.DataFrame, schema: DataSchema | None = None
) -> pd.DataFrame:
    """Keep rows that match preliminary CSV on bt_addrs (and identity when present)."""
    resolved = _resolve_schema(schema)
    preliminary_data = _load_preliminary_data(resolved)
    if resolved.gakuseki_column in df.columns:
        merged = pd.merge(
            preliminary_data,
            df,
            on=[resolved.gakuseki_column, resolved.bt_addr_column],
            how="inner",
        )
    else:
        merged = pd.merge(
            preliminary_data,
            df,
            on=resolved.bt_addr_column,
            how="inner",
        )

    columns = list(resolved.output_columns)
    present = [column for column in columns if column in merged.columns]
    return merged[present].drop_duplicates()


def filter_registered_data(
    df: pd.DataFrame, schema: DataSchema | None = None
) -> pd.DataFrame:
    """Keep registered rows for both scan results and decoded receive DataFrames."""
    return _merge_with_preliminary(df, schema)


def delete_excess_data(
    df: pd.DataFrame, schema: DataSchema | None = None
) -> pd.DataFrame:
    """Keep only rows whose bt_addrs appear in the preliminary registration CSV."""
    return _merge_with_preliminary(df, schema)
