import pandas as pd

from delete_excess_data import delete_excess_data


def test_delete_excess_data_keeps_registered_only(
    sample_scan_df: pd.DataFrame,
) -> None:
    # Given: scan results with one registered and one unknown bt_addr

    # When: filtering against preliminary CSV
    result = delete_excess_data(sample_scan_df)

    # Then: only registered row remains with normalized columns
    assert len(result) == 1
    assert list(result.columns) == ["gakuseki", "bt_addrs", "device_name"]
    assert result.iloc[0]["gakuseki"] == "19G110001"
    assert result.iloc[0]["bt_addrs"] == "FC:66:CF:BE:10:BF"


def test_delete_excess_data_empty_when_no_match() -> None:
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
