import io

import pandas as pd


def pandas_encode(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode()


def pandas_decode(bytes_df: bytes) -> pd.DataFrame:
    buf = io.StringIO(bytes_df.decode())
    return pd.read_csv(buf)
