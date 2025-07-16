# Development Guidelines

## Overview

This guide contains essential development rules, best practices, and workflows for the ESP32 MicroPython project.

## Golden Rules

- Do not create a new file when you should modify an existing file
- Do not use unicode characters or emoji
- Do not overuse styling in markdown documentation - use it very rarely for emphasis

## Critical Rules

### 1. NO UNICODE CHARACTERS OR DOCSTRINGS

NEVER use Unicode characters, emojis, or special symbols in ANY file:
- This includes any non-ASCII characters like check marks, arrows, warning symbols, or emojis
- MicroPython on ESP32 cannot handle UTF-8 files with Unicode characters
- Files with Unicode will fail to deploy with `OSError: [Errno 5] EIO`

Use ASCII alternatives instead:
- Check marks: [OK] or OK
- X marks: [FAIL] or FAIL  
- Arrows: -> or =>
- Warnings: [WARNING] or WARNING

NEVER use triple-quoted strings (""") for docstrings or comments in micropython code:
- MicroPython allocates docstrings as continuous heap blocks, causing memory issues
- Files with docstrings will fail to deploy with `OSError: [Errno 5] EIO`
- Always use regular # comments instead

```python
# GOOD - uses regular comments
def my_function():
    # This function does something
    pass

# BAD - uses docstring (will fail)
def my_function():
    """This function does something"""
    pass
```

### 2. Hardware Safety Rules

NEVER perform hardware operations without confirming device state:
- Always ask about current bootloader configurations before destructive operations
- User may have specific setups (TinyUF2, CircuitPython) that should not be overwritten
- Confirm the plan with the user before executing `erase_flash` or `write_flash`
- Remember: AI has limited visibility into hardware state

### 3. File Management

Always add new Python files to `deploy.py` FILES list:
- Test scripts must be added to deployment or they won't be accessible on the board
- Keep all ESP32 code in the `/esp32` directory
- Use descriptive filenames (e.g., `test_neopixel.py` not `test.py`)

## Code Style Guidelines

### Error Handling
```python
try:
    # your code
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import sys
    sys.print_exception(e)
```

### Hardware Initialization
```python
import config

# Always keep power pin references alive
neopixel_power = Pin(config.NEOPIXEL_POWER_PIN, Pin.OUT)
neopixel_power.value(1)  # Don't let this get garbage collected

# Initialize hardware in try/except blocks
try:
    display = init_display()
except Exception as e:
    print(f"Display init failed: {e}")
    display = None
```

### Configuration Management
- All hardware pin assignments are defined in `config.py`
- For pin details see [Hardware Documentation](hardware.md)
- Use clear print statements for debugging (they show in REPL)
- Don't use comments as the only documentation - use print statements for runtime info

## Development Workflow

### Basic Deploy and Test Cycle

```bash
# 1. Make your changes
# 2. Add new files to deploy.py if needed
# 3. Deploy all files
python deploy.py

# 4. Test your changes
mpremote connect auto repl
>>> import your_module

# Or run directly
mpremote connect auto exec "import your_module"
```

### Testing Individual Components

```bash
# Test LED functionality
mpremote exec "import simple_led_test"

# Test display
mpremote exec "import hardware_test"

# Check board configuration
mpremote exec "import check_board"
```

### Running Main Application

```bash
# Interactive mode
mpremote repl
>>> import main

# Direct execution
mpremote exec "import main"

# Reset and run
mpremote reset
mpremote exec "import main"
```

## Debugging

### Monitor Board Activity
```bash
# View files on board
mpremote ls
mpremote cat main.py

# Interactive debugging
mpremote repl
# Press Ctrl+C to interrupt running code
# Press Ctrl+D to soft reset
# Press Ctrl+X to exit
```

### Memory Monitoring
```python
import gc
print(f"Free: {gc.mem_free()}, Used: {gc.mem_alloc()}")
gc.collect()  # Force garbage collection
```

### Common Issues and Solutions

ImportError: no module named 'xyz'
- File not added to deploy.py
- Deployment failed
- Check with: `mpremote ls`

Serial timeout/disconnect
- Board crashed or reset
- Check for infinite loops
- Add delays in hardware initialization
- Use minimal test scripts to verify stability

LED not working
- See [Hardware Documentation](hardware.md) for troubleshooting

Indentation errors when pasting
- DON'T paste multi-line code in REPL
- Create a script file and import it

## Hardware Considerations

### Pin Management
- Always initialize power pins for peripherals (see [Hardware Documentation](hardware.md))
- Test hardware components independently before integration
- All pin assignments are centralized in `config.py`

### Memory Management
- ESP32-S3 has limited RAM (~300KB available)
- Use `gc.collect()` periodically in long-running loops
- Monitor memory usage during development
- Avoid large string concatenations

### Network Operations
- Always use timeouts on HTTP requests
- Close responses after use to free memory
- Handle connection failures gracefully
- Prefer local sensor polling over frequent API calls

## Project Structure

### Current Architecture
```
esp32/
├── main.py              # Main application loop
├── config.py            # Configuration and pin definitions
├── display_manager.py   # TFT display with frame buffer
├── led_manager.py       # NeoPixel LED status control
├── purple_air.py        # PurpleAir API client
├── ventilation.py       # Relay control logic
├── wifi_manager.py      # WiFi connection management
├── google_logger.py     # Data logging to Google Sheets
├── utils/               # Shared utility modules
│   ├── error_handling.py
│   ├── aqi_colors.py
│   ├── connection_retry.py
│   └── status_display.py
└── lib/                 # External libraries
    ├── st7789py.py
    └── vga1_8x8.py
```

### File Organization Rules
- Core application logic in root directory
- Shared utilities in `utils/` directory
- External libraries in `lib/` directory
- Configuration in dedicated config files
- No duplicate code between modules

## Quality Assurance

### Pre-deployment Checklist
1. [ ] File added to deploy.py?
2. [ ] No Unicode characters or docstrings?
3. [ ] Error handling added?
4. [ ] Hardware pins configured correctly?
5. [ ] Memory usage reasonable?
6. [ ] Testing completed?

### Performance Guidelines
- Keep main loop responsive (< 1 second per iteration)
- Minimize print statements in production code
- Use local variables in loops
- Batch I/O operations when possible

## Emergency Recovery

### Filesystem Corruption
If you get persistent `OSError: [Errno 5] EIO` errors:

```python
import os
import flashbdev

# Format the filesystem (LAST RESORT)
os.umount('/')
os.VfsFat.mkfs(flashbdev.bdev)
os.mount(flashbdev.bdev, '/')
print(os.listdir())  # Should be empty after format
```

### Hardware Recovery
If TinyUF2 bootloader was accidentally overwritten:

1. Re-flash TinyUF2 bootloader first:
   ```bash
   esptool --chip esp32s3 --port COMx write-flash 0x0 tinyuf2-adafruit_feather_esp32s3_tft-0.33.0-combined.bin
   ```

2. Then flash MicroPython using UF2 method

3. Test functionality before proceeding

## Quick Command Reference

For basic setup commands, see [Setup Guide](setup.md). For comprehensive command reference, see [mpremote Reference](reference/mpremote.md).

Development Workflow:
```bash
# Deploy everything
python deploy.py

# Interactive debugging
mpremote repl

# Test specific modules
mpremote exec "import module_name"

# Check board status
mpremote exec "import gc; print(gc.mem_free())"
```

## Future Improvements

### Planned Quality Tools (Phase 2)
- [ ] Set up pytest framework with hardware mocking
- [ ] Add code formatting with black
- [ ] Implement linting with flake8
- [ ] Add type checking where possible
- [ ] Create CI/CD pipeline
- [ ] Add automated testing

### Code Organization (Ongoing)
- [x] Split large modules (ui_manager.py → display_manager.py + led_manager.py)
- [x] Create shared utilities to eliminate code duplication
- [x] Consolidate documentation structure
- [ ] Add comprehensive unit tests
- [ ] Implement configuration validation

## Documentation Standards

- No excessive bold formatting in markdown documents
- Apply changes directly - don't suggest changes for users to apply
- Use clear, actionable language in documentation
- Include code examples for complex procedures
- Keep hardware safety warnings prominent

## Git Workflow

- Don't commit `secrets.py` (it's in .gitignore)
- Test changes locally before committing
- Update documentation when adding new procedures
- Document hardware changes in hardware.md
- Keep commit messages descriptive and focused 

## Local Pre-commit Hooks

This repository can use the **pre-commit** framework to run a battery of quality tools on staged files.

Tools executed (in order):
1. **Black** – opinionated code formatter; rewrites files for consistent style.
2. **isort** – sorts imports into logical groups; auto-fixes in place.
3. **Ruff** – fast linter that auto-fixes many common issues (unused imports, bare `except`, etc.).
4. **flake8** – final linter pass that reports anything Ruff couldn’t auto-fix.

One-time setup (optional):
```bash
# Inside the project root (venv active)
pip install pre-commit  # already in requirements.txt
pre-commit install       # installs the .git/hooks/pre-commit script
```

After that, `git commit` will run the hooks **only if you installed them**.

If you skip this step the commit proceeds normally; you can still run all checks and auto-fixes manually at any time:
```bash
pre-commit run --all-files
```

Current POR is to NOT install pre-commit by default; developers may run it manually when desired.