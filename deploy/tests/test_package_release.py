"""Check the actual packaged release, including chart-only changes and rollback data."""

import importlib.util
from pathlib import Path
import subprocess
import tarfile

import pytest
import yaml

MODULE_PATH = Path(__file__).resolve().parents[1] / "package-release.py"
spec = importlib.util.spec_from_file_location("package_release", MODULE_PATH)
assert spec and spec.loader
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

COMMIT = "a" * 40
DIGEST = "sha256:" + "b" * 64


def test_package_contains_matching_code_and_chart_release(tmp_path):
    archive = release.package_release(COMMIT, "123", DIGEST, tmp_path)
    with tarfile.open(archive) as package:
        metadata_file = package.extractfile("diddukewin-chart/Chart.yaml")
        values_file = package.extractfile("diddukewin-chart/values.yaml")
        assert metadata_file and values_file
        metadata = yaml.safe_load(metadata_file.read())
        values = yaml.safe_load(values_file.read())
        assert metadata["version"] == "0.0.123"
        assert metadata["appVersion"] == COMMIT
        assert metadata["annotations"]["org.opencontainers.image.revision"] == COMMIT
        assert values["image"]["digest"] == DIGEST
        assert values["image"]["tag"] == f"sha-{COMMIT}-123"
        assert not any(".image_descriptor" in name for name in package.getnames())
        assert not any("__pycache__" in name for name in package.getnames())
    rendered = subprocess.check_output(
        [
            "helm",
            "template",
            "diddukewin-default",
            str(archive),
            "--namespace",
            "default",
        ],
        text=True,
    )
    resources = list(yaml.safe_load_all(rendered))
    assert {row["kind"] for row in resources} == {"ConfigMap", "Deployment"}
    deployment = next(row for row in resources if row["kind"] == "Deployment")
    assert deployment["metadata"]["name"] == "diddukewin"
    assert deployment["spec"]["replicas"] == 1
    assert deployment["spec"]["strategy"] == {"type": "Recreate"}
    pod = deployment["spec"]["template"]
    assert pod["metadata"]["annotations"]["checksum/config"]
    container = pod["spec"]["containers"][0]
    assert container["image"] == f"galonsky/diddukewin@{DIGEST}"
    assert container["envFrom"][1] == {"secretRef": {"name": "ddw-credentials"}}


def test_distinct_builds_preserve_earlier_release(tmp_path):
    first = release.package_release(COMMIT, "123", DIGEST, tmp_path)
    original = first.read_bytes()
    second = release.package_release("c" * 40, "124", DIGEST, tmp_path)
    assert second != first
    assert first.read_bytes() == original
    with pytest.raises(ValueError, match="already exists"):
        release.package_release(COMMIT, "123", DIGEST, tmp_path)


@pytest.mark.parametrize(
    "commit,build,digest",
    [("main", "123", DIGEST), (COMMIT, "0", DIGEST), (COMMIT, "123", "latest")],
)
def test_invalid_release_identity_cannot_produce_package(
    tmp_path, commit, build, digest
):
    with pytest.raises(ValueError):
        release.package_release(commit, build, digest, tmp_path)
    assert not list(tmp_path.glob("*.tgz"))
