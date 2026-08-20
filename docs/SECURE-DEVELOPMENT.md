# Secure Development

This document records the project-specific secure-design model and common vulnerability classes considered when maintaining `pocket-id-mcp`.

It complements [SECURITY.md](../SECURITY.md), which owns vulnerability reporting and the maintained public security boundary.

## Security design principles

### Economy of mechanism

Keep the MCP surface small and explicit. Prefer narrowly typed Pocket ID operations over generic request primitives, hidden dispatch, or broad administrative abstractions.

### Fail-safe defaults

Reject ambiguous or incomplete security-sensitive requests. Destructive client deletion requires the current client name plus explicit confirmation. Group-restriction replacement refuses clients that are not already group restricted. Restricted-client creation verifies its security-relevant postconditions and performs best-effort cleanup if verification fails.

### Complete mediation

Validate every tool invocation at the MCP boundary and again where an external or filesystem boundary requires it. Requests are constrained to the configured Pocket ID origin; identifiers, names, callbacks, group restrictions, confirmation values and local secret-file paths are not treated as implicitly trusted.

### Open design

Do not depend on hidden mechanisms for safety. The public README, tool reference and security documentation describe the bounded surface, intentional exclusions, destructive confirmation rules and secret-handling model.

### Least privilege

Expose only the Pocket ID capabilities needed by the maintained MCP workflows. Keep broad user mutation, API-key administration, signup-token administration, SCIM administration, application-wide configuration, image management and raw HTTP outside the public tool surface. Pocket ID remains the authorization authority; the MCP does not introduce a second RBAC system or attempt to bypass Pocket ID policy.

### Least common mechanism

Keep credentials and generated confidential client secrets outside shared model-visible channels. The Pocket ID API key is read from a private file. Generated OIDC client secrets are written directly to protected files rather than being returned through MCP.

### Psychological acceptability

Make safe use straightforward: typed tools describe the operation they perform, destructive actions require explicit confirmation, and configuration uses documented file-backed secret boundaries instead of hidden credential channels.

### Limited attack surface

There is no generic HTTP request tool. Remote requests are restricted to one configured Pocket ID origin. The server exposes a deliberately curated administration surface rather than mirroring the complete Pocket ID API.

### Allowlist-oriented validation

Prefer explicit accepted fields, bounded values and known operation shapes over generic dictionaries or pass-through remote request data. New tools should preserve this model unless a reviewed requirement proves that a broader interface is necessary.

## Common vulnerability classes and mitigations

### Credential or secret disclosure

Risks include Pocket ID API keys or generated confidential OIDC client secrets entering MCP arguments, responses, exceptions, logs, fixtures, issues, commits or CI output.

Mitigations:

- read the API key only from the configured private file;
- never return the API key through MCP;
- write generated confidential OIDC client secrets directly to the configured private output directory with exclusive mode-`0600` semantics;
- never return generated client secrets through MCP;
- keep production secrets out of tests, fixtures, logs, issues and commits;
- use GitHub Secret Scanning and Push Protection as supplementary repository controls.

### Unsafe local file access

Risks include arbitrary path reads/writes, symlink or permission mistakes, and secret output escaping the intended private directory.

Mitigations:

- expose no generic filesystem tool through this product;
- keep API-key and generated-secret paths behind explicit configuration contracts;
- require protected regular-file/private-directory boundaries;
- create confidential secret outputs exclusively rather than overwriting arbitrary model-selected paths.

### Authorization bypass or confused deputy behavior

Risks include making an administrator-level API request that is broader than the caller expects or using the MCP to bypass Pocket ID authorization semantics.

Mitigations:

- Pocket ID remains the authorization boundary;
- the MCP exposes only explicit bounded operations;
- broad user and application administration surfaces are intentionally excluded;
- group-restriction replacement refuses clients that are not already group restricted;
- security-sensitive creation verifies the resulting Pocket ID state before reporting success.

### Over-broad remote request or SSRF-style escape

Risks include a generic request primitive reaching attacker-controlled or unintended origins.

Mitigations:

- do not expose a raw HTTP request tool;
- derive API requests from the single configured Pocket ID origin;
- keep endpoint paths and HTTP methods internal to explicit typed tool implementations.

### Unsafe destructive operations

Risks include deleting the wrong OIDC client or treating an ambiguous caller instruction as authorization.

Mitigations:

- require the target client's current name as a human-readable guard;
- require explicit confirmation for deletion;
- fail closed when guards do not match;
- do not add generic destructive request capabilities.

### Injection and malformed structured input

Risks include malformed callback URLs, names, identifiers, group values or pass-through structures altering the intended API operation.

Mitigations:

- use typed MCP schemas and bounded fields;
- build remote request shapes internally instead of accepting arbitrary method/path/body triples;
- validate tool-specific preconditions before performing mutations.

### Sensitive error propagation

Risks include upstream Pocket ID responses or local exceptions leaking credentials, confidential client secrets, private endpoints or personal data.

Mitigations:

- return bounded safe HTTP errors;
- do not copy raw secret-bearing payloads into tool errors;
- keep private values out of diagnostic examples and test fixtures.

### Dependency and workflow supply-chain compromise

Risks include vulnerable Python dependencies, mutable CI actions, compromised release steps or artifacts that cannot be tied to reviewed source.

Mitigations:

- resolve Python dependencies through the committed `uv.lock`;
- pin GitHub Actions to full commit SHAs;
- use Dependabot for maintained dependency/update paths;
- run CodeQL and GitHub-native security checks;
- require frozen CI/build validation;
- publish checksums and signed GitHub/Sigstore provenance for future releases;
- preserve immutable accepted release history instead of rewriting it after publication.

### Compatibility drift causing unsafe behavior

Risks include a newer Pocket ID version changing API semantics so a previously safe precondition, response assumption or postcondition check no longer means what the MCP expects.

Mitigations:

- document Pocket ID `v2.7.0` as the tested compatibility baseline;
- do not imply untested newer Pocket ID releases are supported;
- revalidate security-sensitive workflows when advancing the upstream compatibility baseline.

## Review expectations

Security-sensitive changes should:

- preserve or reduce the exposed MCP and credential surface;
- add or update focused tests where practical;
- update the tool/security documentation when a boundary changes;
- keep production credentials, generated secrets, private endpoints and personal data out of tests, fixtures, logs, issues and commits;
- pass the maintained frozen test/build and repository security checks before merge.

The OpenSSF `know_secure_design` and `know_common_errors` criteria are personal maintainer self-certifications. This document demonstrates how those principles are applied to `pocket-id-mcp`; it does not substitute for the maintainer's own certification.
