# diddukewin

Fetches Duke basketball scores, publishes the site to S3-compatible storage,
and optionally posts updates to social accounts. It runs as one long-lived
worker that checks for a game every ten minutes and polls every 15 seconds while
one is live.

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
