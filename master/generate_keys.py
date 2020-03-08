from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

# Generate private and public key
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Store them in files
private_bytes = private_key.private_bytes(
    encoding = serialization.Encoding.Raw,
    format = serialization.PrivateFormat.Raw,
    encryption_algorithm = serialization.NoEncryption()
)

public_bytes = public_key.public_bytes(
    encoding = serialization.Encoding.Raw,
    format = serialization.PublicFormat.Raw
)

with open('private_key', 'wb') as f:
    f.write(private_bytes)

with open('public_key', 'wb') as f:
    f.write(public_bytes)
