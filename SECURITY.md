# Security Policy

## Supported versions

The latest maintained release line is the supported public baseline unless a release note states otherwise. Security fixes are developed on `main` and released through the normal versioned release lifecycle.

## Reporting a vulnerability

Do not disclose a suspected vulnerability in a public issue or pull request.

Use [GitHub private vulnerability reporting](https://github.com/X1pheR/pocket-id-mcp/security/advisories/new) for this repository. If that channel is unexpectedly unavailable, create a public issue containing no sensitive details and ask the maintainer to establish a private contact channel before sharing the report.

Include enough information to reproduce and assess the issue, but do not include real Pocket ID API keys, generated OIDC client secrets, private infrastructure details, personal data or other credentials.

## Dependency and code security

The repository uses locked Python dependencies, full-SHA-pinned GitHub Actions, frozen CI/package verification, Dependabot and OpenSSF Scorecard. Public-release acceptance also requires applicable GitHub-native dependency alerts, secret scanning with push protection and CodeQL code scanning to be reviewed and green before a release is published.

These scanners supplement rather than replace source/history review and the project test suite.
