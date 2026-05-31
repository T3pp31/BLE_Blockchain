"""JSON envelope codec for encrypted BLE message payloads."""

import base64
import json
from dataclasses import dataclass
from typing import Any

MESSAGE_VERSION = 1


@dataclass(frozen=True)
class MessagePayload:
    """Wire-format fields for one signed, encrypted BLE message."""
    ciphertext: bytes
    nonce: bytes
    public_key_pem: str
    signature: bytes


def pack(payload: MessagePayload) -> bytes:
    """Serialize a payload to JSON bytes."""
    envelope: dict[str, Any] = {
        "version": MESSAGE_VERSION,
        "ciphertext_b64": base64.b64encode(payload.ciphertext).decode("ascii"),
        "nonce_b64": base64.b64encode(payload.nonce).decode("ascii"),
        "public_key_pem": payload.public_key_pem,
        "signature_b64": base64.b64encode(payload.signature).decode("ascii"),
    }
    return json.dumps(envelope, separators=(",", ":")).encode("utf-8")


def unpack(data: bytes) -> MessagePayload:
    """Deserialize JSON bytes into a MessagePayload."""
    envelope = json.loads(data.decode("utf-8"))
    version = envelope.get("version")
    if version != MESSAGE_VERSION:
        raise ValueError(f"Unsupported message version: {version}")

    return MessagePayload(
        ciphertext=base64.b64decode(envelope["ciphertext_b64"]),
        nonce=base64.b64decode(envelope["nonce_b64"]),
        public_key_pem=str(envelope["public_key_pem"]),
        signature=base64.b64decode(envelope["signature_b64"]),
    )
