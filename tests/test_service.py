from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

import pytest

from pocket_id_mcp.config import Settings
from pocket_id_mcp.models import RestrictedClientCreateInput
from pocket_id_mcp.service import PocketIdService


class FakeClient:
    def __init__(self) -> None:
        self.created_payload: dict[str, Any] | None = None
        self.allowed_payload: dict[str, Any] | None = None
        self.deleted = False
        self.secret = "super-secret-value"
        self.client = {
            "id": "client-1",
            "name": "Proxmox VE",
            "callbackURLs": ["https://proxmox.example.test"],
            "logoutCallbackURLs": [],
            "isPublic": False,
            "pkceEnabled": False,
            "requiresReauthentication": False,
            "launchURL": None,
            "isGroupRestricted": True,
            "allowedUserGroups": [{"id": "group-1", "name": "admins", "friendlyName": "Admins"}],
        }

    def list_paginated(self, path: str, *, search: str | None = None):
        if path == "/api/user-groups":
            return [{"id": "group-1", "name": "admins", "friendlyName": "Admins"}]
        if path == "/api/oidc/clients":
            return []
        raise AssertionError(path)

    def request(self, method: str, path: str, payload=None, *, authenticated: bool = True):
        if method == "POST" and path == "/api/oidc/clients":
            self.created_payload = dict(payload)
            return {"id": "client-1"}
        if method == "PUT" and path.endswith("/allowed-user-groups"):
            self.allowed_payload = dict(payload)
            return self.client
        if method == "GET" and path == "/api/oidc/clients/client-1":
            return self.client
        if method == "POST" and path.endswith("/secret"):
            return {"secret": self.secret}
        if method == "DELETE" and path == "/api/oidc/clients/client-1":
            self.deleted = True
            return None
        raise AssertionError((method, path, payload))


def make_settings(tmp_path: Path) -> Settings:
    key = tmp_path / "api-key"
    key.write_text("test-token", encoding="utf-8")
    key.chmod(0o600)
    output = tmp_path / "runtime"
    output.mkdir(mode=0o700)
    return Settings("https://id.example.test", key, output, 10)


def test_create_restricted_client_verifies_exact_groups(tmp_path: Path) -> None:
    fake = FakeClient()
    service = PocketIdService(fake, make_settings(tmp_path))  # type: ignore[arg-type]
    result = service.create_restricted_client(
        RestrictedClientCreateInput(
            name="Proxmox VE",
            callback_urls=["https://proxmox.example.test"],
            allowed_group_names=["admins"],
        )
    )
    assert result["isGroupRestricted"] is True
    assert fake.created_payload is not None
    assert fake.created_payload["isGroupRestricted"] is True
    assert fake.created_payload["credentials"] == {"federatedIdentities": []}
    assert fake.allowed_payload == {"userGroupIds": ["group-1"]}
    assert fake.deleted is False


def test_create_restricted_client_rolls_back_failed_postcondition(tmp_path: Path) -> None:
    fake = FakeClient()
    fake.client["isGroupRestricted"] = False
    service = PocketIdService(fake, make_settings(tmp_path))  # type: ignore[arg-type]
    with pytest.raises(Exception, match="not group restricted"):
        service.create_restricted_client(
            RestrictedClientCreateInput(
                name="Proxmox VE",
                callback_urls=["https://proxmox.example.test"],
                allowed_group_names=["admins"],
            )
        )
    assert fake.deleted is True


def test_secret_is_written_without_being_returned(tmp_path: Path) -> None:
    fake = FakeClient()
    settings = make_settings(tmp_path)
    service = PocketIdService(fake, settings)  # type: ignore[arg-type]
    result = service.create_secret_file("client-1", "proxmox-secret")
    path = settings.secret_output_dir / "proxmox-secret"
    assert path.read_text(encoding="utf-8") == fake.secret
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert fake.secret not in repr(result)
    assert result["secret_written"] is True


def test_secret_file_refuses_overwrite(tmp_path: Path) -> None:
    fake = FakeClient()
    settings = make_settings(tmp_path)
    target = settings.secret_output_dir / "existing"
    target.write_text("keep", encoding="utf-8")
    target.chmod(0o600)
    service = PocketIdService(fake, settings)  # type: ignore[arg-type]
    with pytest.raises(FileExistsError):
        service.create_secret_file("client-1", "existing")
    assert target.read_text(encoding="utf-8") == "keep"
