"""Unit tests for process_received_payload in main app."""

import pandas as pd

from ble_blockchain.app.main import process_received_payload
from ble_blockchain.ble.message_codec import MessagePayload, pack
from ble_blockchain.cipher.aes_cipher import encrypt_payload
from ble_blockchain.cipher.cipher import make_key, make_signature, public_key_to_pem
from ble_blockchain.pipeline.pandas_d_encode import pandas_encode

_SAMPLE_DF = pd.DataFrame(
    {
        "gakuseki": ["19G110001"],
        "bt_addrs": ["FC:66:CF:BE:10:BF"],
        "device_name": ["phone"],
    }
)


def _build_signed_payload() -> tuple[bytes, str]:
    """Build a signed and encrypted payload for receive tests."""
    secret_key, public_key = make_key()
    plaintext = pandas_encode(_SAMPLE_DF)
    signature = make_signature(secret_key, plaintext)
    ciphertext, nonce = encrypt_payload(plaintext)
    pem = public_key_to_pem(public_key)
    raw = pack(
        MessagePayload(
            ciphertext=ciphertext,
            nonce=nonce,
            public_key_pem=pem,
            signature=signature,
        )
    )
    return raw, pem


def test_process_received_payload_rejects_untrusted_public_key() -> None:
    """異常系: untrusted public key PEM is rejected."""
    # Given: valid signature path but untrusted PEM
    raw, _pem = _build_signed_payload()
    trusted = frozenset({"other-peer-pem"})

    # When: processing
    result = process_received_payload(raw, trusted)

    # Then: not verified and no dataframe for chain
    assert result[3] is False
    assert result[0] is None


def test_process_received_payload_accepts_trusted_peer() -> None:
    """正常系: trusted peer PEM is accepted."""
    # Given: signed payload from trusted peer PEM
    raw, pem = _build_signed_payload()

    # When: processing with trusted PEM
    result = process_received_payload(raw, frozenset({pem}))

    # Then: verified with dataframe
    assert result[3] is True
    assert result[0] is not None
