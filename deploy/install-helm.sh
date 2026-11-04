#!/usr/bin/env bash
set -euo pipefail

# Pinned, checksum-verified Helm 3 for CI; packages are compatible with Devtron.
helm_version=3.22.1
download_dir=$(mktemp -d)
trap 'rm -rf "$download_dir"' EXIT
archive="helm-v${helm_version}-linux-amd64.tar.gz"
curl --fail --silent --show-error --location \
  "https://get.helm.sh/${archive}" --output "$download_dir/$archive"
curl --fail --silent --show-error --location \
  "https://get.helm.sh/${archive}.sha256sum" --output "$download_dir/checksum"
(cd "$download_dir" && sha256sum --check checksum)
tar -xzf "$download_dir/$archive" -C "$download_dir"
mkdir -p "$HOME/.local/bin"
install -m 0755 "$download_dir/linux-amd64/helm" "$HOME/.local/bin/helm"
