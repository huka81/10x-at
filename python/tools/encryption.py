import os

from cryptography.fernet import Fernet


def encrypt_password(password: str) -> str:
    """Encrypt the password using Fernet"""
    cipher_suite = Fernet(os.getenv("ENCRYPTING_KEY"))
    encrypted_password = cipher_suite.encrypt(password.encode()).decode("utf-8")
    return encrypted_password


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt the encrypted password using Fernet"""
    cipher_suite = Fernet(os.getenv("ENCRYPTING_KEY"))
    decrypted_password = cipher_suite.decrypt(encrypted_password.encode()).decode(
        "utf-8"
    )
    return decrypted_password
