#!/usr/bin/env bash
set -euo pipefail

: "${CIRCLE_SHA1:?CircleCI commit SHA is required}"
: "${CIRCLE_BUILD_NUM:?CircleCI build number is required}"
: "${DOCKERHUB_USER:?Docker Hub username is required}"
: "${DOCKERHUB_PASSWORD:?Docker Hub publishing token is required}"
[[ "${CIRCLE_BRANCH:-}" == master && -z "${CIRCLE_TAG:-}" ]] || {
  echo 'Publishing is restricted to branch builds on master.' >&2
  exit 1
}
[[ "$(git rev-parse HEAD)" == "$CIRCLE_SHA1" ]] || {
  echo 'Checkout does not match the requested release commit.' >&2
  exit 1
}
[[ "$CIRCLE_BUILD_NUM" =~ ^[1-9][0-9]*$ && "$CIRCLE_SHA1" =~ ^[0-9a-f]{40}$ ]] || {
  echo 'Invalid commit SHA or build number.' >&2
  exit 1
}
release_version="0.0.${CIRCLE_BUILD_NUM}"
image="galonsky/diddukewin:sha-${CIRCLE_SHA1}-${CIRCLE_BUILD_NUM}"
export PATH="$HOME/.local/bin:$PATH"
mkdir -p deploy/dist

printf '%s' "$DOCKERHUB_PASSWORD" | docker login \
  --username "$DOCKERHUB_USER" --password-stdin
printf '%s' "$DOCKERHUB_PASSWORD" | helm registry login registry-1.docker.io \
  --username "$DOCKERHUB_USER" --password-stdin

# Publish the chart last: a discoverable release must always reference an image
# that was pushed successfully. No mutable latest tag or source Git tag is used.
docker buildx build --platform linux/amd64 --push \
  --tag "$image" \
  --label "org.opencontainers.image.revision=$CIRCLE_SHA1" \
  --label org.opencontainers.image.source=https://github.com/galonsky/diddukewin_v3 \
  --metadata-file deploy/dist/image-metadata.json .
uv run --frozen python deploy/package-release.py \
  --commit "$CIRCLE_SHA1" --build-number "$CIRCLE_BUILD_NUM" \
  --image-metadata deploy/dist/image-metadata.json
helm push "deploy/dist/diddukewin-chart-${release_version}.tgz" \
  oci://registry-1.docker.io/galonsky
