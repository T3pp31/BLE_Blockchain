"""Unit tests for delete_excess_data pipeline step."""

from pathlib import Path

import pandas as pd
import pytest

from conftest_helpers import patch_preliminary_csv
from ble_blockchain.config.loader import DataSchema
from ble_blockchain.pipeline.delete_excess_data import delete_excess_data


def test_delete_excess_data_keeps_registered_only(
    sample_scan_df: pd.DataFrame,
) -> None:
    """正常系: only registered bt_addrs are kept."""
    # Given: scan results with one registered and one unknown bt_addr

    # When: filtering against preliminary CSV
    result = delete_excess_data(sample_scan_df)

    # Then: only registered row remains with normalized columns
    assert len(result) == 1
    assert list(result.columns) == ["gakuseki", "bt_addrs", "device_name"]
    assert result.iloc[0]["gakuseki"] == "19G110001"
    assert result.iloc[0]["bt_addrs"] == "FC:66:CF:BE:10:BF"


def test_delete_excess_data_empty_when_no_match() -> None:
    """正常系: empty result when no addresses match."""
    # Given: scan with no registered addresses
    df = pd.DataFrame(
        {"bt_addrs": ["00:00:00:00:00:00"], "device_name": ["unknown"]}
    )

    # When: filtering
    result = delete_excess_data(df)

    # Then: empty dataframe with expected columns
    assert result.empty
    assert "gakuseki" in result.columns
    assert "bt_addrs" in result.columns


def test_delete_excess_data_with_csv_identity_rename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """正常系: csv_identity_rename maps foreign CSV headers into schema columns."""
    # Given: CSV using Japanese header and schema rename mapping
    csv_path = tmp_path / "registry.csv"
    csv_path.write_text(
        "学籍番号,bt_addrs,備考\n19G110001,FC:66:CF:BE:10:BF,phone\n",
        encoding="utf-8",
    )
    patch_preliminary_csv(monkeypatch, csv_path)
    schema = DataSchema(
        gakuseki_column="gakuseki",
        bt_addr_column="bt_addrs",
        csv_identity_rename={"学籍番号": "gakuseki"},
        output_columns=["gakuseki", "bt_addrs", "device_name"],
        input_field="gakuseki",
        output_field="bt_addrs",
    )
    df = pd.DataFrame(
        {
            "bt_addrs": ["FC:66:CF:BE:10:BF", "AA:BB:CC:DD:EE:FF"],
            "device_name": ["phone", "laptop"],
        }
    )

    # When: filtering with explicit schema
    result = delete_excess_data(df, schema=schema)

    # Then: rename applied and only registered row kept
    assert len(result) == 1
    assert result.iloc[0]["gakuseki"] == "19G110001"
