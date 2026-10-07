import os
import time

from cryptography.fernet import Fernet

from app.core.config import settings


def delivery_cipher() -> Fernet:
    config = settings()
    if config.account_mail_key:
        return Fernet(config.account_mail_key.get_secret_value().encode())
    if config.environment != "development":
        raise RuntimeError("ACCOUNT_MAIL_KEY required")
    path = config.account_mail_key_file
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, "wb") as output:
            output.write(Fernet.generate_key())
            output.flush()
            os.fsync(output.fileno())
    # Another local process may have created, but not yet flushed, the file.
    for _ in range(20):
        key = path.read_bytes()
        if len(key) == 44:
            return Fernet(key)
        time.sleep(0.025)
    raise RuntimeError("Invalid local account mail key")
