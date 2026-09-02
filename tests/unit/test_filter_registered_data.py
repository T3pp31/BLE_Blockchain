"""Unit tests for filter_registered_data pipeline step."""

from pathlib import Path

import pandas as pd
import pytest

from conftest_helpers import patch_preliminary_csv, student_mac_schema
from ble_blockchain.pipeline.delete_excess_data import filter_registered_data


def test_filter_registered_data_keeps_decoded_receive_df(
    sample_plaintext_df: pd.DataFrame,
) -> None:
    """正常系: registered receive rows are kept."""
    # Given: decoded receive dataframe already containing gakuseki
    # When: filtering against preliminary CSV
    result = filter_registered_data(sample_plaintext_df)

    # Then: row is kept without duplicate columns
    assert list(result.columns) == ["gakuseki", "bt_addrs", "device_name"]
    assert len(result) == 1


def test_filter_registered_data_drops_unregistered_receive_rows() -> None:
    """正常系: unregistered bt_addrs are dropped."""
    # Given: decoded dataframe with unregistered bt_addr
    df = pd.DataFrame(
        {
            "gakuseki": ["19G110001"],
            "bt_addrs": ["00:00:00:00:00:00"],
            "device_name": ["unknown"],
        }
    )

    # When: filtering
    result = filter_registered_data(df)

    # Then: row removed
    assert result.empty


def test_filter_registered_data_drops_wrong_gakuseki_for_registered_bt_addr() -> None:
    """正常系: wrong gakuseki for registered bt_addr is dropped."""
    # Given: registered bt_addr but gakuseki not in CSV for that address
    df = pd.DataFrame(
        {
            "gakuseki": ["19G999999"],
            "bt_addrs": ["FC:66:CF:BE:10:BF"],
            "device_name": ["phone"],
        }
    )

    # When: filtering with (gakuseki, bt_addrs) merge
    result = filter_registered_data(df)

    # Then: row removed
    assert result.empty


def test_filter_registered_data_with_alternate_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """正常系: alternate DataSchema drives column rename and merge keys."""
    # Given: CSV with English headers and matching schema
    csv_path = tmp_path / "registry.csv"
    csv_path.write_text(
        "student_id,mac,note\nS001,11:22:33:44:55:66,phone\n",
        encoding="utf-8",
    )
    patch_preliminary_csv(monkeypatch, csv_path)
    schema = student_mac_schema()
    df = pd.DataFrame(
        {
            "student_id": ["S001"],
            "mac": ["11:22:33:44:55:66"],
            "device_name": ["phone"],
        }
    )

    # When: filtering with alternate schema
    result = filter_registered_data(df, schema=schema)

    # Then: row kept under alternate column names
    assert list(result.columns) == ["student_id", "mac", "device_name"]
    assert len(result) == 1
    assert result.iloc[0]["student_id"] == "S001"


def test_filter_registered_data_alternate_schema_drops_unregistered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """異常系: alternate schema drops unregistered mac addresses."""
    # Given: registry without the scanned mac
    csv_path = tmp_path / "registry.csv"
    csv_path.write_text(
        "student_id,mac,note\nS001,11:22:33:44:55:66,phone\n",
        encoding="utf-8",
    )
    patch_preliminary_csv(monkeypatch, csv_path)
    schema = student_mac_schema()
    df = pd.DataFrame(
        {
            "student_id": ["S001"],
            "mac": ["00:00:00:00:00:00"],
            "device_name": ["unknown"],
        }
    )

    # When: filtering
    result = filter_registered_data(df, schema=schema)

    # Then: unregistered mac removed
    assert result.empty
