# Kubernetes deployment

`deploy/chart` is the source of the app's Kubernetes resources. The production
Argo CD Application manages exactly:

- `Deployment/diddukewin/diddukewin` (one replica, `Recreate` strategy)
- `ConfigMap/diddukewin/ddw-config`

The manually managed Secrets `ddw-credentials` and `ddw-cloudflare` are referenced
by the chart but are not created, updated, or deleted by Argo CD. They must exist
in the target namespace before the Deployment starts.

## Runtime behaviour

The publisher runs as one long-lived pod (`ddw/app.py`, `serve()`). Every loop
iteration is stateless: the page state lives in R2 (`index.html`, `score.json`)
and each social client checks its latest post before posting. Replacing the pod
at any time, mid-game included, costs only the seconds the new pod takes to start.

| Situation | What the worker does |
| --- | --- |
| Outside the active hours (default 11:00–01:59 New York) with nothing live | Sleeps; no NCAA or R2 calls |
| Inside the active hours, no game or game already final | Checks NCAA every 10 minutes and uploads nothing new |
| Game more than 12 minutes from tip-off | Same 10-minute check |
| 12 minutes before tip-off until 45 minutes after the listed start, or live | Polls every 15 seconds, past the end of the active hours if needed |
| Game just went final | Publishes the result, posts once, returns to the 10-minute check |
| NCAA throttles or any error | Logs, reports to Sentry and retries; never exits. During a game, throttles back off (Retry-After, else 30 s doubling to 5 min) and other errors retry at 15 s; after 5 failures in a row it falls back to the idle schedule above |
| Game still not final `MAX_RUN_HOURS` (default 4) after its listed start | Treated as stale (suspended game, stuck feed): back to the idle schedule |

SIGTERM stops the loop at its next sleep, so pod replacement is immediate.

## Commit releases

Every successful commit build on `master` publishes:

- Image: `docker.io/galonsky/diddukewin:sha-<full-git-sha>-<circleci-build-number>`
- Chart: `oci://registry-1.docker.io/galonsky/diddukewin-chart`, version `0.0.<circleci-build-number>`

The published chart contains the exact chart/configuration from the checkout and
pins the published image by SHA-256 digest. Its `appVersion` and revision annotation
record the full Git SHA. Code-only and chart-only commits follow the same path;
both get a complete release. Rebuilding on every commit is intentional, with no
manual Git tag or chart version bump required. Re-running a CI job gets a new build
number and therefore a new release version.

CircleCI runs tests, type checking, formatting, Helm validation, and package-level
release tests before publishing. Images are pushed first, then charts, so a failed
image build/push cannot advertise a broken release. A failed chart push leaves an
unused image, not a deployable chart. Earlier chart versions remain deployable.
No `latest` image tag is published and the old Git-tag build job is retired.

`package-release.py` stages the chart outside the checkout and leaves tracked
source values unchanged. `publish-release.sh` verifies that its checkout matches
the CI commit, restricts publishing to master branch builds, and uses the existing
`DOCKERHUB_USER` / `DOCKERHUB_PASSWORD` CircleCI variables. Their token needs write
access to both Docker Hub repositories. CI holds no Kubernetes, Argo CD, or Kargo
credentials and has no private network access. Both repositories must be public
for the configured anonymous cluster pulls.

CircleCI retains the chart package, buildx image metadata, and `release.json` as
build artifacts. Use the Git SHA in the chart or release metadata to correlate a
release with its source. Build numbers identify publication runs and may contain
gaps because CircleCI numbers other jobs too.

## Deploy and roll back

Kargo and Argo CD resources for this deployment are recorded in [`kargo/`](kargo/)
and [`argocd/application.yaml`](argocd/application.yaml).
The Kargo Warehouse watches `master` and Docker Hub for matching commit-SHA image
tags. It creates Freight automatically; promotion to the `test` Stage is manual.
That Stage currently deploys to the production namespace `diddukewin`; there is
no separate test namespace.

Promoting Freight updates the `diddukewin-kargo` Argo CD Application to that Git
commit and image digest. Argo CD auto-syncs it into the production namespace
`diddukewin`. Kargo then waits for the Application's operation to finish and for
it to report both Healthy and Synced before the Promotion succeeds. To roll back,
manually promote an earlier Freight.

Argo CD automated pruning is disabled. If a chart change removes a Kubernetes
resource, the Application will need an Argo sync with prune before Kargo's
healthy-and-synced wait can complete. Review deletions carefully before pruning.

## Set up on a cluster

Install Argo CD and Kargo first; this repo contains the Diddukewin resources, not
the controllers or their cluster-specific authentication settings. The GitHub repo
and Docker Hub image are public, so no repository credentials are required. Create
`diddukewin` and its manually
managed Secrets before syncing the Application. `ddw-credentials` is required;
`ddw-cloudflare` is optional. Use the placeholders in `secrets.example.yaml` as a
key reference only; never apply that file or commit real values.

The Application manifest starts from a known healthy, immutable commit and image
digest. It is intentionally not pointed at `master`: with auto-sync enabled, that
would deploy commits before a manual Kargo promotion. Once Kargo is configured,
promotions move the Application to the selected commit and digest. Apply this
manifest once to bootstrap the Application; reapplying it later resets the
revision and digest to the bootstrap release.

Apply the Application and Kargo resources in this order:

```sh
kubectl create namespace diddukewin --dry-run=client -o yaml | kubectl apply -f -
# Create this local env file with the required credentials; never commit it.
kubectl -n diddukewin create secret generic ddw-credentials \
  --from-env-file=/secure/path/ddw-credentials.env
# Optional; create only if Cloudflare cache purging is configured.
kubectl -n diddukewin create secret generic ddw-cloudflare \
  --from-env-file=/secure/path/ddw-cloudflare.env
kubectl apply -f deploy/argocd/application.yaml
kubectl apply -f deploy/kargo/project.yaml
kubectl wait --for=condition=Ready project.kargo.akuity.io/diddukewin-kargo --timeout=2m
kubectl apply -f deploy/kargo/project-config.yaml
kubectl apply -f deploy/kargo/warehouse.yaml
kubectl apply -f deploy/kargo/stage.yaml
```

Wait for the Argo Application to become Healthy before promoting Freight. The
Application manifest includes the required authorization annotation
`kargo.akuity.io/authorized-stage: diddukewin-kargo:test`. These manifests contain
no credentials; they reference the public Git and Docker Hub repositories.

## Configuration and dependencies

Edit `deploy/chart/values.yaml` for ordinary configuration and defaults. Current settings:

| Setting | Purpose |
| --- | --- |
| `image.repository`, `image.tag`, `image.digest` | CI embeds the published image digest; the tag is retained for traceability and local recovery |
| `deployment.*` | Deployment name and 30-second termination grace period |
| `config.BUCKET_NAME`, `config.S3_ENDPOINT_URL` | Cloudflare R2 storage target using the S3 API |
| `config.BLUESKY_USERNAME`, `config.SKEETING_ENABLED` | Bluesky account and posting enablement |
| `config.USE_NCAA` | Legacy setting retained from the running configuration |

A change to `config` changes the pod's `checksum/config` annotation, so it also
replaces the pod.

The app obtains NCAA scores over HTTPS, publishes `index.html` and `score.json`
to R2, optionally purges Cloudflare caches, and optionally posts to Bluesky,
Mastodon, and Twitter. Sentry is optional. There are no app-specific Kubernetes
Services, volumes, or ingress resources.

Other supported non-sensitive environment settings include `SITE_URL`,
`LIVE_POLL_SECONDS` (default 15), `IDLE_POLL_SECONDS` (default 600),
`ACTIVE_START_HOUR` (default 11) and `ACTIVE_END_HOUR` (default 2, exclusive,
wrapping past midnight; equal values mean always active), `PREGAME_WINDOW_MINUTES`,
`PREGAME_GRACE_MINUTES`, `MAX_RUN_HOURS` (default 4; caps live polling per game),
`MIN_HOURS_BETWEEN_SKEETS`, `MIN_HOURS_BETWEEN_TOOTS`, and
`MIN_HOURS_BETWEEN_TWEETS`. Omitted settings retain the defaults in the app code.
Posting flags (`SKEETING_ENABLED`, `TOOTING_ENABLED`, `TWEETING_ENABLED`) and
`FORCE_UPLOAD` treat **any non-empty string as enabled**, including `"false"`;
omit a flag or use an empty value to disable it.

## Manually managed Secrets

`secrets.example.yaml` documents key names using placeholders. Do not apply it
directly or commit a filled copy. For a new cluster, prepare a local file outside
the checkout with mode 0600 and use `kubectl create secret generic ... --from-env-file`.
For this existing cluster, update individual values locally with:

```sh
kubectl -n diddukewin edit secret ddw-credentials
kubectl -n diddukewin edit secret ddw-cloudflare
```

The `data` values shown by `kubectl edit secret` are base64-encoded. Base64 is not
encryption; keep these values out of Git and command output shared with others.
The pod reads Secrets only at start, so replace it after a credential change
(see "Check now" below); no chart release is needed.

| Secret | Keys and use |
| --- | --- |
| `ddw-credentials` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: required for the configured R2 bucket |
| `ddw-credentials` | `BLUESKY_PASSWORD`: needed with `BLUESKY_USERNAME` when Bluesky posting is enabled |
| `ddw-credentials` | `MASTODON_ACCESS_TOKEN`: needed when Mastodon posting is enabled |
| `ddw-credentials` | `SENTRY_DSN`: optional error reporting |
| `ddw-credentials` | `API_BASKETBALL_KEY`: legacy credential preserved during migration |
| `ddw-credentials` | Optional Twitter credentials: `TWITTER_CONSUMER_KEY`, `TWITTER_CONSUMER_SECRET`, `TWITTER_ACCESS_TOKEN_KEY`, `TWITTER_ACCESS_TOKEN_SECRET` |
| `ddw-cloudflare` | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`: optional cache purging, requiring both values |

`ddw-credentials` itself must exist. Missing optional integration keys are allowed.
The entire `ddw-cloudflare` Secret is optional. `envFrom` precedence is ConfigMap,
credentials Secret, then Cloudflare Secret. Keep keys in their documented resource
to avoid accidental overrides.

## Chart changes and local validation

Edit `deploy/chart/templates` and `deploy/chart/values.yaml`, then commit to master through the
normal review workflow. CI packages the changed chart automatically.

```sh
helm lint deploy/chart
helm template diddukewin-kargo deploy/chart --namespace diddukewin > /tmp/diddukewin.yaml
kubectl apply --dry-run=server -f /tmp/diddukewin.yaml -o name
uv run --frozen pytest tests deploy/tests
```

`install-helm.sh` installs checksum-verified Helm 3.22.1 for CI. The package tests
run the actual Helm CLI. `deploy/dist/` is ignored by Git. The unmodified source
chart retains a tagged fallback image for local inspection; production release
packages always embed a digest.

Use Kargo and Argo CD for deployment and rollback. Avoid installing a separate
local Helm release against the production namespace, as that would create another
owner for the same resources.

## Verification and operations

```sh
kubectl -n diddukewin get deploy diddukewin
kubectl -n diddukewin logs deploy/diddukewin -f
```

**Check now.** To make the worker look for a game immediately (or pick up changed
Secrets), delete its pod; the Deployment starts a fresh one:

```sh
kubectl -n diddukewin delete pod -l app.kubernetes.io/name=diddukewin
```

Avoid `kubectl rollout restart`: it edits the pod template, which Argo CD reports
as drift.

**Forced upload.** To re-render and upload the last known result once, run a one-off
inside the pod. This publishes real content; posting is skipped for a last known game.

```sh
kubectl -n diddukewin exec deploy/diddukewin -- \
  env FORCE_UPLOAD=1 uv run --no-sync python ddw/app.py once
```

`migrate-config.py` is the one-time legacy ConfigMap-to-Secret migration, written
against the old CronJob and kept for reference; it doesn't apply to the Deployment.
It previews
by default; `--apply` first creates a private backup outside the repo under
`~/.local/state/diddukewin-deploy/backups/`, then writes the Secret, updates future
jobs to reference it, and removes credential keys from the ConfigMap. The migration
has already been applied on elitedesk. Backups contain credentials; protect them and
include the manual Secrets in off-machine backups. Recover missing values into
Secrets, rather than restoring the old credential-bearing ConfigMap.

Deleting the Argo CD Application does not delete resources while automated pruning
is disabled. Review and remove the Deployment and ConfigMap separately if retiring
the application. Manually managed Secrets must also be handled separately.
