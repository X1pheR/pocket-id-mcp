from __future__ import annotations

from pathlib import Path

import pytest

from pocket_id_mcp.config import Settings


def test_private_paths_are_required(tmp_path: Path) -> None:
    key = tmp_path / "api-key"
    key.write_text("token", encoding="utf-8")
    key.chmod(0o644)
    output = tmp_path / "runtime"
    output.mkdir(mode=0o700)
    settings = Settings("https://id.example.test", key, output, 10)
    with pytest.raises(ValueError, match="group or other permissions"):
        settings.validate()


def test_secret_file_name_cannot_escape_directory(tmp_path: Path) -> None:
    key = tmp_path / "api-key"
    key.write_text("token", encoding="utf-8")
    key.chmod(0o600)
    output = tmp_path / "runtime"
    output.mkdir(mode=0o700)
    settings = Settings("https://id.example.test", key, output, 10)
    settings.validate()
    with pytest.raises(ValueError, match="safe basename"):
        settings.secret_path("../escape")
