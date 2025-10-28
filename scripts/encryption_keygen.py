from cryptography.fernet import Fernet

SECRET_ENCRYPTION_KEY = Fernet.generate_key()
print(f"SECRET_ENCRYPTION_KEY={SECRET_ENCRYPTION_KEY.decode()}")
