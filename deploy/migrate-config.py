"""Move legacy ConfigMap credentials into a manual Secret without changing values.

Preview by default; --apply writes protected backups outside the repository first.
This is a one-time migration, not the normal credential update mechanism.
"""

import argparse
import base64
import copy
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

CREDENTIAL_KEYS = {
    "API_BASKETBALL_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "BLUESKY_PASSWORD",
    "MASTODON_ACCESS_TOKEN",
    "SENTRY_DSN",
    "TWITTER_CONSUMER_KEY",
    "TWITTER_CONSUMER_SECRET",
    "TWITTER_ACCESS_TOKEN_KEY",
    "TWITTER_ACCESS_TOKEN_SECRET",
}


def kubectl(*args: str, body: dict | list | None = None) -> dict:
    result = subprocess.run(
        ["kubectl", "-n", "default", *args],
        input=json.dumps(body) if body is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        sys.exit(
            "kubectl operation failed; inspect cluster access/resource state locally."
        )
    return json.loads(result.stdout) if result.stdout.strip() else {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    cm = kubectl("get", "configmap", "ddw-config", "-o", "json")
    cron = kubectl("get", "cronjob", "diddukewin", "-o", "json")
    existing = kubectl(
        "get", "secret", "ddw-credentials", "--ignore-not-found", "-o", "json"
    )
    source = cm.get("data", {})
    credentials = {
        key: base64.b64decode(value).decode()
        for key, value in existing.get("data", {}).items()
    }
    if set(credentials) - CREDENTIAL_KEYS:
        sys.exit("ddw-credentials has unexpected keys; review before migrating.")
    for key in CREDENTIAL_KEYS & source.keys():
        if key in credentials and credentials[key] != source[key]:
            sys.exit(f"Conflicting value for {key}; resolve locally before migrating.")
        credentials[key] = source[key]
    if not {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"} <= credentials.keys():
        sys.exit("Expected storage credentials are missing; nothing changed.")
    public = {key: value for key, value in source.items() if key not in CREDENTIAL_KEYS}
    container_path = "/spec/jobTemplate/spec/template/spec/containers/0/envFrom"
    env_from = cron["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0][
        "envFrom"
    ]
    expected = [
        {"configMapRef": {"name": "ddw-config"}},
        {"secretRef": {"name": "ddw-cloudflare", "optional": True}},
    ]
    migrated = [
        expected[0],
        {"secretRef": {"name": "ddw-credentials"}},
        expected[1],
    ]
    if env_from not in (expected, migrated):
        sys.exit("Unexpected CronJob environment references; review before migrating.")
    # Cloudflare remains the final envFrom source, unchanged by this migration.
    before = {**source, **credentials} if env_from == migrated else source
    if before != {**public, **credentials}:
        sys.exit("Effective environment would change; nothing changed.")
    print("Public configuration keys:", ", ".join(sorted(public)))
    print("Credential keys:", ", ".join(sorted(credentials)))
    if not args.apply:
        print("Preview only. Rerun with --apply to back up and migrate.")
        return

    os.umask(0o077)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = Path.home() / ".local/state/diddukewin-deploy/backups" / stamp
    backup.mkdir(parents=True, mode=0o700)
    (backup / "resources.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "kind": "List",
                "items": [cm, cron, *([existing] if existing else [])],
            },
            indent=2,
        )
        + "\n"
    )
    secret = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": copy.deepcopy(
            existing.get("metadata", {"name": "ddw-credentials"})
        ),
        "type": "Opaque",
        "data": {
            key: base64.b64encode(value.encode()).decode()
            for key, value in credentials.items()
        },
    }
    kubectl("replace" if existing else "create", "-f", "-", "-o", "json", body=secret)
    if env_from != migrated:
        kubectl(
            "patch",
            "cronjob",
            "diddukewin",
            "--type=json",
            "--patch-file=/dev/stdin",
            "-o",
            "json",
            body=[
                {
                    "op": "test",
                    "path": "/metadata/resourceVersion",
                    "value": cron["metadata"]["resourceVersion"],
                },
                {"op": "replace", "path": container_path, "value": migrated},
            ],
        )
    # Remove credentials only after future jobs reference the successfully written
    # Secret. Optimistic concurrency prevents overwriting simultaneous config edits.
    updated_cm = copy.deepcopy(cm)
    updated_cm["data"] = public
    updated_cm["metadata"].get("annotations", {}).pop(
        "kubectl.kubernetes.io/last-applied-configuration", None
    )
    kubectl("replace", "-f", "-", "-o", "json", body=updated_cm)
    actual_cm = kubectl("get", "configmap", "ddw-config", "-o", "json")
    actual_secret = kubectl("get", "secret", "ddw-credentials", "-o", "json")
    assert actual_cm["data"] == public
    assert actual_secret["data"] == secret["data"]
    print("Migrated without changing values. Protected backup:", backup)


if __name__ == "__main__":
    main()
