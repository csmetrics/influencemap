#!/bin/bash
# Deploy latest code to the InfluenceMap stack.
#
# What this does:
#   - Fast-forward-only pull (fails loudly on merge conflicts instead of
#     silently making them).
#   - Rebuilds + recreates ONLY webapp and konigsberg. OpenSearch stays
#     up so its indexes and page cache don't get lost.
#   - Preserves persistent volumes: bingraph, OpenSearch data, numba
#     cache, flower cache, kb cache, opensearch cache.
#   - Shows post-deploy status.
#
# Usage:
#   ./update.sh              # standard deploy
#   ./update.sh --no-cache   # rebuild images from scratch (rare — use
#                            #   when a base image or system package
#                            #   changed)
set -euo pipefail

BUILD_ARGS=()
if [[ "${1:-}" == "--no-cache" ]]; then
    BUILD_ARGS+=(--no-cache)
fi

echo "==> git pull (ff-only)"
git pull --ff-only

echo "==> building webapp + konigsberg images"
sudo docker compose build "${BUILD_ARGS[@]}" webapp konigsberg

echo "==> recreating webapp + konigsberg containers"
# --force-recreate ensures the new image is used even if the tag hasn't
# moved. Also picks up any compose.yaml env changes.
sudo docker compose up -d --force-recreate webapp konigsberg

echo "==> status"
sudo docker compose ps

echo
echo "==> konigsberg last 20 lines"
sudo docker compose logs --tail=20 konigsberg

echo
echo "==> webapp last 20 lines"
sudo docker compose logs --tail=20 webapp

echo
echo "Deploy complete. Tail live logs with:"
echo "  sudo docker compose logs -f konigsberg webapp"
