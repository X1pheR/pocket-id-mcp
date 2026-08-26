#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UV_IMAGE="${UV_IMAGE:-ghcr.io/astral-sh/uv:0.12.4-python3.12-trixie-slim}"

command -v docker >/dev/null
command -v git >/dev/null

uid="$(id -u)"
gid="$(id -g)"

docker run --rm \
  --user "${uid}:${gid}" \
  -e HOME=/tmp \
  -e UV_CACHE_DIR=/tmp/uv-cache \
  -e UV_PROJECT_ENVIRONMENT=/tmp/pocket-id-venv \
  -e UV_LINK_MODE=copy \
  -v "${ROOT}:/work:ro" \
  -w /work \
  --entrypoint sh \
  "${UV_IMAGE}" \
  -c 'set -eu; uv sync --frozen --extra test; uv run --frozen --extra test pytest -q; uv build --out-dir /tmp/pocket-id-dist'

git -C "${ROOT}" diff --check
