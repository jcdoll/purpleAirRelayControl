# ESP32-S3 MicroPython Implementation

Control HVAC ventilation based on PurpleAir air quality sensor data using ESP32-S3 Reverse TFT Feather with integrated display.

## Quick Start

1. [Setup Guide](docs/setup.md) - Complete installation and setup instructions
2. [Hardware Guide](docs/hardware.md) - Pin assignments and hardware details  
3. [Development Guide](docs/development.md) - Development rules and workflow

## Project Overview

This MicroPython implementation provides automated air quality-based ventilation control featuring:

- Real-time monitoring of indoor and outdoor air quality (PurpleAir sensors)
- Automated ventilation control based on configurable AQI thresholds
- Visual status display on built-in 1.14" TFT screen
- LED status indicators using built-in NeoPixel
- Data logging to Google Sheets for trend analysis
- Manual override via tactile buttons

## Hardware

- ESP32-S3 Reverse TFT Feather (Adafruit #5691) with built-in display and buttons
- Relay modules for ventilation control
- PurpleAir sensors for indoor/outdoor air quality monitoring

## Platform: MicroPython

Why MicroPython?
- Rapid development with no compile step
- Interactive REPL debugging
- Clear, maintainable Python syntax
- Excellent hardware support for ESP32-S3

## Documentation

All documentation is organized in the [`docs/`](docs/) directory:

- [Setup Guide](docs/setup.md) - MicroPython installation, bootloader setup, and project deployment
- [Hardware Documentation](docs/hardware.md) - Complete pin assignments and troubleshooting
- [Development Guidelines](docs/development.md) - Critical rules, workflow, and best practices
- [Reference Materials](docs/reference/) - Command references and technical details

## Getting Started

Important: Read the [Setup Guide](docs/setup.md) carefully, especially the bootloader configuration steps for Adafruit boards.

1. Hardware Setup: Connect ESP32-S3 board and optional relays
2. Software Setup: Follow [docs/setup.md](docs/setup.md) for MicroPython installation
3. Configuration: Copy and edit configuration files
4. Deployment: Use included deploy script to upload code
5. Testing: Verify display, LED, and sensor connectivity

## Project Structure

```
esp32/
├── docs/                   # All documentation
│   ├── setup.md            #   Complete setup guide
│   ├── hardware.md         #   Hardware specifications
│   ├── development.md      #   Development guidelines
│   └── reference/          #   Command references
├── main.py                 # Main application
├── config.py               # Hardware and system configuration
├── display_manager.py      # TFT display control
├── led_manager.py          # NeoPixel LED control
├── purple_air.py           # Air quality sensor interface
├── ventilation.py          # Ventilation control logic
├── wifi_manager.py         # WiFi connection management
├── google_logger.py        # Data logging to Google Sheets
├── utils/                  # Shared utility modules
└── lib/                    # External libraries
```

## Key Features

- Event-based logging: Status changes trigger immediate console output
- Memory-efficient display: Software frame buffer prevents screen flashing
- Robust error handling: Comprehensive exception handling and recovery
- Single source of truth: All pin assignments centralized in `config.py`
- Modular architecture: Separated concerns for display, LED, sensors, and ventilation

## Support

- Setup Issues: Check [docs/setup.md Common Issues](docs/setup.md#common-issues)
- Hardware Problems: See [docs/hardware.md Troubleshooting](docs/hardware.md#common-hardware-issues)  
- Development Questions: Review [docs/development.md](docs/development.md)

## License

See [LICENSE](../LICENSE) file for license information.
