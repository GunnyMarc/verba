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

    def apply_to_env(self):
        data = self._load_store()
        for vendor, api_key in data.items():
            env_var = VENDOR_ENV_MAP.get(vendor)
            if env_var and api_key:
                os.environ[env_var] = api_key
