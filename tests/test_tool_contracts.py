from __future__ import annotations

import asyncio

from pocket_id_mcp.server import list_tools


def test_all_pocket_id_tools_publish_complete_annotations() -> None:
    for tool in asyncio.run(list_tools()):
        annotations = tool.annotations
        assert annotations is not None
        assert annotations.readOnlyHint is not None
        assert annotations.destructiveHint is not None
        assert annotations.idempotentHint is not None
        assert annotations.openWorldHint is not None


def test_allowed_group_replacement_is_destructive() -> None:
    tools = {tool.name: tool for tool in asyncio.run(list_tools())}
    annotations = tools["oidc_client_set_allowed_groups"].annotations
    assert annotations is not None
    assert annotations.readOnlyHint is False
    assert annotations.destructiveHint is True
    assert annotations.idempotentHint is False
    assert annotations.openWorldHint is False
