# diddukewin

Fetches Duke basketball scores, publishes the site to S3-compatible storage,
and optionally posts updates to social accounts.

Use `uv sync --frozen` for local dependencies and `uv run --frozen pytest` for tests.
Each successful CircleCI build on `master` publishes a complete release to Docker
Hub: a commit-specific image and an OCI Helm chart containing its exact image
digest. Git tags do not trigger builds. Devtron discovers chart versions for manual
deployment; CircleCI has no tailnet or Kubernetes access.

See [deployment documentation](deploy/README.md) for the Helm chart, Devtron
workflow, configuration, manual Secrets, and recovery procedures.
