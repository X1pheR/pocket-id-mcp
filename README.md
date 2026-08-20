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
- Pocket ID v2.7.0 as the tested compatibility baseline
- a Pocket ID API key that can perform the Pocket ID operations exposed by the tools you intend to use
- an MCP client or gateway that supports STDIO servers
- `uv` for the documented source workflow

Newer Pocket ID versions are unverified unless explicitly documented as supported.

## Configuration

| Variable | Required | Default | Meaning |
|---|---:|---|---|
| `POCKET_ID_BASE_URL` | yes | - | Pocket ID HTTP(S) origin without a path, for example `https://id.example.com`. |
| `POCKET_ID_API_KEY_FILE` | yes | - | Private regular file containing one Pocket ID API key. Group/other permissions are rejected. |
| `POCKET_ID_SECRET_OUTPUT_DIR` | yes | - | Existing private directory where generated confidential OIDC client secrets may be written. Group/other permissions are rejected. |
| `POCKET_ID_REQUEST_TIMEOUT_SECONDS` | no | `10` | Per-request timeout in seconds, greater than zero and at most 120. |

Example MCP registration from a source checkout:

```json
{
  "mcpServers": {
    "pocket-id": {
      "command": "uv",
      "args": [
        "run",
        "--frozen",
        "--directory",
        "/path/to/pocket-id-mcp",
        "pocket-id-mcp"
      ],
      "env": {
        "POCKET_ID_BASE_URL": "https://id.example.com",
        "POCKET_ID_API_KEY_FILE": "/run/secrets/pocket-id-api-key",
        "POCKET_ID_SECRET_OUTPUT_DIR": "/run/secrets/pocket-id-mcp"
      }
    }
  }
}
```

The API-key file and secret-output directory must already exist with private permissions before the server starts.

## MCP surface

The current source exposes 12 curated tools:

| Area | Tools | Access |
|---|---:|---|
| Service and OIDC discovery | 2 | Read-only |
| OIDC client inventory | 2 | Read-only |
| User-group and user inventory | 4 | Read-only |
| OIDC client administration | 4 | State-changing; three tools are marked destructive |

See the [Tool reference](docs/tools.md) for the complete tool table, inputs, side effects, annotations and security-relevant postconditions.

## Feedback and contributions

Use [GitHub Issues](https://github.com/X1pheR/pocket-id-mcp/issues) for bug reports and feature requests and pull requests for proposed changes. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow, test requirements, and change expectations. Security issues must follow the private process in [SECURITY.md](SECURITY.md).

User-visible release changes are summarized in [CHANGELOG.md](CHANGELOG.md).

## Running from source

The repository includes `uv.lock` for a reproducible source environment.

```bash
uv sync --frozen
POCKET_ID_BASE_URL=https://id.example.com \
POCKET_ID_API_KEY_FILE=/run/secrets/pocket-id-api-key \
POCKET_ID_SECRET_OUTPUT_DIR=/run/secrets/pocket-id-mcp \
uv run --frozen pocket-id-mcp
```

## Security model

- The Pocket ID API key is read from a private local file and is never accepted as an MCP tool argument.
- Generated confidential OIDC client secrets are written directly to a new exclusive mode-`0600` file and are never returned in MCP output.
- API calls are restricted to the configured Pocket ID origin; there is no raw request tool.
- HTTP error bodies are reduced to bounded safe messages rather than returned verbatim.
- Restricted-client creation attaches the exact requested groups and verifies security-relevant postconditions. A failed verification triggers best-effort cleanup of the newly created client.
- Allowed-group replacement refuses to operate on an OIDC client that is not already group restricted.
- OIDC client deletion requires both the current client name and an explicit confirmation flag.
- All tools publish MCP annotations with `openWorldHint=false`; read and destructive semantics are documented in the [Tool reference](docs/tools.md).
- Pocket ID remains the authorization boundary. This MCP does not add a second RBAC or authorization model.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and the maintained security boundary.
See [Secure Development](docs/SECURE-DEVELOPMENT.md) for the project-specific secure-design model and common vulnerability mitigations.

## Deliberate exclusions

The server does not expose:

- arbitrary or raw Pocket ID HTTP requests;
- Pocket ID API-key administration;
- application-wide Pocket ID configuration;
- signup-token administration;
- SCIM administration;
- user mutation;
- image management;
- plaintext API keys or generated OIDC client secrets as MCP inputs or output.

These are product and security boundaries, not missing generic escape hatches.

## Compatibility

Pocket ID v2.7.0 is the tested compatibility baseline for the current `0.1.0` source. Support for other Pocket ID versions is unverified unless it is explicitly documented and covered by validation.

## Development

```bash
uv sync --frozen --extra test
uv run --frozen --extra test pytest -q
uv build
```

GitHub CI runs the same frozen dependency, test and package-build checks. Dependency updates are proposed by Dependabot and remain subject to compatibility review. OpenSSF Scorecard runs on `main` and weekly and publishes its public result for independent repository-security review.

Normal development does not publish a release. An accepted strict SemVer tag (`vMAJOR.MINOR.PATCH`) triggers the release workflow, which verifies the exact tag/source/package version, reruns frozen tests, proves two independent wheel/source builds are byte-identical, generates signed GitHub/Sigstore build provenance for the release artifacts, creates a draft release, attaches artifacts plus `SHA256SUMS` and the provenance bundle, and only then publishes the release.

## License

`pocket-id-mcp` is licensed under the MIT License. See [LICENSE](LICENSE).

Pocket ID is a separate upstream project with its own license and project governance.
