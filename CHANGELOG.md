# Changelog

This file records user-visible changes to `pocket-id-mcp`. Security fixes with a public CVE or equivalent identifier are called out explicitly in the release that fixes them.

## Unreleased

## 0.1.1 - 2026-08-24

- Added Pocket ID v2.14.0 compatibility for the multi-secret OIDC client lifecycle: bounded secret inventory, zero-downtime secret creation into a private file, optional expiry metadata, and guarded single-secret deletion.
- Added bounded light/dark OIDC-client logo upload/delete from an explicitly configured local asset directory without arbitrary filesystem reads or remote image fetching.
- Expanded the curated MCP surface from 12 to 16 tools and updated operation annotations for the Pocket ID 2.14 semantics.
- Added public OpenSSF Scorecard reporting, protected-branch repository controls, signed GitHub/Sigstore build provenance, and explicit contribution/private vulnerability-reporting routes.

## 0.1.0 - 2026-08-14

Initial public release.

- Added 12 typed MCP tools for Pocket ID health/discovery, OIDC client inventory and bounded administration, user/group inventory, and restricted-client lifecycle workflows.
- Kept Pocket ID API keys and generated confidential OIDC client secrets outside model-visible tool arguments and responses.
- Added verified group-restriction and delete-confirmation guards for security-relevant OIDC client mutations.
- Published wheel and source artifacts with `SHA256SUMS` and established Pocket ID `v2.7.0` as the tested compatibility baseline.
