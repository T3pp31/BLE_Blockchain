import pandas as pd

from config.loader import load_paths_config


def _load_preliminary_data() -> pd.DataFrame:
    paths = load_paths_config()
    preliminary_data = pd.read_csv(paths.preliminary_csv)
    return preliminary_data.rename(columns={"学籍番号": "gakuseki"})


def _load_registered_bt_addrs() -> set[str]:
    preliminary_data = _load_preliminary_data()
    return set(preliminary_data["bt_addrs"].astype(str))


def _merge_with_preliminary(df: pd.DataFrame) -> pd.DataFrame:
    """Keep rows that match preliminary CSV on bt_addrs (and gakuseki when present)."""
    preliminary_data = _load_preliminary_data()
    if "gakuseki" in df.columns:
        merged = pd.merge(
            preliminary_data,
            df,
            on=["gakuseki", "bt_addrs"],
            how="inner",
        )
    else:
        merged = pd.merge(preliminary_data, df, on="bt_addrs", how="inner")

    columns = ["gakuseki", "bt_addrs"]
    if "device_name" in merged.columns:
        columns.append("device_name")
    return merged[columns].drop_duplicates()


def filter_registered_data(df: pd.DataFrame) -> pd.DataFrame:
    """Keep registered rows for both scan results and decoded receive DataFrames."""
    return _merge_with_preliminary(df)


def delete_excess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows whose bt_addrs appear in the preliminary registration CSV."""
    return _merge_with_preliminary(df)
