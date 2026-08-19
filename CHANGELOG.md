# Changelog

This file records user-visible changes to `pocket-id-mcp`. Security fixes with a public CVE or equivalent identifier are called out explicitly in the release that fixes them.

## Unreleased

- Added public OpenSSF Scorecard reporting and protected-branch repository controls.
- Future releases publish signed GitHub/Sigstore build provenance alongside checksums and reproducible package artifacts.
- Added explicit contribution and private vulnerability-reporting routes.

## 0.1.0 - 2026-08-14

Initial public release.

- Added 12 typed MCP tools for Pocket ID health/discovery, OIDC client inventory and bounded administration, user/group inventory, and restricted-client lifecycle workflows.
- Kept Pocket ID API keys and generated confidential OIDC client secrets outside model-visible tool arguments and responses.
- Added verified group-restriction and delete-confirmation guards for security-relevant OIDC client mutations.
- Published wheel and source artifacts with `SHA256SUMS` and established Pocket ID `v2.7.0` as the tested compatibility baseline.
