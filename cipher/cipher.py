from ecdsa import SECP256k1, BadSignatureError, SigningKey, VerifyingKey


def make_key() -> tuple[SigningKey, VerifyingKey]:
    secret_key = SigningKey.generate(curve=SECP256k1)
    public_key = secret_key.verifying_key
    return secret_key, public_key


def public_key_to_pem(public_key: VerifyingKey) -> str:
    return public_key.to_pem().decode("ascii")


def public_key_from_pem(pem: str) -> VerifyingKey:
    return VerifyingKey.from_pem(pem.encode("ascii"))


def make_signature(secret_key: SigningKey, plaintext: bytes) -> bytes:
    return secret_key.sign(plaintext)


def judge_signature(
    signature: bytes, plaintext: bytes, public_key: VerifyingKey
) -> bool:
    try:
        return public_key.verify(signature, plaintext)
    except BadSignatureError:
        return False
