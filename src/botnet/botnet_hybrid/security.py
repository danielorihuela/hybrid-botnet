"""Utilities to sign and verify messages"""

import hashlib
import cryptography.hazmat.backends.openssl
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from . import ENCODING, logger


def sign_hash(hash_: bytes, private_key_path: str) -> bytes:
    private_key = load_private_key(private_key_path)
    signed_hash = private_key.sign(
        hash_,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    logger.debug(f"{hash_} signed = {signed_hash}")

    return signed_hash


def verify_message(public_key: str, msg: bytes, signed_hash: bytes) -> bool:
    msg_hash = calculate_hash(msg)
    public_key_bytes = load_public_key(public_key)
    try:
        public_key_bytes.verify(
            signed_hash,
            msg_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
    except cryptography.exceptions.InvalidSignature:
        return False

    return True


def calculate_hash(data: bytes) -> bytes:
    hash_ = hashlib.sha256(data).hexdigest().encode(ENCODING)
    logger.debug(f"{data} hash is {hash_}")

    return hash_


def calculate_file_hash(file_path: str) -> str:
    with open(file_path, "rb") as content:
        text = content.read()
    hash_ = hashlib.sha256(text).hexdigest()
    logger.debug(f"{file_path} content hash is {hash_}")

    return hash_


def encrypt(msg: str, public_key_path: str) -> bytes:
    public_key = load_public_key(public_key_path)
    msg_in_bytes = msg.encode(ENCODING)
    ciphertext = public_key.encrypt(
        msg_in_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    logger.debug(f"Plaintext to encrypt = {msg}")
    logger.debug(f"Ciphertext = {ciphertext}")

    return ciphertext


def decrypt(ciphertext: bytes, private_key_path: str) -> str:
    private_key = load_private_key(private_key_path)
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    logger.debug(f"Ciphertext to decrypt = {ciphertext}")
    logger.debug(f"Plaintext = {plaintext}")

    return plaintext.decode(ENCODING)


def load_private_key(
    private_key_path: str, password: str = None
) -> cryptography.hazmat.backends.openssl.rsa._RSAPrivateKey:
    logger.debug(f"Load private RSA key from {private_key_path}")
    with open(private_key_path, "rb") as pem:
        private_key = serialization.load_pem_private_key(
            pem.read(), password=password, backend=default_backend()
        )

    return private_key


def load_public_key(
    public_key_path: str,
) -> cryptography.hazmat.backends.openssl.rsa._RSAPublicKey:
    logger.debug(f"Load public RSA key from {public_key_path}")
    with open(public_key_path, "rb") as key_file:
        pub_bytes = serialization.load_pem_public_key(
            key_file.read(), backend=default_backend()
        )

    return pub_bytes
