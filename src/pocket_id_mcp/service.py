from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

from .api import PocketIdClient, PocketIdError
from .config import Settings
from .models import RestrictedClientCreateInput


def _minimal_group(group: dict[str, Any]) -> dict[str, Any]:
    return {
        key: group.get(key)
        for key in ("id", "name", "friendlyName", "userCount")
        if key in group
    }


def _minimal_user(user: dict[str, Any]) -> dict[str, Any]:
    groups = user.get("userGroups")
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "displayName": user.get("displayName"),
        "email": user.get("email"),
        "disabled": user.get("disabled"),
        "isAdmin": user.get("isAdmin"),
        "userGroups": [
            _minimal_group(group) for group in groups if isinstance(group, dict)
        ]
        if isinstance(groups, list)
        else [],
    }


def _minimal_client(client: dict[str, Any]) -> dict[str, Any]:
    allowed = client.get("allowedUserGroups")
    result = {
        key: client.get(key)
        for key in (
            "id",
            "name",
            "callbackURLs",
            "logoutCallbackURLs",
            "isPublic",
            "pkceEnabled",
            "requiresReauthentication",
            "launchURL",
            "isGroupRestricted",
            "allowedUserGroupsCount",
        )
        if key in client
    }
    if isinstance(allowed, list):
        result["allowedUserGroups"] = [
            _minimal_group(group) for group in allowed if isinstance(group, dict)
        ]
    return result


class PocketIdService:
    def __init__(self, client: PocketIdClient, settings: Settings):
        self.client = client
        self.settings = settings

    def discovery(self) -> dict[str, Any]:
        value = self.client.request(
            "GET", "/.well-known/openid-configuration", authenticated=False
        )
        if not isinstance(value, dict):
            raise PocketIdError("Pocket ID discovery response has an unexpected shape")
        allowed = (
            "issuer",
            "authorization_endpoint",
            "token_endpoint",
            "userinfo_endpoint",
            "jwks_uri",
            "scopes_supported",
            "claims_supported",
        )
        return {key: value.get(key) for key in allowed if key in value}

    def health(self) -> dict[str, Any]:
        discovery = self.discovery()
        groups = self.client.list_paginated("/api/user-groups")
        return {
            "status": "ok",
            "issuer": discovery.get("issuer"),
            "authenticated": True,
            "groupCount": len(groups),
        }

    def list_clients(self, search: str | None = None) -> list[dict[str, Any]]:
        return [
            _minimal_client(client)
            for client in self.client.list_paginated("/api/oidc/clients", search=search)
        ]

    def get_client(self, client_id: str) -> dict[str, Any]:
        value = self.client.request("GET", f"/api/oidc/clients/{client_id}")
        if not isinstance(value, dict):
            raise PocketIdError("Pocket ID client response has an unexpected shape")
        return _minimal_client(value)

    def list_groups(self, search: str | None = None) -> list[dict[str, Any]]:
        return [
            _minimal_group(group)
            for group in self.client.list_paginated("/api/user-groups", search=search)
        ]

    def get_group(self, group_id: str) -> dict[str, Any]:
        value = self.client.request("GET", f"/api/user-groups/{group_id}")
        if not isinstance(value, dict):
            raise PocketIdError("Pocket ID group response has an unexpected shape")
        return _minimal_group(value)

    def list_users(self, search: str | None = None) -> list[dict[str, Any]]:
        return [
            _minimal_user(user)
            for user in self.client.list_paginated("/api/users", search=search)
        ]

    def get_user(self, user_id: str) -> dict[str, Any]:
        value = self.client.request("GET", f"/api/users/{user_id}")
        if not isinstance(value, dict):
            raise PocketIdError("Pocket ID user response has an unexpected shape")
        return _minimal_user(value)

    def _resolve_group_ids(self, names: list[str]) -> tuple[list[str], list[str]]:
        if len(set(names)) != len(names):
            raise ValueError("allowed_group_names must not contain duplicates")
        groups = self.client.list_paginated("/api/user-groups")
        by_name = {
            group.get("name"): group
            for group in groups
            if isinstance(group.get("name"), str)
        }
        missing = [name for name in names if name not in by_name]
        if missing:
            raise ValueError("Unknown Pocket ID group name(s): " + ", ".join(missing))
        ids = [str(by_name[name]["id"]) for name in names]
        return ids, names

    def _replace_allowed_groups(
        self, client_id: str, group_names: list[str]
    ) -> dict[str, Any]:
        group_ids, expected_names = self._resolve_group_ids(group_names)
        self.client.request(
            "PUT",
            f"/api/oidc/clients/{client_id}/allowed-user-groups",
            {"userGroupIds": group_ids},
        )
        verified = self.client.request("GET", f"/api/oidc/clients/{client_id}")
        if not isinstance(verified, dict):
            raise PocketIdError("Pocket ID client verification response has an unexpected shape")
        if verified.get("isGroupRestricted") is not True:
            raise PocketIdError("OIDC client is not group restricted after group update")
        actual_names = sorted(
            str(group.get("name"))
            for group in verified.get("allowedUserGroups", [])
            if isinstance(group, dict)
        )
        if actual_names != sorted(expected_names):
            raise PocketIdError(
                "OIDC client allowed groups do not match the requested exact set"
            )
        return _minimal_client(verified)

    def create_restricted_client(
        self, args: RestrictedClientCreateInput
    ) -> dict[str, Any]:
        existing = self.client.list_paginated("/api/oidc/clients")
        if any(client.get("name") == args.name for client in existing):
            raise ValueError(f"An OIDC client named {args.name!r} already exists")
        payload: dict[str, Any] = {
            "name": args.name,
            "callbackURLs": args.callback_urls,
            "logoutCallbackURLs": args.logout_callback_urls,
            "isPublic": args.is_public,
            "pkceEnabled": args.pkce_enabled,
            "requiresReauthentication": args.requires_reauthentication,
            "credentials": {"federatedIdentities": []},
            "launchURL": args.launch_url,
            "hasLogo": False,
            "hasDarkLogo": False,
            "logoUrl": None,
            "darkLogoUrl": None,
            "isGroupRestricted": True,
        }
        if args.requested_client_id is not None:
            payload["id"] = args.requested_client_id
        created = self.client.request("POST", "/api/oidc/clients", payload)
        if not isinstance(created, dict) or not isinstance(created.get("id"), str):
            raise PocketIdError("Pocket ID create-client response has an unexpected shape")
        client_id = created["id"]
        try:
            verified = self._replace_allowed_groups(
                client_id, args.allowed_group_names
            )
            checks = {
                "name": verified.get("name") == args.name,
                "callbackURLs": verified.get("callbackURLs") == args.callback_urls,
                "logoutCallbackURLs": verified.get("logoutCallbackURLs")
                == args.logout_callback_urls,
                "isPublic": verified.get("isPublic") is args.is_public,
                "pkceEnabled": verified.get("pkceEnabled") is args.pkce_enabled,
                "requiresReauthentication": verified.get("requiresReauthentication")
                is args.requires_reauthentication,
                "isGroupRestricted": verified.get("isGroupRestricted") is True,
            }
            failed = [name for name, passed in checks.items() if not passed]
            if failed:
                raise PocketIdError(
                    "OIDC client postcondition verification failed: " + ", ".join(failed)
                )
            return verified
        except Exception:
            try:
                self.client.request("DELETE", f"/api/oidc/clients/{client_id}")
            except Exception:
                pass
            raise

    def set_allowed_groups(
        self, client_id: str, group_names: list[str]
    ) -> dict[str, Any]:
        current = self.client.request("GET", f"/api/oidc/clients/{client_id}")
        if not isinstance(current, dict):
            raise PocketIdError("Pocket ID client response has an unexpected shape")
        if current.get("isGroupRestricted") is not True:
            raise ValueError("Refusing to assign groups to an unrestricted OIDC client")
        return self._replace_allowed_groups(client_id, group_names)

    def create_secret_file(self, client_id: str, file_name: str) -> dict[str, Any]:
        current = self.client.request("GET", f"/api/oidc/clients/{client_id}")
        if not isinstance(current, dict):
            raise PocketIdError("Pocket ID client response has an unexpected shape")
        if current.get("isPublic") is not False:
            raise ValueError("Client secrets are only supported for confidential OIDC clients")
        target = self.settings.secret_path(file_name)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(target, flags, 0o600)
        generated = False
        try:
            value = self.client.request(
                "POST", f"/api/oidc/clients/{client_id}/secret"
            )
            if not isinstance(value, dict) or not isinstance(value.get("secret"), str):
                raise PocketIdError("Pocket ID secret response has an unexpected shape")
            secret = value["secret"]
            generated = True
            encoded = secret.encode("utf-8")
            with os.fdopen(descriptor, "wb", closefd=True) as handle:
                descriptor = -1
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(target, 0o600)
            info = target.lstat()
            if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600:
                raise PocketIdError("Generated secret file did not retain mode 0600")
            return {
                "client_id": client_id,
                "client_name": current.get("name"),
                "secret_written": True,
                "secret_file": str(target),
                "secret_bytes": len(encoded),
                "permissions": "0600",
            }
        except Exception:
            if descriptor >= 0:
                os.close(descriptor)
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
            if generated:
                raise PocketIdError(
                    "A new client secret was generated but could not be persisted; generate another secret"
                ) from None
            raise

    def delete_client(
        self, client_id: str, expected_name: str, confirm: bool
    ) -> dict[str, Any]:
        if confirm is not True:
            raise ValueError("confirm must be true for OIDC client deletion")
        current = self.client.request("GET", f"/api/oidc/clients/{client_id}")
        if not isinstance(current, dict):
            raise PocketIdError("Pocket ID client response has an unexpected shape")
        if current.get("name") != expected_name:
            raise ValueError("OIDC client name does not match expected_name")
        self.client.request("DELETE", f"/api/oidc/clients/{client_id}")
        return {"deleted": True, "client_id": client_id, "name": expected_name}
