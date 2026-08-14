# Pocket ID MCP

Small MCP server for bounded Pocket ID administration through the supported Pocket ID API.

## Scope

The server intentionally exposes only:

- health and OIDC discovery;
- read-only OIDC client, user-group and user inventory;
- creation of group-restricted OIDC clients with verified postconditions;
- replacement of allowed groups on an already restricted client;
- generation of a confidential client secret directly into a protected file;
- guarded OIDC client deletion.

It does not expose arbitrary HTTP requests, API-key management, application configuration, signup tokens, SCIM administration, user mutation or image management.

## Configuration

```text
POCKET_ID_BASE_URL=https://id.example.com
POCKET_ID_API_KEY_FILE=/run/secrets/pocket-id-api-key
POCKET_ID_SECRET_OUTPUT_DIR=/run/secrets/pocket-id-mcp
POCKET_ID_REQUEST_TIMEOUT_SECONDS=10
```

`POCKET_ID_API_KEY_FILE` must point to a regular file with no group or other permissions. `POCKET_ID_SECRET_OUTPUT_DIR` must already exist and have no group or other permissions. The server accepts no API key or generated client secret as an MCP tool argument and never returns those secret values in tool output.

## Run from a checkout

Python 3.12 or newer and `uv` are required.

```bash
uv sync --frozen
uv run --frozen pocket-id-mcp
```

An MCP client should start the command as a stateful STDIO child process and provide the required configuration in its process environment.

## Security properties

- API calls use only the configured Pocket ID origin.
- HTTP errors are bounded and reduced to a status plus a safe message.
- Restricted-client creation is a compound operation: create, attach exact groups, read back, verify, and best-effort delete on failure.
- Client-secret generation opens an exclusive mode-`0600` file before rotating the secret and never returns the secret value.
- Delete requires the current client name and an explicit boolean confirmation.

See [SECURITY.md](SECURITY.md) for vulnerability reporting after the repository hardening commit.

## License

MIT. See [LICENSE](LICENSE).
