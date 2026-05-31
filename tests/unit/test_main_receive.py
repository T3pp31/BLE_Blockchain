import pandas as pd

from main import process_received_payload
from pandas_d_encode import pandas_encode


def test_process_received_payload_rejects_untrusted_public_key(
    monkeypatch,
) -> None:
    # Given: valid signature path but untrusted PEM
    from cipher.cipher import make_key, make_signature, public_key_to_pem
    from cipher.aes_cipher import encrypt_payload

    secret_key, public_key = make_key()
    df = pd.DataFrame(
        {
            "gakuseki": ["19G110001"],
            "bt_addrs": ["FC:66:CF:BE:10:BF"],
            "device_name": ["phone"],
        }
    )
    plaintext = pandas_encode(df)
    signature = make_signature(secret_key, plaintext)
    ciphertext, nonce = encrypt_payload(plaintext)
    pem = public_key_to_pem(public_key)

    from ble.message_codec import MessagePayload, pack

    raw = pack(
        MessagePayload(
            ciphertext=ciphertext,
            nonce=nonce,
            public_key_pem=pem,
            signature=signature,
        )
    )
    trusted = frozenset({"other-peer-pem"})

    # When: processing
    result = process_received_payload(raw, trusted)

    # Then: not verified and no dataframe for chain
    assert result[3] is False
    assert result[0] is None


def test_process_received_payload_accepts_trusted_peer(
    monkeypatch,
) -> None:
    # Given: signed payload from trusted peer PEM
    from cipher.cipher import make_key, make_signature, public_key_to_pem
    from cipher.aes_cipher import encrypt_payload
    from ble.message_codec import MessagePayload, pack

    secret_key, public_key = make_key()
    df = pd.DataFrame(
        {
            "gakuseki": ["19G110001"],
            "bt_addrs": ["FC:66:CF:BE:10:BF"],
            "device_name": ["phone"],
        }
    )
    plaintext = pandas_encode(df)
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

    # When: processing with trusted PEM
    result = process_received_payload(raw, frozenset({pem}))

    # Then: verified with dataframe
    assert result[3] is True
    assert result[0] is not None
