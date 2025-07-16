import importlib
import pathlib

ESP32_PATH = pathlib.Path(__file__).resolve().parents[2]  # esp32 directory

python_files = [p for p in ESP32_PATH.glob('*.py') if p.name not in {'secrets.py', 'secrets_template.py', 'venv'}]

# Include subdirectory utils/*.py, scripts/*.py
python_files += list((ESP32_PATH / 'utils').glob('*.py'))
python_files += list((ESP32_PATH / 'scripts').glob('*.py'))

# Convert to module import paths relative to esp32 package root
module_names = []
for file_path in python_files:
    rel = file_path.relative_to(ESP32_PATH)
    if rel.parts[0] == 'scripts':
        # scripts are imported as scripts.<name>
        module_names.append('scripts.' + file_path.stem)
    elif rel.parts[0] == 'utils':
        module_names.append('utils.' + file_path.stem)
    else:
        module_names.append(file_path.stem)


def test_import_all_modules():
    """Ensure every esp32 python file imports cleanly under host stubs."""
    failed = []
    for name in module_names:
        try:
            importlib.import_module(name)
        except Exception as e:
            failed.append((name, str(e)))
    assert not failed, f"Modules failed to import: {failed}"
