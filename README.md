# diddukewin

Fetches Duke basketball scores, publishes the site to S3-compatible storage,
and optionally posts updates to social accounts. It runs as one long-lived
worker that checks for a game every ten minutes and polls every 15 seconds while
one is live.

Use `uv sync --frozen` for local dependencies and `uv run --frozen pytest` for tests.
Each successful CircleCI build on `master` publishes a complete release to Docker
Hub: a commit-specific image and an OCI Helm chart containing its exact image
digest. Git tags do not trigger builds. A Kargo Warehouse picks up each chart
version, and promoting it in Kargo has Argo CD sync it to the cluster; CircleCI
has no tailnet or Kubernetes access.

See [deployment documentation](deploy/README.md) for the Helm chart, Kargo and
Argo CD workflow, runtime behaviour, configuration, manual Secrets, and recovery procedures.
