"""Unit tests for ECDSA signing and verification."""

import pandas as pd

from ble_blockchain.cipher.cipher import judge_signature, make_key, make_signature
from ble_blockchain.pipeline.pandas_d_encode import pandas_encode


def test_make_key_generates_non_empty_keys() -> None:
    """正常系: make_key returns non-empty key pair."""
    # Given/When: generating a key pair
    secret_key, public_key = make_key()

    # Then: both keys exist
    assert secret_key is not None
    assert public_key is not None


def test_sign_and_verify_csv_bytes(sample_plaintext_df: pd.DataFrame) -> None:
    """正常系: signature verifies for encoded CSV bytes."""
    # Given: CSV bytes and a key pair
    secret_key, public_key = make_key()
    plaintext = pandas_encode(sample_plaintext_df)

    # When: signing and verifying
    signature = make_signature(secret_key, plaintext)
    result = judge_signature(signature, plaintext, public_key)

    # Then: verification succeeds
    assert result is True


def test_judge_signature_rejects_tampered_data(
    sample_plaintext_df: pd.DataFrame,
) -> None:
    """異常系: tampered plaintext fails verification."""
    # Given: valid signature but tampered plaintext
    secret_key, public_key = make_key()
    plaintext = pandas_encode(sample_plaintext_df)
    signature = make_signature(secret_key, plaintext)
    tampered = plaintext + b"tamper"

    # When: verifying tampered data
    result = judge_signature(signature, tampered, public_key)

    # Then: verification fails
    assert result is False
