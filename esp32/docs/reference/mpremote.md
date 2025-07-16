# mpremote Quick Reference

## Common Commands

### Connection
```bash
# Connect to device
mpremote connect COM3              # Windows
mpremote connect /dev/ttyUSB0      # Linux
mpremote connect /dev/tty.usbserial-0001  # Mac

# Auto-connect (finds first available device)
mpremote
```

### File Operations
```bash
# Copy file to device
mpremote cp local_file.py :remote_file.py

# Copy all Python files
mpremote cp *.py :

# Copy file from device
mpremote cp :remote_file.py local_file.py

# List files on device
mpremote ls
mpremote ls lib/

# Remove file from device
mpremote rm :file.py

# Create directory
mpremote mkdir :lib
```

### Running Code
```bash
# Enter REPL
mpremote repl
# Exit with Ctrl+X

# Run a file on device
mpremote run script.py

# Execute Python command
mpremote exec "print('Hello')"
mpremote exec "import gc; print(gc.mem_free())"

# Reset device
mpremote reset

# Soft reset (Ctrl+D in REPL)
mpremote exec "import machine; machine.soft_reset()"
```

### Development Workflow
```bash
# Mount local directory (edit locally, run on device)
mpremote mount .
# Files are accessible on device but not copied

# Install packages with mip
mpremote mip install github:russhughes/st7789s3_mpy

# Chain commands
mpremote connect COM3 cp main.py : + reset
```

### Keyboard Shortcuts (in REPL)
- `Ctrl+A`: Enter raw REPL mode
- `Ctrl+B`: Exit raw REPL mode
- `Ctrl+C`: Interrupt running program
- `Ctrl+D`: Soft reset
- `Ctrl+E`: Enter paste mode
- `Ctrl+X`: Exit mpremote

### Troubleshooting
```bash
# Get device info
mpremote exec "import os; print(os.uname())"

# Check free memory
mpremote exec "import gc; gc.collect(); print(f'Free: {gc.mem_free()/1024:.1f}KB')"

# List running threads
mpremote exec "import _thread; print(_thread.list())"

# Check filesystem
mpremote exec "import os; print(os.statvfs('/'))"
```

### Windows-Specific Tips
- Use `COM3` (or your port) instead of `/dev/ttyUSB0`
- If permission denied, run as Administrator
- For WSL, use Windows COM ports directly

### Useful Aliases (add to .bashrc/.zshrc)
```bash
alias mpr='mpremote'
alias mprrepl='mpremote repl'
alias mprls='mpremote ls'
alias mprup='mpremote cp *.py : + reset'
```