"""Package this checkout as an immutable Helm release; does not publish anything."""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import yaml


def package_release(
    commit: str, build_number: str, image_digest: str, output: Path
) -> Path:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("commit must be a full lowercase Git SHA")
    if not re.fullmatch(r"[1-9][0-9]*", build_number):
        raise ValueError("build number must be a positive integer")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_digest):
        raise ValueError("image digest must be a sha256 digest")
    root = Path(__file__).resolve().parents[1]
    version = f"0.0.{build_number}"
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"diddukewin-chart-{version}.tgz"
    if archive.exists():
        raise ValueError("release package already exists; use a fresh output directory")
    image_tag = f"sha-{commit}-{build_number}"
    with tempfile.TemporaryDirectory(prefix="diddukewin-release-") as temp:
        chart = Path(temp) / "diddukewin-chart"
        shutil.copytree(
            root / "deploy/chart",
            chart,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.tgz"),
        )
        metadata_path = chart / "Chart.yaml"
        metadata = yaml.safe_load(metadata_path.read_text())
        metadata.update({"version": version, "appVersion": commit})
        metadata.setdefault("annotations", {}).update(
            {
                "org.opencontainers.image.revision": commit,
                "org.opencontainers.image.source": "https://github.com/galonsky/diddukewin_v3",
            }
        )
        metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False))
        values_path = chart / "values.yaml"
        values = yaml.safe_load(values_path.read_text())
        values["image"].update(
            {
                "repository": "galonsky/diddukewin",
                "tag": image_tag,
                "digest": image_digest,
            }
        )
        values_path.write_text(yaml.safe_dump(values, sort_keys=False))
        # Published charts deploy their embedded digest. The old external-image
        # descriptor belongs only to the legacy Devtron app workflow.
        (chart / ".image_descriptor_template.json").unlink(missing_ok=True)
        subprocess.run(["helm", "lint", str(chart)], check=True)
        subprocess.run(
            ["helm", "package", str(chart), "--destination", str(output)], check=True
        )
    (output / "release.json").write_text(
        json.dumps(
            {
                "version": version,
                "commit": commit,
                "image": f"galonsky/diddukewin@{image_digest}",
                "imageTag": image_tag,
                "chart": "oci://registry-1.docker.io/galonsky/diddukewin-chart",
                "buildNumber": build_number,
            },
            indent=2,
        )
        + "\n"
    )
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--build-number", required=True)
    parser.add_argument("--image-metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("deploy/dist"))
    args = parser.parse_args()
    metadata = json.loads(args.image_metadata.read_text())
    digest = metadata.get("containerimage.digest")
    if not isinstance(digest, str):
        parser.error("buildx metadata is missing containerimage.digest")
    try:
        archive = package_release(args.commit, args.build_number, digest, args.output)
    except ValueError as error:
        parser.error(str(error))
    print(archive)


if __name__ == "__main__":
    main()
