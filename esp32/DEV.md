# ESP32 Development Guide

## Golden rules

- Do not create a new file when you should modify an existing file.
- Do not use unicode characters or emoji
- Do not overuse bold or other style adjustments in markdown documentation - use it very rarely for emphasis.

## Development Rules and Best Practices

### 1. NO UNICODE CHARACTERS OR DOCSTRINGS - CRITICAL
- **NEVER** use Unicode characters, emojis, or special symbols in ANY file
- This includes: ✓ ✗ → ⚠️ 🔧 or any other non-ASCII characters
- MicroPython on ESP32 cannot handle UTF-8 files with Unicode characters
- Files with Unicode will fail to deploy with `OSError: [Errno 5] EIO`
- Use ASCII alternatives instead:
  - ✓ → [OK] or OK
  - ✗ → [FAIL] or FAIL  
  - → → -> or =>
  - ⚠ → [WARNING] or WARNING
- This applies to ALL files: Python code, comments, docstrings, print statements

- **NEVER** use triple-quoted strings (""") for docstrings or comments
- MicroPython allocates docstrings as continuous heap blocks, causing memory issues
- Files with docstrings will fail to deploy with `OSError: [Errno 5] EIO`
- Always use regular # comments instead:
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

### 2. File Management
- **ALWAYS** add new Python files to `deploy.py` FILES list
- Test scripts must be added to deployment or they won't be accessible on the board
- Keep all ESP32 code in the `/esp32` directory
- Use descriptive filenames (e.g., `test_neopixel.py` not `test.py`)

### 3. Code Style
- Use clear print statements for debugging (they show in REPL)
- Add error handling with stack traces:
  ```python
  try:
      # your code
  except Exception as e:
      print(f"Error: {type(e).__name__}: {e}")
      import sys
      sys.print_exception(e)
  ```
- Keep hardware pin assignments in `config.py`
- Don't use comments as the only documentation - use print statements for runtime info

### 4. Hardware Considerations
- Always keep power pin references alive (don't let them get garbage collected)
- Initialize hardware in try/except blocks
- Test hardware components independently before integration
- Pin assignments for ESP32-S3 Reverse TFT Feather:
  - NeoPixel: Data=33, Power=34
  - Display: See HARDWARE.md

### 5. Development Workflow

#### Basic Deploy and Test Cycle
```bash
# 1. Make your changes
# 2. Add new files to deploy.py if needed
# 3. Deploy all files
python deploy.py

# 4. Test your changes
mpremote connect COM5 repl
>>> import your_module

# Or run directly
mpremote connect COM5 exec "import your_module"
```

#### Testing Hardware
```bash
# Test LED
mpremote connect COM5 exec "import simple_led_test"

# Test display
mpremote connect COM5 exec "import hardware_test"

# Check board configuration
mpremote connect COM5 exec "import check_board"
```

#### Running Main Application
```bash
# Since boot.py no longer auto-imports main:
mpremote connect COM5 repl
>>> import main

# Or to reset and run
mpremote connect COM5 reset
mpremote connect COM5 exec "import main"
```

### 6. Debugging

#### View Files on Board
```bash
mpremote connect COM5 ls
mpremote connect COM5 cat main.py
```

#### Monitor Output
```bash
mpremote connect COM5 repl
# Press Ctrl+C to interrupt running code
# Press Ctrl+D to soft reset
# Press Ctrl+X to exit
```

#### Common Issues
1. **ImportError: no module named 'xyz'**
   - File not added to deploy.py
   - Deployment failed
   - Check with: `mpremote connect COM5 ls`

2. **Serial timeout/disconnect**
   - Board crashed or reset
   - Check for infinite loops
   - Add delays in hardware initialization
   - Use minimal_test.py to verify stability

3. **LED not working**
   - Power pin must be HIGH (pin 34)
   - Keep power pin reference alive
   - Check neopixel module is installed

4. **Indentation errors when pasting**
   - DON'T paste multi-line code in REPL
   - Create a script file and import it

### 7. Testing (Not Yet Implemented)

#### Future PyTest Setup
```bash
# Install pytest and pytest-mock
pip install pytest pytest-mock

# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

#### Test Structure (Planned)
```
esp32/
├── tests/
│   ├── test_purple_air.py
│   ├── test_ventilation.py
│   └── test_hardware_mock.py
├── conftest.py  # PyTest configuration
└── requirements-dev.txt
```

### 8. Memory Management
- ESP32-S3 has limited RAM
- Use `gc.collect()` periodically
- Monitor memory with:
  ```python
  import gc
  print(f"Free: {gc.mem_free()}, Used: {gc.mem_alloc()}")
  ```

### 9. Network Requests
- Always use timeouts on requests
- Close responses after use
- Handle connection failures gracefully
- Local sensor polling should be preferred over API calls

### 10. Git Workflow
- Don't commit `secrets.py` (it's in .gitignore)
- Test changes locally before committing
- Update DEV.md when adding new development procedures
- Document hardware changes in HARDWARE.md

### 11. Performance Tips
- Minimize print statements in production
- Use local variables in loops
- Batch I/O operations when possible
- Keep the main loop responsive (< 1 second per iteration)

## Quick Commands Reference

```bash
# Deploy everything
python deploy.py

# Quick test
mpremote connect COM5 exec "import simple_led_test"

# Interactive REPL
mpremote connect COM5 repl

# View files
mpremote connect COM5 ls

# Read a file
mpremote connect COM5 cat config.py

# Remove a file
mpremote connect COM5 rm test.py

# Reset board
mpremote connect COM5 reset

# Run main application
mpremote connect COM5 exec "import main"
```

## Troubleshooting Checklist

1. [ ] File added to deploy.py?
2. [ ] Deployment successful?
3. [ ] No import errors?
4. [ ] Hardware pins correct?
5. [ ] Power pins set HIGH?
6. [ ] Try/except blocks added?
7. [ ] Serial connection stable?
8. [ ] Memory usage OK?

## Last Resort - Filesystem Corruption

If you get persistent `OSError: [Errno 5] EIO` errors or `UnicodeError` when listing files, the filesystem may be corrupted. This can happen if a file with invalid Unicode characters gets created.

### Fix corrupted filesystem:
```python
import os
import flashbdev

# Format the filesystem
os.umount('/')
os.VfsFat.mkfs(flashbdev.bdev)
os.mount(flashbdev.bdev, '/')

# Now try to list
print(os.listdir())
```

If that doesn't work, try a hard reset:
```python
import machine
machine.reset_cause()  # Check what caused last reset
machine.reset()  # Hard reset
```

After formatting, you'll need to redeploy all files.

## TODO
- [ ] Set up pytest framework
- [ ] Add hardware mocking for tests
- [ ] Create CI/CD pipeline
- [ ] Add code formatting (black)
- [ ] Add type hints where possible

# Development Notes and Guidelines

## CRITICAL HARDWARE GUIDELINES

### ⚠️ NEVER FLASH WITHOUT CONFIRMING DEVICE STATE FIRST

**ALWAYS ask the user about current device state before any flash operations:**

- User may have specific bootloader configurations (TinyUF2, CircuitPython, etc.)
- Adafruit boards often require TinyUF2 bootloader for proper operation
- Generic MicroPython firmware may not work on boards with custom partition layouts
- Erasing flash can destroy working bootloader configurations

**Required confirmation before flash operations:**
1. Ask: "What bootloader is currently installed?"
2. Ask: "What was the last working firmware configuration?"
3. Confirm: "I plan to do X, Y, Z - is this correct?"
4. Wait for explicit user approval before executing

**Remember:** AI has limited visibility into hardware state. User knows their setup better.

## Hardware Recovery

If TinyUF2 bootloader was accidentally overwritten:

1. Re-flash TinyUF2 bootloader first:
   ```bash
   esptool --chip esp32s3 --port COMx write-flash 0x0 tinyuf2-adafruit_feather_esp32s3_tft-0.33.0-combined.bin
   ```

2. Then flash MicroPython using UF2 method or at proper offset

3. Test functionality before proceeding with deployment

## Additional Notes

- Document working configurations before making changes
- Keep backup of known-good firmware files
- Test incremental changes rather than full reformats