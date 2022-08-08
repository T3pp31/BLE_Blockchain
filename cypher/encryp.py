from ecdsa import SigningKey
from ecdsa import VerifyingKey
from ecdsa import SECP256k1

def key():
    secret_key = SigningKey.generate(curve=SECP256k1)
    public_key = secret_key.verifying_key
    secret_b = secret_key.to_string()
    public_b = public_key.to_string()
    secret_s = secret_b.hex()
    public_s = public_b.hex()
    print(secret_s)
    print(public_s)