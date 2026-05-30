import pandas as pd

from config.loader import load_paths_config


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
