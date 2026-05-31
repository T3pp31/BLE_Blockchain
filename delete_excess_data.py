import pandas as pd

from config.loader import load_paths_config


def _load_registered_bt_addrs() -> set[str]:
    paths = load_paths_config()
    preliminary_data = pd.read_csv(paths.preliminary_csv)
    return set(preliminary_data["bt_addrs"].astype(str))


def filter_registered_data(df: pd.DataFrame) -> pd.DataFrame:
    """Keep registered rows for both scan results and decoded receive DataFrames."""
    registered_addrs = _load_registered_bt_addrs()
    if "gakuseki" in df.columns:
        filtered = df[df["bt_addrs"].astype(str).isin(registered_addrs)].copy()
        columns = ["gakuseki", "bt_addrs"]
        if "device_name" in filtered.columns:
            columns.append("device_name")
        return filtered[columns].drop_duplicates()

    return delete_excess_data(df)


def delete_excess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows whose bt_addrs appear in the preliminary registration CSV."""
    paths = load_paths_config()
    preliminary_data = pd.read_csv(paths.preliminary_csv)

    merged = pd.merge(preliminary_data, df, on="bt_addrs", how="inner")
    merged = merged.rename(columns={"学籍番号": "gakuseki"})
    columns = ["gakuseki", "bt_addrs"]
    if "device_name" in merged.columns:
        columns.append("device_name")
    result = merged[columns].drop_duplicates()
    print(result)
    return result
