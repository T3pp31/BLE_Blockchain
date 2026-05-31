import pandas as pd

from delete_excess_data import filter_registered_data


def test_filter_registered_data_keeps_decoded_receive_df(
    sample_plaintext_df: pd.DataFrame,
) -> None:
    # Given: decoded receive dataframe already containing gakuseki
    # When: filtering against preliminary CSV
    result = filter_registered_data(sample_plaintext_df)

    # Then: row is kept without duplicate columns
    assert list(result.columns) == ["gakuseki", "bt_addrs", "device_name"]
    assert len(result) == 1


def test_filter_registered_data_drops_unregistered_receive_rows() -> None:
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
