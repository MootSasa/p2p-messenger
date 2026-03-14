import os
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

class CryptoManager:
    def __init__(self):
        self.ed_private_key = ed25519.Ed25519PrivateKey.generate()
        self.ed_public_key = self.ed_private_key.public_key()
        self.x_private_key = x25519.X25519PrivateKey.generate()
        self.x_public_key = self.x_private_key.public_key()
        self.shared_secret_key = None
        self.cipher = None

    def get_public_bytes(self) -> bytes:
        return self.x_public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

    def establish_shared_secret(self, peer_public_bytes: bytes):
        peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_public_bytes)
        shared_secret = self.x_private_key.exchange(peer_public_key)
        self.shared_secret_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'p2p_messenger_handshake',
        ).derive(shared_secret)
        self.cipher = ChaCha20Poly1305(self.shared_secret_key)

    def encrypt_data(self, data: bytes) -> bytes:
        if not self.cipher:
            raise ValueError()
        nonce = os.urandom(12)
        return nonce + self.cipher.encrypt(nonce, data, associated_data=None)

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        if not self.cipher:
            raise ValueError()
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        return self.cipher.decrypt(nonce, ciphertext, associated_data=None)
    