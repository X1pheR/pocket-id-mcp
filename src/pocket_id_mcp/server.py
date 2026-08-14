from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, TypeVar

import mcp.types as types
from mcp.server import Server
from pydantic import BaseModel, ValidationError

from .api import PocketIdClient, PocketIdError
from .config import Settings
from .models import (
    DeleteClientInput,
    EmptyInput,
    IdentifierInput,
    RestrictedClientCreateInput,
    SearchInput,
    SecretFileInput,
    SetAllowedGroupsInput,
)
from .service import PocketIdService

app = Server("pocket-id")
_settings: Settings
_service: PocketIdService
ModelT = TypeVar("ModelT", bound=BaseModel)


def _annotations(*, read_only: bool, destructive: bool = False) -> types.ToolAnnotations:
    return types.ToolAnnotations(
        readOnlyHint=read_only,
        destructiveHint=destructive,
        idempotentHint=read_only,
        openWorldHint=False,
    )


def _tool(
    name: str,
    description: str,
    model: type[BaseModel],
    *,
    read_only: bool,
    destructive: bool = False,
) -> types.Tool:
    return types.Tool(
        name=name,
        description=description,
        inputSchema=model.model_json_schema(),
        annotations=_annotations(read_only=read_only, destructive=destructive),
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        _tool(
            "pocket_id_health",
            "Check Pocket ID discovery and authenticated API access without changing state.",
            EmptyInput,
            read_only=True,
        ),
        _tool(
            "oidc_discovery",
            "Return the bounded public OIDC discovery contract for the configured Pocket ID issuer.",
            EmptyInput,
            read_only=True,
        ),
        _tool(
            "oidc_client_list",
            "List Pocket ID OIDC clients with secret-bearing fields omitted.",
            SearchInput,
            read_only=True,
        ),
        _tool(
            "oidc_client_get",
            "Get one Pocket ID OIDC client with secret-bearing fields omitted.",
            IdentifierInput,
            read_only=True,
        ),
        _tool(
            "user_group_list",
            "List Pocket ID user groups without changing Pocket ID state.",
            SearchInput,
            read_only=True,
        ),
        _tool(
            "user_group_get",
            "Get one Pocket ID user group without changing Pocket ID state.",
            IdentifierInput,
            read_only=True,
        ),
        _tool(
            "user_list",
            "List Pocket ID users with a bounded non-secret field set.",
            SearchInput,
            read_only=True,
        ),
        _tool(
            "user_get",
            "Get one Pocket ID user with a bounded non-secret field set.",
            IdentifierInput,
            read_only=True,
        ),
        _tool(
            "oidc_client_create_restricted",
            "Create a group-restricted OIDC client, attach the exact requested groups, verify all security-relevant postconditions, and best-effort delete the client if verification fails.",
            RestrictedClientCreateInput,
            read_only=False,
        ),
        _tool(
            "oidc_client_set_allowed_groups",
            "Replace the exact allowed-group set of an OIDC client that is already group restricted and verify the postcondition.",
            SetAllowedGroupsInput,
            read_only=False,
            destructive=True,
        ),
        _tool(
            "oidc_client_create_secret_file",
            "Rotate a confidential OIDC client secret and write it directly to a new exclusive mode-0600 file in the configured secret directory. The secret value is never returned.",
            SecretFileInput,
            read_only=False,
            destructive=True,
        ),
        _tool(
            "oidc_client_delete",
            "Delete one OIDC client only when its current name matches expected_name and confirm is true.",
            DeleteClientInput,
            read_only=False,
            destructive=True,
        ),
    ]


def _validate(model: type[ModelT], arguments: Any) -> ModelT:
    return model.model_validate(arguments or {})


@app.call_tool()
async def call_tool(
    name: str, arguments: Any
) -> Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    try:
        if name == "pocket_id_health":
            _validate(EmptyInput, arguments)
            result = _service.health()
        elif name == "oidc_discovery":
            _validate(EmptyInput, arguments)
            result = _service.discovery()
        elif name == "oidc_client_list":
            args = _validate(SearchInput, arguments)
            result = _service.list_clients(args.search)
        elif name == "oidc_client_get":
            args = _validate(IdentifierInput, arguments)
            result = _service.get_client(args.id)
        elif name == "user_group_list":
            args = _validate(SearchInput, arguments)
            result = _service.list_groups(args.search)
        elif name == "user_group_get":
            args = _validate(IdentifierInput, arguments)
            result = _service.get_group(args.id)
        elif name == "user_list":
            args = _validate(SearchInput, arguments)
            result = _service.list_users(args.search)
        elif name == "user_get":
            args = _validate(IdentifierInput, arguments)
            result = _service.get_user(args.id)
        elif name == "oidc_client_create_restricted":
            args = _validate(RestrictedClientCreateInput, arguments)
            result = _service.create_restricted_client(args)
        elif name == "oidc_client_set_allowed_groups":
            args = _validate(SetAllowedGroupsInput, arguments)
            result = _service.set_allowed_groups(
                args.client_id, args.allowed_group_names
            )
        elif name == "oidc_client_create_secret_file":
            args = _validate(SecretFileInput, arguments)
            result = _service.create_secret_file(args.client_id, args.file_name)
        elif name == "oidc_client_delete":
            args = _validate(DeleteClientInput, arguments)
            result = _service.delete_client(
                args.client_id, args.expected_name, args.confirm
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
    except ValidationError as error:
        raise ValueError(f"Invalid tool input: {error}") from None
    except (PocketIdError, ValueError) as error:
        raise RuntimeError(str(error)) from None

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True),
        )
    ]


async def run_stdio(settings: Settings, service: PocketIdService) -> None:
    from mcp.server.stdio import stdio_server

    global _settings, _service
    _settings = settings
    _service = service
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
