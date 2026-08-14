# Tool reference

`pocket-id-mcp` exposes 12 explicit MCP tools. There is no generic Pocket ID HTTP request tool.

## Overview

| Tool | Access | Destructive | Purpose |
|---|---|---:|---|
| `pocket_id_health` | Read | No | Verify public OIDC discovery and authenticated Pocket ID API access. |
| `oidc_discovery` | Read | No | Return the bounded public OIDC discovery contract. |
| `oidc_client_list` | Read | No | List OIDC clients with secret-bearing fields omitted. |
| `oidc_client_get` | Read | No | Read one OIDC client with secret-bearing fields omitted. |
| `user_group_list` | Read | No | List Pocket ID user groups. |
| `user_group_get` | Read | No | Read one Pocket ID user group. |
| `user_list` | Read | No | List users with a bounded non-secret field set. |
| `user_get` | Read | No | Read one user with a bounded non-secret field set. |
| `oidc_client_create_restricted` | Write | No | Create and verify a group-restricted OIDC client. |
| `oidc_client_set_allowed_groups` | Write | Yes | Replace the exact allowed-group set on an already restricted client. |
| `oidc_client_create_secret_file` | Write | Yes | Rotate a confidential client secret and write it directly to a new private file. |
| `oidc_client_delete` | Write | Yes | Delete one OIDC client behind name-match and confirmation guards. |

All tools publish `openWorldHint=false`. Read-only tools publish `readOnlyHint=true` and `idempotentHint=true`. State-changing tools publish `readOnlyHint=false` and `idempotentHint=false`.

## Service and discovery

### `pocket_id_health`

Checks both the public OIDC discovery endpoint and authenticated API access.

**Input:** none.

**Output:** bounded health information including status, issuer, authenticated state and the observed user-group count.

**Side effects:** none.

### `oidc_discovery`

Returns a bounded subset of Pocket ID's public OIDC discovery metadata.

**Input:** none.

**Output:** supported fields can include issuer, authorization endpoint, token endpoint, user-info endpoint, JWKS URI, scopes and claims.

**Side effects:** none.

## OIDC client inventory

### `oidc_client_list`

Lists OIDC clients while omitting secret-bearing fields.

**Input:** optional `search` string, maximum 200 characters.

**Side effects:** none.

### `oidc_client_get`

Reads one OIDC client while omitting secret-bearing fields.

**Input:** `id` — Pocket ID OIDC client identifier.

**Side effects:** none.

## Identity inventory

### `user_group_list`

Lists Pocket ID user groups.

**Input:** optional `search` string, maximum 200 characters.

**Side effects:** none.

### `user_group_get`

Reads one Pocket ID user group.

**Input:** `id` — user-group identifier.

**Side effects:** none.

### `user_list`

Lists users using a bounded field set rather than returning arbitrary user objects.

**Input:** optional `search` string, maximum 200 characters.

**Output:** bounded user fields including ID, username, display name, email, disabled/admin state and minimal group metadata where available.

**Side effects:** none.

### `user_get`

Reads one user using the same bounded field set as `user_list`.

**Input:** `id` — user identifier.

**Side effects:** none.

## OIDC client administration

### `oidc_client_create_restricted`

Creates an OIDC client that is group restricted from the start, replaces its allowed groups with the exact requested set, reads it back and verifies security-relevant postconditions.

**Input:**

| Field | Required | Meaning |
|---|---:|---|
| `name` | yes | Client name, 1-50 characters. |
| `callback_urls` | yes | One or more callback URLs, maximum 20. |
| `allowed_group_names` | yes | Exact group-name set to attach, maximum 20. Duplicates and unknown names are rejected. |
| `logout_callback_urls` | no | Logout callback URLs, maximum 20. |
| `is_public` | no | Whether the OIDC client is public; default `false`. |
| `pkce_enabled` | no | Whether PKCE is enabled; default `false`. |
| `requires_reauthentication` | no | Reauthentication setting; default `false`. |
| `launch_url` | no | Optional launch URL. |
| `requested_client_id` | no | Optional requested client identifier. |

**Guards and postconditions:**

- refuses to create a client when an existing client has the same name;
- resolves every requested group name before applying the set;
- verifies the client remains group restricted and has exactly the requested groups;
- verifies name, callbacks and relevant security settings after creation;
- performs best-effort deletion of the newly created client when postcondition verification fails.

**Annotation:** state-changing but not marked destructive because the intended operation creates a new client rather than replacing or deleting existing state.

### `oidc_client_set_allowed_groups`

Replaces the complete allowed-group set for an existing group-restricted OIDC client.

**Input:**

- `client_id` — target OIDC client identifier;
- `allowed_group_names` — exact replacement set, one to 20 names.

**Guards and postconditions:**

- refuses to operate on a client that is not already group restricted;
- rejects duplicate or unknown group names;
- reads the client back and verifies the exact requested group set.

**Annotation:** destructive because the existing allowed-group set is replaced.

### `oidc_client_create_secret_file`

Rotates the secret of an existing confidential OIDC client and writes the new value directly to a new file inside `POCKET_ID_SECRET_OUTPUT_DIR`.

**Input:**

- `client_id` — target OIDC client identifier;
- `file_name` — safe basename for the new secret file, maximum 128 characters.

**Guards and postconditions:**

- refuses public OIDC clients;
- refuses unsafe file names and paths outside the configured secret directory;
- creates the destination exclusively and refuses overwrite;
- writes the generated secret with mode `0600` and verifies the resulting file type and mode;
- never returns the secret value in MCP output;
- removes an incomplete output file on write failure where possible;
- if Pocket ID has already rotated the secret but persistence fails, reports that another secret must be generated rather than pretending rollback occurred.

**Annotation:** destructive because rotating the client secret invalidates the previous secret.

### `oidc_client_delete`

Deletes one OIDC client.

**Input:**

- `client_id` — target OIDC client identifier;
- `expected_name` — expected current client name;
- `confirm` — must be `true`.

**Guards:**

- refuses deletion unless `confirm=true`;
- reads the target first and refuses deletion when its current name does not exactly match `expected_name`.

**Annotation:** destructive.

## Security boundary

Pocket ID's API authorization remains authoritative. Tool annotations describe MCP operation semantics; they do not grant permission to perform an operation. An MCP gateway or client should expose only the tools appropriate for its consumer; Pocket ID determines what the configured API key is authorized to do.

See [Security policy](../SECURITY.md) and the [README security model](../README.md#security-model).
