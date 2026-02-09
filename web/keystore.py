from __future__ import annotations

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet

from .config import VENDOR_ENV_MAP

# File paths relative to web/ directory
WEB_DIR = Path(__file__).resolve().parent
KEY_FILE = WEB_DIR / ".verba.key"
DATA_FILE = WEB_DIR / ".verba_keys.dat"


class KeyStore:
    """Fernet-encrypted API key storage."""

    def __init__(self):
        self._fernet = Fernet(self._load_or_create_key())

    def _load_or_create_key(self) -> bytes:
        if KEY_FILE.exists():
            return KEY_FILE.read_bytes().strip()
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
        os.chmod(KEY_FILE, 0o600)
        return key

    def _load_store(self) -> dict:
        if not DATA_FILE.exists():
            return {}
        encrypted = DATA_FILE.read_bytes()
        decrypted = self._fernet.decrypt(encrypted)
        return json.loads(decrypted.decode("utf-8"))

    def _save_store(self, data: dict):
        raw = json.dumps(data).encode("utf-8")
        encrypted = self._fernet.encrypt(raw)
        DATA_FILE.write_bytes(encrypted)

    def save_key(self, vendor: str, api_key: str):
        data = self._load_store()
        data[vendor] = api_key
        self._save_store(data)

    def get_key(self, vendor: str) -> str | None:
        data = self._load_store()
        return data.get(vendor)

    def get_all(self) -> dict[str, str]:
        return self._load_store()

    def stored_vendors(self) -> list[str]:
        return list(self._load_store().keys())

    def masked_keys(self) -> dict[str, str]:
        """Return {vendor: masked_key} for all stored keys."""
        data = self._load_store()
        masked = {}
        for vendor, key in data.items():
            if len(key) > 8:
                masked[vendor] = key[:4] + "*" * (len(key) - 8) + key[-4:]
            elif len(key) > 4:
                masked[vendor] = key[:2] + "*" * (len(key) - 2)
            else:
                masked[vendor] = "*" * len(key)
        return masked

    def delete_key(self, vendor: str):
        """Remove a single vendor's key from the store."""
        data = self._load_store()
        if vendor in data:
            del data[vendor]
            if data:
                self._save_store(data)
            else:
                # No keys left — clean up the data file
                if DATA_FILE.exists():
                    DATA_FILE.unlink()

    def delete_all(self):
        """Remove all stored keys and the key file."""
        if DATA_FILE.exists():
            DATA_FILE.unlink()
        if KEY_FILE.exists():
            KEY_FILE.unlink()

    def apply_to_env(self):
        data = self._load_store()
        for vendor, api_key in data.items():
            env_var = VENDOR_ENV_MAP.get(vendor)
            if env_var and api_key:
                os.environ[env_var] = api_key
