# Kubernetes deployment

`deploy/chart` is the source of the app's Kubernetes resources. It replaces the
old standalone `k8s/cron.yaml`. The chart manages exactly:

- `CronJob/default/diddukewin`
- `ConfigMap/default/ddw-config`

The manually managed Secrets `ddw-credentials` and `ddw-cloudflare` are referenced
by the chart but are not created, updated, or deleted by Helm.

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
access to both Docker Hub repositories. No Devtron credentials, kubeconfig,
Tailscale keys, or private network access are used by CI. Both repositories must
be public for the configured anonymous cluster pulls.

CircleCI retains the chart package, buildx image metadata, and `release.json` as
build artifacts. Use the Git SHA in the chart or release metadata to correlate a
release with its source. Build numbers identify publication runs and may contain
gaps because CircleCI numbers other jobs too.

## Deploy and roll back

Open http://devtron.tail9932cd.ts.net/dashboard/ and use the Helm application
**diddukewin-default**, in namespace `default`. Its chart source is
**galonsky-charts** and its chart is **diddukewin-chart**. Select a chart version
and deploy it; selecting an earlier version restores its chart and image together.
Use the selected chart's default values so an old image or setting is not pinned
by an override. Keep ordinary configuration in this repo and publish a new release
for configuration changes rather than maintaining UI-only overrides.

Devtron's built-in chart sync refreshes the configured OCI source every five
minutes. It does not automatically deploy new releases. For immediate discovery,
use the chart source's Resync button. No app-specific polling job is installed.
Installation-specific identifiers and source details are recorded in `devtron.json`.

A fresh CI commit release becomes available after this configuration is merged to
`master`, its pipeline succeeds, and catalog synchronization completes. The
`0.0.0-validation.*` versions are integration probes using the existing v6.0.0
image, not CI builds of new app code. They sort below commit releases.

Deploying changes the existing CronJob template for future jobs; it does not run
the publisher immediately or change a job that is already running. The release
name remains `diddukewin-default`; the CronJob name remains `diddukewin`.
The local checkout is not required to deploy published releases.

The older `diddukewin` Devtron app record and image-event pipeline remain in Manual
mode pending approval for control-plane cleanup. Use the **diddukewin-default Helm
App** for this workflow. Removing the old records is separate from deleting any
Kubernetes workloads.

## Configuration and dependencies

Edit `chart/values.yaml` for ordinary configuration and defaults. Current settings:

| Setting | Purpose |
| --- | --- |
| `image.repository`, `image.tag`, `image.digest` | CI embeds the published image digest; the tag is retained for traceability and local recovery |
| `cronjob.*` | New York timezone, every ten minutes during the configured hours, no overlapping scheduled jobs |
| `job.*` | Five-hour job deadline, one retry, 30-second termination grace period |
| `config.BUCKET_NAME`, `config.S3_ENDPOINT_URL` | Cloudflare R2 storage target using the S3 API |
| `config.BLUESKY_USERNAME`, `config.SKEETING_ENABLED` | Bluesky account and posting enablement |
| `config.USE_NCAA` | Legacy setting retained from the running configuration |

The app obtains NCAA scores over HTTPS, publishes `index.html` and `score.json`
to R2, optionally purges Cloudflare caches, and optionally posts to Bluesky,
Mastodon, and Twitter. Sentry is optional. There are no app-specific Kubernetes
Services, volumes, or ingress resources.

Other supported non-sensitive environment settings include `SITE_URL`,
`LIVE_POLL_SECONDS`, `PREGAME_WINDOW_MINUTES`, `PREGAME_GRACE_MINUTES`,
`MAX_RUN_HOURS`, `MIN_HOURS_BETWEEN_SKEETS`, `MIN_HOURS_BETWEEN_TOOTS`, and
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
kubectl -n default edit secret ddw-credentials
kubectl -n default edit secret ddw-cloudflare
```

The `data` values shown by `kubectl edit secret` are base64-encoded. Base64 is not
encryption; keep these values out of Git and command output shared with others.
Credential changes affect subsequently started jobs; no chart upload is needed.

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

Edit `chart/templates` and `chart/values.yaml`, then commit to master through the
normal review workflow. CI packages the changed chart automatically. Do not upload
custom chart snapshots to Devtron or announce individual image events.

```sh
helm lint deploy/chart
helm template diddukewin-default deploy/chart --namespace default > /tmp/diddukewin.yaml
kubectl apply --dry-run=server -f /tmp/diddukewin.yaml -o name
uv run --frozen pytest tests deploy/tests
```

`install-helm.sh` installs checksum-verified Helm 3.22.1 for CI. The package tests
run the actual Helm CLI. `deploy/dist/` is ignored by Git. The unmodified source
chart retains a tagged fallback image for local inspection; production release
packages always embed a digest.

For recovery without Devtron, fetch a published release directly:

```sh
helm upgrade --install diddukewin-default \
  oci://registry-1.docker.io/galonsky/diddukewin-chart \
  --version 0.0.BUILD_NUMBER --namespace default --reset-values
```

Replace the example version with an actual published release. Resetting values
uses that release's embedded configuration and image digest. Manually managed
Secrets remain independent.

## Verification and operations

```sh
kubectl -n default get cronjob diddukewin
kubectl -n default get jobs --sort-by=.metadata.creationTimestamp
helm status diddukewin-default -n default
kubectl -n default create job --from=cronjob/diddukewin ddw-validation --dry-run=server -o name
```

The last command validates job creation without running the publisher. To run it
immediately when intended, omit the dry-run and use a unique name. That publishes
real content and may post to social accounts. Scheduled job execution can be
inspected through Devtron's Kubernetes resource browser and pod logs.

On 2026-11-04, migration verified the original resource UIDs, image, schedule,
timezone, concurrency policy, history limits, job limits, and effective environment
values against a protected backup. No immediate publisher job was executed.

`migrate-config.py` is the one-time legacy ConfigMap-to-Secret migration. It previews
by default; `--apply` first creates a private backup outside the repo under
`~/.local/state/diddukewin-deploy/backups/`, then writes the Secret, updates future
jobs to reference it, and removes credential keys from the ConfigMap. The migration
has already been applied on elitedesk. Backups contain credentials; protect them and
include the manual Secrets in off-machine backups. Recover missing values into
Secrets, rather than restoring the old credential-bearing ConfigMap.

Deleting the app/release with workload deletion enabled removes its CronJob and
ConfigMap. Manually managed Secrets remain and must be handled separately.
