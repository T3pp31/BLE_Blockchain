import pandas as pd


def delete_excess_data(df):
    """
    Parameters
    ----------
    df : DataFrame,scanで作成したデータフレーム

    Return
    ----------
    df : 事前登録されているもののみが残っているデータフレーム
    """

    preliminary_data = pd.read_csv("data_folder/事前取得データ.csv")

    # 左結合をすることによって，事前に登録されているもののみ残す．
    df = pd.merge(preliminary_data, df, on="bt_addrs", how="left")
    print(df)

    return df
