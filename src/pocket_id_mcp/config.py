from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

_SAFE_FILE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key_file: Path
    secret_output_dir: Path
    request_timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "Settings":
        base_url = os.environ.get("POCKET_ID_BASE_URL", "").rstrip("/")
        api_key_file = Path(os.environ.get("POCKET_ID_API_KEY_FILE", ""))
        secret_output_dir = Path(os.environ.get("POCKET_ID_SECRET_OUTPUT_DIR", ""))
        timeout = float(os.environ.get("POCKET_ID_REQUEST_TIMEOUT_SECONDS", "10"))
        settings = cls(base_url, api_key_file, secret_output_dir, timeout)
        settings.validate()
        return settings

    def validate(self) -> None:
        parsed = urlsplit(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path not in {"", "/"}:
            raise ValueError("POCKET_ID_BASE_URL must be an HTTP(S) origin without a path")
        if self.request_timeout_seconds <= 0 or self.request_timeout_seconds > 120:
            raise ValueError("POCKET_ID_REQUEST_TIMEOUT_SECONDS must be greater than 0 and at most 120")
        self._validate_private_file(self.api_key_file, "Pocket ID API-key file")
        self._validate_private_directory(self.secret_output_dir, "Pocket ID secret output directory")
        self.read_api_key()

    @staticmethod
    def _validate_private_file(path: Path, label: str) -> None:
        try:
            info = path.lstat()
        except FileNotFoundError as exc:
            raise ValueError(f"{label} does not exist: {path}") from exc
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"{label} is not a regular file: {path}")
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError(f"{label} must not have group or other permissions: {path}")
        if info.st_size < 1 or info.st_size > 4096:
            raise ValueError(f"{label} has an invalid size")

    @staticmethod
    def _validate_private_directory(path: Path, label: str) -> None:
        try:
            info = path.lstat()
        except FileNotFoundError as exc:
            raise ValueError(f"{label} does not exist: {path}") from exc
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError(f"{label} is not a directory: {path}")
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError(f"{label} must not have group or other permissions: {path}")

    def read_api_key(self) -> str:
        self._validate_private_file(self.api_key_file, "Pocket ID API-key file")
        value = self.api_key_file.read_text(encoding="utf-8").strip()
        if not value or any(character.isspace() for character in value):
            raise ValueError("Pocket ID API-key file must contain one non-empty token")
        return value

    def secret_path(self, file_name: str) -> Path:
        if not _SAFE_FILE_NAME.fullmatch(file_name):
            raise ValueError("Secret file name must be a safe basename of at most 128 characters")
        self._validate_private_directory(self.secret_output_dir, "Pocket ID secret output directory")
        candidate = self.secret_output_dir / file_name
        if candidate.parent.resolve() != self.secret_output_dir.resolve():
            raise ValueError("Secret output path escapes the configured directory")
        return candidate
