import importlib.util
from pathlib import Path

# Dynamically load the deploy module so we do not rely on it being a package
# Locate esp32/deploy.py regardless of where tests are executed from
ESP32_DIR = Path(__file__).resolve().parents[3]
DEPLOY_PATH = ESP32_DIR / "deploy.py"

spec = importlib.util.spec_from_file_location("deploy", DEPLOY_PATH)
deploy = importlib.util.module_from_spec(spec)  # type: ignore
spec.loader.exec_module(deploy)  # type: ignore


def test_load_manifest(tmp_path):
    """load_manifest should ignore blanks, strip inline comments, preserve order."""
    manifest_content = (
        "\n# comment line\n" "lib/foo.py\n" "secrets.py  # comment inline\n" "\nutils/bar.py  \n" "# another comment\n"
    )
    manifest_file = tmp_path / "manifest.txt"
    manifest_file.write_text(manifest_content)

    files = deploy.load_manifest(manifest_file)

    assert files == ["lib/foo.py", "secrets.py", "utils/bar.py"]


def test_get_required_directories():
    files = [
        "lib/foo.py",
        "utils/bar.py",
        "boot.py",
        "lib/baz.py",
    ]
    dirs = deploy.get_required_directories(files)

    # Should include unique top-level dirs, root-level files ignored
    assert dirs == {"lib", "utils"}
