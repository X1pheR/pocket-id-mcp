# pocket-id-mcp

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/X1pheR/pocket-id-mcp/badge)](https://scorecard.dev/viewer/?uri=github.com/X1pheR/pocket-id-mcp)

A typed Model Context Protocol server for bounded administration of [Pocket ID](https://github.com/pocket-id/pocket-id) through its supported API.

This is a community-maintained integration and is not affiliated with, endorsed by, or officially maintained by the Pocket ID project.

The current public release is immutable `v0.1.0`, published through GitHub Releases with wheel/source artifacts and `SHA256SUMS`. The package is not published to PyPI.

## Design

`pocket-id-mcp` maps a deliberately bounded set of Pocket ID administration workflows to explicit MCP tools instead of exposing a generic HTTP request primitive. This keeps tool inputs discoverable, lets MCP clients distinguish read-only and destructive operations, and keeps API keys and generated OIDC client secrets outside model-visible arguments and output.

The server focuses on OIDC client administration and read-only identity inventory. It deliberately does not mirror the complete Pocket ID API.

## Requirements

- Python 3.12 or newer
- a reachable Pocket ID instance
- a Pocket ID API key with the permissions required by the operations you intend to use
- a private file containing that API key
- a private directory for generated confidential OIDC client secret files when using secret-rotation tools

The tested compatibility baseline is Pocket ID `v2.7.0`. Newer Pocket ID releases are not implied supported until they have been validated separately.

## Install

Download the wheel for the desired release from GitHub Releases and verify it against the published `SHA256SUMS` file before installation.

For example, after downloading the current release artifacts:

```bash
sha256sum -c SHA256SUMS
python -m venv .venv
. .venv/bin/activate
pip install pocket_id_mcp-0.1.0-py3-none-any.whl
```

The GitHub release tag provides the corresponding source snapshot.

## Configuration

The server uses these environment variables:

| Variable | Required | Default | Purpose |
|---|---:|---|---|
| `POCKET_ID_BASE_URL` | yes | - | Pocket ID origin, for example `https://id.example.com` |
| `POCKET_ID_API_KEY_FILE` | yes | - | Private regular file containing the Pocket ID API key |
| `POCKET_ID_SECRET_OUTPUT_DIR` | for secret-generation tools | - | Private directory for generated confidential OIDC client secret files |
| `POCKET_ID_REQUEST_TIMEOUT_SECONDS` | no | `15` | Per-request timeout in seconds |

The API key is read from the configured file at startup and is never exposed as an MCP tool argument or returned by a tool.

Generated confidential OIDC client secrets are written directly to exclusive mode-`0600` files under `POCKET_ID_SECRET_OUTPUT_DIR`. Secret values are never returned through MCP.

## Running

With the package installed and configuration present:

```bash
pocket-id-mcp
```

The server speaks MCP over standard input/output.

## Tool surface

The public surface contains 12 curated tools:

### Users and groups

- `user_list`
- `user_get`
- `user_group_list`
- `user_group_get`

### OIDC clients

- `oidc_client_list`
- `oidc_client_get`
- `oidc_client_create_restricted`
- `oidc_client_update_restricted`
- `oidc_client_delete`
- `oidc_client_create_secret_file`
- `oidc_client_replace_allowed_groups`
- `oidc_client_rotate_secret_file`

See [docs/tools.md](docs/tools.md) for the complete input, output, safety and confirmation contract for each tool.

## Deliberate exclusions

The server intentionally does **not** expose:

- raw or generic HTTP request execution;
- Pocket ID API-key administration;
- application-wide configuration administration;
- signup-token administration;
- SCIM administration;
- general user mutation;
- image management;
- plaintext API keys or generated client secrets.

These exclusions are part of the security boundary, not missing convenience features.

## Security behavior

- The API key is file-backed and never model visible.
- Generated confidential OIDC client secrets are written directly to exclusive mode-`0600` files and never returned.
- Remote requests are restricted to the configured Pocket ID origin; there is no raw request tool.
- HTTP failures are translated to bounded errors rather than returning arbitrary upstream response bodies.
- Restricted-client creation verifies the resulting allowed-group and public-client state; failed verification triggers best-effort cleanup.
- Allowed-group replacement refuses clients that are not already group restricted.
- OIDC client deletion requires the current client name and explicit confirmation.
- MCP tool annotations mark read-only/destructive behavior and set `openWorldHint=false` because tools operate only against the configured Pocket ID instance.
- Pocket ID remains the authorization boundary. The MCP does not add a second RBAC layer.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and the maintained security boundary.
See [Secure Development](docs/SECURE-DEVELOPMENT.md) for the project-specific secure-design model and common vulnerability mitigations.

## Development

```bash
uv sync --frozen --extra test
uv run --frozen --extra test pytest -q
uv build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution expectations and [CHANGELOG.md](CHANGELOG.md) for release history.

## Release and provenance

`v0.1.0` is the current immutable release. Future releases are created from exact tags through the maintained GitHub release workflow, publish `SHA256SUMS`, and attach signed GitHub/Sigstore build provenance.

## License

MIT. See [LICENSE](LICENSE).
