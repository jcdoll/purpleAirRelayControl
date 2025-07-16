# ESP32 MicroPython Documentation

This directory contains comprehensive documentation for the ESP32-S3 Reverse TFT Feather MicroPython implementation of the PurpleAir Relay Control system.

## Quick Start

1. [Setup Guide](setup.md) - Complete installation and configuration guide
2. [Hardware Documentation](hardware.md) - Pin assignments and hardware details
3. [Development Guidelines](development.md) - Development rules and best practices

## Documentation Structure

### Core Documentation
- [setup.md](setup.md) - MicroPython installation, bootloader setup, testing, and project deployment
- [hardware.md](hardware.md) - Hardware specifications, pin assignments, and troubleshooting
- [development.md](development.md) - Development rules, workflow, and coding guidelines

### Reference Materials
- [reference/mpremote.md](reference/mpremote.md) - mpremote command reference
- [reference/deployment.md](reference/deployment.md) - Deploy script improvements and history

## Key Information

### Hardware Safety
CRITICAL: Always confirm device bootloader state before flash operations. See [Hardware Safety Rules](development.md#hardware-safety-rules).

### MicroPython Constraints
NO UNICODE OR DOCSTRINGS: MicroPython cannot handle UTF-8 files with Unicode characters or triple-quoted docstrings. See [Critical Rules](development.md#critical-rules).

### Single Source of Truth
- Pin assignments: Defined in `config.py`, documented in [hardware.md](hardware.md)
- Hardware details: Only in [hardware.md](hardware.md)  
- Setup instructions: Only in [setup.md](setup.md)
- Development workflow: Only in [development.md](development.md)

## Getting Help

1. Setup issues: Check [setup.md Common Issues](setup.md#common-issues)
2. Hardware problems: Check [hardware.md Troubleshooting](hardware.md#common-hardware-issues)
3. Development questions: Check [development.md](development.md)
4. Command reference: Check [reference/mpremote.md](reference/mpremote.md)

## Project Overview

This MicroPython implementation controls HVAC ventilation based on PurpleAir sensor data, featuring:

- ESP32-S3 Reverse TFT Feather with built-in display and NeoPixel LED
- Real-time air quality monitoring from indoor and outdoor sensors
- Automated ventilation control based on AQI thresholds
- Visual status display with TFT screen showing current conditions
- LED status indicators for system state
- Google Sheets logging for data tracking

For project source code and implementation details, see the main project files in the parent directory. 