#!/usr/bin/env python3
"""Build and verify Atlaso's temporary multi-platform CPython 3.14 wheels."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import os
import platform
import shutil
import struct
import subprocess
import sys
import sysconfig
import tarfile
import tempfile
import urllib.request
import zipfile
from datetime import UTC, datetime
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

PACKAGE_VERSION = "0.4.1"
SOURCE_DATE_EPOCH = "1785419723"
RELEASE_TAG = "atlaso-wheel-v0.4.1-cp314.2"
PURELIB_PREFIX = "onepassword_sdk-0.4.1.data/purelib/"
MAX_DOWNLOAD_BYTES = 40 * 1024 * 1024
SDIST = {
    "filename": "onepassword_sdk-0.4.1.tar.gz",
    "url": "https://files.pythonhosted.org/packages/df/06/989f5b40e802e11e37c44bc72faabcdd362dcba3392fbfc48be6da49e147/onepassword_sdk-0.4.1.tar.gz",
    "sha256": "4b9224208aa6e35e13bad8534e6521d3abf5ba166ea4efd370fcdc918c4a4d26",
    "size": 34561961,
}
TARGETS = {
    "windows-x86_64": {
        "sys_platform": "win32",
        "machines": ("amd64", "x86_64"),
        "os_platform": "Windows",
        "machine_platform": "amd64",
        "host_platform": "win-amd64",
        "wheel_tag": "cp314-cp314-win_amd64",
        "library": "onepassword/lib/x86_64/op_uniffi_core.dll",
        "binding": "onepassword/lib/x86_64/op_uniffi_core.py",
        "official": {
            "filename": "onepassword_sdk-0.4.1-cp313-cp313-win_amd64.whl",
            "url": "https://files.pythonhosted.org/packages/00/e6/c795eebd51be8cf70f61577d44eccb345df012d1bd036e7545dace0f944d/onepassword_sdk-0.4.1-cp313-cp313-win_amd64.whl",
            "sha256": "45c2a2751017bd43697f949aea74efcd3058b2395dfa5d94c33adfb7ef96a60a",
            "size": 6140433,
        },
    },
    "macos-x86_64": {
        "sys_platform": "darwin",
        "machines": ("x86_64", "amd64"),
        "os_platform": "Darwin",
        "machine_platform": "x86_64",
        "host_platform": "macosx-10.13-x86_64",
        "wheel_tag": "cp314-cp314-macosx_10_13_x86_64",
        "library": "onepassword/lib/x86_64/libop_uniffi_core.dylib",
        "binding": "onepassword/lib/x86_64/op_uniffi_core.py",
        "official": {
            "filename": "onepassword_sdk-0.4.1-cp313-cp313-macosx_10_13_x86_64.whl",
            "url": "https://files.pythonhosted.org/packages/c3/1d/fec27ec00105ada1baa0ed529925e213c87261da9e4bda8997ecb80f4361/onepassword_sdk-0.4.1-cp313-cp313-macosx_10_13_x86_64.whl",
            "sha256": "3ab99159b0680781c29103e8a481487a7cbe307d80ca82d1ebe1696482717dbf",
            "size": 7310375,
        },
    },
    "macos-arm64": {
        "sys_platform": "darwin",
        "machines": ("arm64", "aarch64"),
        "os_platform": "Darwin",
        "machine_platform": "arm64",
        "host_platform": "macosx-11.0-arm64",
        "wheel_tag": "cp314-cp314-macosx_11_0_arm64",
        "library": "onepassword/lib/aarch64/libop_uniffi_core.dylib",
        "binding": "onepassword/lib/aarch64/op_uniffi_core.py",
        "official": {
            "filename": "onepassword_sdk-0.4.1-cp313-cp313-macosx_11_0_arm64.whl",
            "url": "https://files.pythonhosted.org/packages/bc/22/aa06e570c0477a5ab05635f3f216158012bcb6a2a77a85da97d6e598fc0f/onepassword_sdk-0.4.1-cp313-cp313-macosx_11_0_arm64.whl",
            "sha256": "e08741964f94b257ac843b01fbb260fa1ecea1da33e33132c27c33a001d1f750",
            "size": 7030317,
        },
    },
    "manylinux-x86_64": {
        "sys_platform": "linux",
        "machines": ("x86_64", "amd64"),
        "os_platform": "Linux",
        "machine_platform": "x86_64",
        "host_platform": "manylinux-2-32-x86_64",
        "wheel_tag": "cp314-cp314-manylinux_2_32_x86_64",
        "library": "onepassword/lib/x86_64/libop_uniffi_core.so",
        "binding": "onepassword/lib/x86_64/op_uniffi_core.py",
        "official": {
            "filename": "onepassword_sdk-0.4.1-cp313-cp313-manylinux_2_32_x86_64.whl",
            "url": "https://files.pythonhosted.org/packages/71/be/2b669a038881f98512587c512821a50d78b4eae8aa380253d35808643852/onepassword_sdk-0.4.1-cp313-cp313-manylinux_2_32_x86_64.whl",
            "sha256": "438f3d11cc8ce74fb8fa06d6fe8ecb9c8f72ee1490a0ebd2e3f6029d61c3157c",
            "size": 7298314,
        },
    },
    "manylinux-aarch64": {
        "sys_platform": "linux",
        "machines": ("aarch64", "arm64"),
        "os_platform": "Linux",
        "machine_platform": "aarch64",
        "host_platform": "manylinux-2-32-aarch64",
        "wheel_tag": "cp314-cp314-manylinux_2_32_aarch64",
        "library": "onepassword/lib/aarch64/libop_uniffi_core.so",
        "binding": "onepassword/lib/aarch64/op_uniffi_core.py",
        "official": {
            "filename": "onepassword_sdk-0.4.1-cp313-cp313-manylinux_2_32_aarch64.whl",
            "url": "https://files.pythonhosted.org/packages/34/23/d7e0adf4e619904e3be43084ba6bd607ce33dc46798f7c2a52c8d99af3a1/onepassword_sdk-0.4.1-cp313-cp313-manylinux_2_32_aarch64.whl",
            "sha256": "55426aa708316698739babd87693d99312eeb3fbf45a429f467014b4c171d578",
            "size": 7098627,
        },
    },
}


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _target(name: str) -> dict[str, object]:
    try:
        return TARGETS[name]
    except KeyError:
        raise SystemExit(f"unsupported target: {name}") from None


def _expected_wheel(specification: dict[str, object]) -> str:
    return f"onepassword_sdk-{PACKAGE_VERSION}-{specification['wheel_tag']}.whl"


def _assert_runtime(specification: dict[str, object]) -> None:
    if sys.platform != specification["sys_platform"]:
        raise SystemExit(f"target requires {specification['sys_platform']}, found {sys.platform}")
    machine = platform.machine().lower()
    if machine not in specification["machines"]:
        raise SystemExit(f"target requires {specification['machines']}, found {machine}")
    if sys.version_info[:2] != (3, 14) or struct.calcsize("P") != 8:
        raise SystemExit("compatibility wheels require 64-bit CPython 3.14")
    if sysconfig.get_config_var("Py_GIL_DISABLED") not in (None, 0, "0", ""):
        raise SystemExit("free-threaded CPython is not supported")
    if "free-thread" in sys.version.lower():
        raise SystemExit("free-threaded CPython is not supported")


def _download(specification: dict[str, object], destination: Path) -> None:
    request = urllib.request.Request(
        str(specification["url"]), headers={"User-Agent": "Atlaso-cp314-wheel-builder/2"}
    )
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        final_url = response.geturl()
        if not final_url.startswith("https://files.pythonhosted.org/"):
            raise RuntimeError(f"unexpected download origin: {final_url}")
        total = 0
        while block := response.read(1024 * 1024):
            total += len(block)
            if total > MAX_DOWNLOAD_BYTES:
                raise RuntimeError("download exceeded the maximum admitted size")
            output.write(block)
    if total != specification["size"] or _sha256(destination) != specification["sha256"]:
        raise RuntimeError(f"download identity mismatch for {destination.name}")


def _safe_extract_sdist(archive: Path, destination: Path) -> Path:
    with tarfile.open(archive, "r:gz") as source:
        for member in source.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk():
                raise RuntimeError(f"unsafe sdist member: {member.name}")
        source.extractall(destination, filter="data")
    roots = [entry for entry in destination.iterdir() if entry.is_dir()]
    if len(roots) != 1:
        raise RuntimeError("sdist must contain exactly one root directory")
    return roots[0]


def _safe_zip_members(archive: zipfile.ZipFile) -> list[str]:
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise RuntimeError("wheel contains duplicate members")
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            raise RuntimeError(f"unsafe wheel member: {name}")
    return names


def _verify_record(archive: zipfile.ZipFile, names: list[str]) -> None:
    records = [name for name in names if name.endswith(".dist-info/RECORD")]
    if len(records) != 1:
        raise RuntimeError("wheel must contain exactly one RECORD")
    rows = list(csv.reader(archive.read(records[0]).decode("utf-8").splitlines()))
    declared = {row[0]: row[1:] for row in rows}
    if set(declared) != set(names):
        raise RuntimeError("wheel RECORD inventory does not match wheel members")
    for name in names:
        digest, size = declared[name]
        if name == records[0]:
            if digest or size:
                raise RuntimeError("RECORD must not hash itself")
            continue
        value = archive.read(name)
        expected = base64.urlsafe_b64encode(hashlib.sha256(value).digest()).rstrip(b"=").decode()
        if digest != f"sha256={expected}" or size != str(len(value)):
            raise RuntimeError(f"invalid RECORD entry: {name}")


def _verify_wheel(
    wheel: Path, sdist_root: Path, official_wheel: Path, specification: dict[str, object]
) -> dict[str, str]:
    if wheel.name != _expected_wheel(specification):
        raise RuntimeError(f"unexpected wheel filename: {wheel.name}")
    with zipfile.ZipFile(wheel) as built, zipfile.ZipFile(official_wheel) as official:
        built_names = _safe_zip_members(built)
        official_names = _safe_zip_members(official)
        _verify_record(built, built_names)
        metadata_names = [name for name in built_names if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            raise RuntimeError("wheel must contain exactly one METADATA file")
        metadata = BytesParser().parsebytes(built.read(metadata_names[0]))
        if metadata["Name"] != "onepassword-sdk" or metadata["Version"] != PACKAGE_VERSION:
            raise RuntimeError("wheel package identity mismatch")
        if metadata["Requires-Python"] != ">=3.9" or metadata["License"] != "MIT":
            raise RuntimeError("wheel compatibility or license metadata mismatch")
        source_root = sdist_root / "src"
        for name in built_names:
            if ".dist-info/" in name or name.endswith("/"):
                continue
            source_name = name.removeprefix(PURELIB_PREFIX)
            source_file = source_root.joinpath(*PurePosixPath(source_name).parts)
            if not source_file.is_file() or source_file.read_bytes() != built.read(name):
                raise RuntimeError(f"built package member differs from the sdist: {name}")
        component_hashes: dict[str, str] = {}
        for relative_member in (specification["library"], specification["binding"]):
            member = f"{PURELIB_PREFIX}{relative_member}"
            source_value = source_root.joinpath(*PurePosixPath(str(relative_member)).parts).read_bytes()
            built_value = built.read(member)
            official_value = official.read(member)
            if source_value != built_value or source_value != official_value:
                raise RuntimeError(f"upstream component identity mismatch: {member}")
            component_hashes[member] = _sha256_bytes(source_value)
        official_package = {
            name for name in official_names if ".dist-info/" not in name and not name.endswith("/")
        }
        built_package = {
            name for name in built_names if ".dist-info/" not in name and not name.endswith("/")
        }
        if official_package != built_package:
            raise RuntimeError("official and built package inventories differ")
        return component_hashes


def _verify_ffi(wheel: Path, specification: dict[str, object]) -> None:
    with tempfile.TemporaryDirectory(prefix="atlaso-cp314-import-") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(wheel) as archive:
            _safe_zip_members(archive)
            archive.extractall(root)
        binding_member = f"{PURELIB_PREFIX}{specification['binding']}"
        binding = root.joinpath(*PurePosixPath(binding_member).parts)
        child = (
            "import importlib.util,sys;"
            "p=sys.argv[1];"
            "s=importlib.util.spec_from_file_location('atlaso_op_uniffi_core',p);"
            "m=importlib.util.module_from_spec(s);"
            "s.loader.exec_module(m);"
            "m._uniffi_check_contract_api_version(m._UniffiLib);"
            "m._uniffi_check_api_checksums(m._UniffiLib)"
        )
        subprocess.run([sys.executable, "-I", "-S", "-c", child, str(binding)], check=True)


def build(output: Path, target_name: str) -> None:
    specification = _target(target_name)
    _assert_runtime(specification)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("output directory must be empty")
    with tempfile.TemporaryDirectory(prefix="atlaso-cp314-build-") as temporary:
        root = Path(temporary)
        sdist = root / str(SDIST["filename"])
        official_specification = specification["official"]
        official = root / str(official_specification["filename"])
        _download(SDIST, sdist)
        _download(official_specification, official)
        source = _safe_extract_sdist(sdist, root / "source")
        environment = os.environ.copy()
        environment.update(
            {
                "PIP_CONFIG_FILE": os.devnull,
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PYTHONHASHSEED": "0",
                "PYTHON_OS_PLATFORM": str(specification["os_platform"]),
                "PYTHON_MACHINE_PLATFORM": str(specification["machine_platform"]),
                "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH,
                "_PYTHON_HOST_PLATFORM": str(specification["host_platform"]),
            }
        )
        subprocess.run(
            [
                sys.executable,
                "-I",
                "-m",
                "pip",
                "wheel",
                "--no-build-isolation",
                "--no-deps",
                "--no-index",
                "--wheel-dir",
                str(output),
                str(source),
            ],
            check=True,
            env=environment,
        )
        wheel = output / _expected_wheel(specification)
        components = _verify_wheel(wheel, source, official, specification)
        _verify_ffi(wheel, specification)
        manifest = {
            "artifact": {
                "filename": wheel.name,
                "sha256": _sha256(wheel),
                "size": wheel.stat().st_size,
                "tag": specification["wheel_tag"],
            },
            "build": {
                "machine": platform.machine().lower(),
                "python": ".".join(str(part) for part in sys.version_info[:3]),
                "source_date_epoch": int(SOURCE_DATE_EPOCH),
                "free_threaded": False,
            },
            "components": components,
            "license": "MIT",
            "package": "onepassword-sdk",
            "schema_version": 2,
            "source": {"cp313_wheel": official_specification, "sdist": SDIST},
            "target": target_name,
            "upstream": {
                "commit": "50b2adadef5d1cd6b71c387ea36599af62318100",
                "repository": "1Password/onepassword-sdk-python",
                "tag": "v0.4.1",
            },
            "version": PACKAGE_VERSION,
        }
        (output / "build-manifest.json").write_text(
            _canonical_json(manifest), encoding="utf-8", newline="\n"
        )


def assemble(first: Path, second: Path, output: Path, target_name: str) -> None:
    specification = _target(target_name)
    expected_wheel = _expected_wheel(specification)
    first_wheel = first / expected_wheel
    second_wheel = second / expected_wheel
    first_manifest = first / "build-manifest.json"
    second_manifest = second / "build-manifest.json"
    if first_wheel.read_bytes() != second_wheel.read_bytes():
        raise SystemExit("independent wheel builds are not byte-identical")
    if first_manifest.read_bytes() != second_manifest.read_bytes():
        raise SystemExit("independent build manifests are not byte-identical")
    manifest = json.loads(first_manifest.read_text(encoding="utf-8"))
    if manifest.get("target") != target_name:
        raise SystemExit("build manifest target mismatch")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("assembly output directory must be empty")
    shutil.copy2(first_wheel, output / first_wheel.name)
    shutil.copy2(first_manifest, output / "build-manifest.json")


def bundle(input_root: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("bundle output directory must be empty")
    manifests = []
    for target_name, specification in TARGETS.items():
        candidates = list(input_root.rglob(_expected_wheel(specification)))
        if len(candidates) != 1:
            raise SystemExit(f"expected exactly one reconciled wheel for {target_name}")
        wheel = candidates[0]
        manifest_path = wheel.parent / "build-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (
            manifest.get("target") != target_name
            or manifest.get("artifact", {}).get("filename") != wheel.name
            or manifest.get("artifact", {}).get("sha256") != _sha256(wheel)
            or manifest.get("artifact", {}).get("size") != wheel.stat().st_size
        ):
            raise SystemExit(f"reconciled manifest mismatch for {target_name}")
        shutil.copy2(wheel, output / wheel.name)
        manifests.append(manifest)
    provenance = {
        "artifacts": [manifest["artifact"] | {"target": manifest["target"]} for manifest in manifests],
        "builds": [
            {
                "build": manifest["build"],
                "components": manifest["components"],
                "official_cp313_wheel": manifest["source"]["cp313_wheel"],
                "target": manifest["target"],
            }
            for manifest in manifests
        ],
        "license": "MIT",
        "package": "onepassword-sdk",
        "release_tag": RELEASE_TAG,
        "schema_version": 2,
        "sdist": SDIST,
        "upstream": manifests[0]["upstream"],
        "version": PACKAGE_VERSION,
    }
    (output / "provenance.json").write_text(
        _canonical_json(provenance), encoding="utf-8", newline="\n"
    )
    packages = []
    relationships = []
    for manifest in manifests:
        target_name = manifest["target"]
        package_id = f"SPDXRef-Package-onepassword-sdk-{target_name.replace('_', '-')}"
        packages.append(
            {
                "SPDXID": package_id,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": manifest["artifact"]["sha256"]}
                ],
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": True,
                "licenseConcluded": "MIT",
                "licenseDeclared": "MIT",
                "name": f"onepassword-sdk-{target_name}",
                "supplier": "Organization: 1Password",
                "versionInfo": PACKAGE_VERSION,
            }
        )
        relationships.append(
            {
                "relatedSpdxElement": package_id,
                "relationshipType": "DESCRIBES",
                "spdxElementId": "SPDXRef-DOCUMENT",
            }
        )
    bundle_digest = _sha256_bytes((output / "provenance.json").read_bytes())
    sbom = {
        "SPDXID": "SPDXRef-DOCUMENT",
        "creationInfo": {
            "created": "2026-07-30T13:55:23Z",
            "creators": ["Tool: build-atlaso-cp314-wheel.py"],
        },
        "dataLicense": "CC0-1.0",
        "documentNamespace": (
            "https://github.com/mdaneri/onepassword-sdk-python/spdx/" + bundle_digest
        ),
        "name": f"onepassword-sdk-{PACKAGE_VERSION}-cp314-multiplatform",
        "packages": packages,
        "relationships": relationships,
        "spdxVersion": "SPDX-2.3",
    }
    (output / "sbom.spdx.json").write_text(
        _canonical_json(sbom), encoding="utf-8", newline="\n"
    )
    shutil.copy2(Path(__file__).resolve().parents[3] / "LICENSE", output / "LICENSE")


def stage_scan_materials(output: Path) -> None:
    """Stage every verified upstream input for one aggregate malware scan."""
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("scan-material output directory must be empty")
    sdist = output / str(SDIST["filename"])
    _download(SDIST, sdist)
    _safe_extract_sdist(sdist, output / "extracted-sdist")
    official_root = output / "official-cp313-wheels"
    official_root.mkdir()
    for specification in TARGETS.values():
        official = specification["official"]
        _download(official, official_root / str(official["filename"]))


def live_validate(
    wheel: Path, target_name: str, account: str, environment_id_file: Path, output: Path
) -> None:
    specification = _target(target_name)
    _assert_runtime(specification)
    if wheel.name != _expected_wheel(specification) or not wheel.is_file():
        raise SystemExit("the exact target CPython 3.14 compatibility wheel is required")
    environment_lines = environment_id_file.read_text(encoding="utf-8").splitlines()
    if len(environment_lines) != 1 or not environment_lines[0].strip():
        raise SystemExit("the Environment ID file must contain exactly one non-empty line")
    environment_id = environment_lines[0].strip()
    if not account.strip():
        raise SystemExit("the approved 1Password desktop account is required")
    with tempfile.TemporaryDirectory(prefix="atlaso-cp314-live-") as temporary:
        dependencies = Path(temporary) / "dependencies"
        environment = os.environ.copy()
        environment.update({"PIP_CONFIG_FILE": os.devnull, "PIP_DISABLE_PIP_VERSION_CHECK": "1"})
        subprocess.run(
            [sys.executable, "-I", "-m", "pip", "install", "--target", str(dependencies), str(wheel)],
            check=True,
            env=environment,
        )
        child = r'''import argparse,asyncio,sys
parser=argparse.ArgumentParser()
parser.add_argument('--dependency-path',required=True)
parser.add_argument('--account',required=True)
parser.add_argument('--environment-id',required=True)
args=parser.parse_args()
sys.path.insert(0,args.dependency_path)
from onepassword import Client,DesktopAuth
async def validate():
    client=await asyncio.wait_for(Client.authenticate(
        auth=DesktopAuth(account_name=args.account),
        integration_name='Atlaso CPython 3.14 wheel validation',
        integration_version='v1'),timeout=180)
    response=await asyncio.wait_for(
        client.environments.get_variables(args.environment_id),timeout=180)
    matches=[item for item in response.variables
             if item.name=='DEFAULT_ADMIN_PASSWORD']
    if len(matches)!=1 or not matches[0].masked or not matches[0].value:
        raise SystemExit('required concealed variable validation failed')
    matches[0].value=''
    del matches
    del response
asyncio.run(validate())
print('LIVE_VALIDATION_OK')
'''
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    "-c",
                    child,
                    "--dependency-path",
                    str(dependencies),
                    "--account",
                    account.strip(),
                    "--environment-id",
                    environment_id,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=240,
                env=environment,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            raise SystemExit("sanitized desktop authorization validation failed") from None
        if result.stdout.strip() != "LIVE_VALIDATION_OK" or result.stderr.strip():
            raise SystemExit("sanitized desktop authorization validation returned unexpected output")
    evidence = {
        "artifact_sha256": _sha256(wheel),
        "desktop_authorization": "passed",
        "environment_access": "passed",
        "secret_values_recorded": False,
        "target": target_name,
        "validated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "validator": "maintainer",
    }
    output.write_text(_canonical_json(evidence), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--output", required=True, type=Path)
    build_parser.add_argument("--target", required=True, choices=TARGETS)
    assemble_parser = subparsers.add_parser("assemble")
    assemble_parser.add_argument("--first", required=True, type=Path)
    assemble_parser.add_argument("--second", required=True, type=Path)
    assemble_parser.add_argument("--output", required=True, type=Path)
    assemble_parser.add_argument("--target", required=True, choices=TARGETS)
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--input-root", required=True, type=Path)
    bundle_parser.add_argument("--output", required=True, type=Path)
    scan_parser = subparsers.add_parser("stage-scan-materials")
    scan_parser.add_argument("--output", required=True, type=Path)
    live_parser = subparsers.add_parser("live-validate")
    live_parser.add_argument("--wheel", required=True, type=Path)
    live_parser.add_argument("--target", required=True, choices=TARGETS)
    live_parser.add_argument("--account", required=True)
    live_parser.add_argument("--environment-id-file", required=True, type=Path)
    live_parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    if arguments.command == "build":
        build(arguments.output, arguments.target)
    elif arguments.command == "assemble":
        assemble(arguments.first, arguments.second, arguments.output, arguments.target)
    elif arguments.command == "bundle":
        bundle(arguments.input_root, arguments.output)
    elif arguments.command == "stage-scan-materials":
        stage_scan_materials(arguments.output)
    else:
        live_validate(
            arguments.wheel,
            arguments.target,
            arguments.account,
            arguments.environment_id_file,
            arguments.output,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
