# AGENTS.md

Guidance for agents working in this repository.

## Project

PurpleAir Relay Control monitors PurpleAir air quality data, controls ventilation relays, logs measurements to Google Sheets, and includes a static React app for viewing that logged data.

Main areas:
- `arduino/` - Arduino MKR WiFi 1010 firmware.
- `esp32/` - ESP32-S3 MicroPython firmware, deployment tools, host tests, and docs.
- `dashboard/` - Create React App viewer for Google Sheets CSV data.
- `scripts/filter_efficiency_analysis/` - Python filter efficiency analysis.
- `case/` - OpenSCAD enclosure files.

Dashboard behavior from the code:
- `dashboard/src/App.js` fetches two CSV exports from Google Sheets URLs defined in `dashboard/src/constants/app.js`.
- The main air-quality CSV is parsed with PapaParse and expects `Timestamp`, `IndoorAirQuality`, `OutdoorAirQuality`, `SwitchState`, `VentilationState`, and optional `Reason`.
- The filter CSV expects `Timestamp`, `Estimated Filter Efficiency (%)`, `Efficiency Uncertainty (%)`, `Indoor PM2.5`, and `Outdoor PM2.5`.
- The app refreshes both CSVs every 5 minutes, shows latest indoor/outdoor AQI summary cards, and renders selectable ApexCharts views: Timeline, Recent heatmap, Hourly Analysis, Correlation, Annual, and Filter Efficiency.

## Hard Rules

- Do not add Unicode or emojis to code, docs, tests, scripts, comments, or console output. Python on Windows can fail when the active encoding cannot represent Unicode characters; MicroPython deployment can also fail on UTF-8/non-ASCII files. Use `OK`, `FAIL`, `->`, and `[WARNING]`. Some dashboard files already contain legacy emoji; do not add more, and replace them with ASCII if editing those lines.
- Never commit secrets. Keep `arduino/arduino_secrets.h`, `esp32/secrets.py`, Google service-account JSON, API keys, WiFi credentials, and private Google Forms/Sheets credentials out of git.
- Never flash, erase, format, deploy to, or remove files from a connected microcontroller without explicit user confirmation of the device, port, bootloader state, and intended command.
- Never run destructive git commands such as `git reset --hard` or path checkout unless the user explicitly asks for that exact operation.
- Do not add unrequested features. For hardware-facing behavior, threshold changes, relay defaults, pin changes, or switch mapping, discuss the plan first.

## Before Editing

- For ESP32 work, read `esp32/docs/development.md`; for pin or board behavior, also read `esp32/docs/hardware.md`.
- For Arduino work, read `arduino/README.md`.
- For dashboard work, read `dashboard/README.md`.
- For filter analysis work, read `scripts/filter_efficiency_analysis/README.md` and `scripts/filter_efficiency_analysis/PHYSICS.md`.
- Prefer editing existing files over creating new ones.
- Work with existing uncommitted user changes; do not revert unrelated edits.

## Commands

Dashboard:

```powershell
cd dashboard
npm ci
$env:CI="true"; npm test -- --watchAll=false
npm run build
```

ESP32 host tests:

```powershell
cd esp32
python -m pip install -r requirements.txt
pytest tests/host/ --cov=esp32 --cov-branch --cov-report=term-missing
```

ESP32 board commands, only after explicit user confirmation:

```powershell
cd esp32
python deploy.py --list
python deploy.py
python deploy.py --clean
mpremote connect auto repl
```

Filter analysis:

```powershell
cd scripts/filter_efficiency_analysis
python -m pip install -r requirements.txt
python -m pytest tests/ -v --cov=utils --cov=models --cov-report=term-missing
python analyze_filter_performance.py --dry-run
```

## Component Notes

- ESP32: all hardware constants belong in `esp32/config.py`; deployed files must be listed in `esp32/deploy_manifest.txt`; do not use triple-quoted docstrings in MicroPython files.
- Arduino: keep timing, pins, network, and logging constants in `arduino/constants.h`; preserve safe relay behavior for unknown switch states and missing sensor data.
- Dashboard: must remain a static GitHub Pages app; do not add a backend or put secrets in client code.
- Filter analysis: treat results as experimental; use synthetic data for tests; do not write to Google Sheets unless the user explicitly asks for a live write.

## Verification

Run the relevant tests/build for the component you changed. If hardware, Arduino IDE, or live Google integration is required and you cannot run it, say exactly what was not verified.
