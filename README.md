# diddukewin

Fetches Duke basketball scores, publishes the site to S3-compatible storage,
and optionally posts updates to social accounts. It runs as one long-lived
worker that checks for a game every ten minutes and polls every 15 seconds while
one is live.

When a game ends, the worker draws a 1200x630 social card (`ddw/card.py`) and
uploads it with a frozen page at `g/<date>-<hash>/` (`ddw/social.py`), so every
finished game has its own link-preview URL. The Bluesky post links to that page
and carries the card as its embed; the homepage `og:image` follows the latest
final result and falls back to `cards/default.png` while a game is live.

Use `uv sync --frozen` for local dependencies and `uv run --frozen pytest` for tests.
Each successful CircleCI build on `master` publishes a complete release to Docker
Hub: a commit-specific image and an OCI Helm chart containing its exact image
digest. Git tags do not trigger builds. A Kargo Warehouse correlates `master`
commits with matching Docker Hub image tags and creates Freight. A manual
promotion updates the production Argo CD Application; Kargo waits for Argo to
report the app healthy and synced. CircleCI has no tailnet or Kubernetes access.

See [deployment documentation](deploy/README.md) for the Helm chart, Kargo and
Argo CD workflow, runtime behaviour, configuration, manually managed Secrets, and
recovery procedures. The Argo CD Application and public Kargo resources are in
[`deploy/argocd`](deploy/argocd/) and [`deploy/kargo`](deploy/kargo/).
