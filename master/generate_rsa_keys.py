from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

PUBLIC_EXPONENT = 65537
KEY_SIZE = 2048

# Generate private and public key
private_key = rsa.generate_private_key(
    public_exponent=PUBLIC_EXPONENT,
    key_size=KEY_SIZE,
    backend=default_backend()
)
public_key = private_key.public_key()

# Store them in files
pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()
)
pub = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

with open('private_key', 'wb') as f:
    f.write(pem)

with open('public_key', 'wb') as f:
    f.write(pub)
