#!/usr/bin/env python3
"""
Deploy all files to ESP32 running MicroPython
Cross-platform deployment script
"""

import subprocess
import sys
import os
from pathlib import Path

# Files to deploy
FILES = [
    "lib/st7789py.py",  # Display driver
    "boot.py",
    "main.py",
    "config.py",
    "secrets.py",  # Your private credentials
    "wifi_manager.py",
    "purple_air.py",
    "ventilation.py",
    "display_ui.py",
    "google_logger.py",
]

def find_port():
    """Try to find the ESP32 port automatically"""
    try:
        result = subprocess.run(
            ["mpremote", "connect", "auto"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return "auto"
    except:
        pass
    
    # Default ports to try
    if sys.platform == "win32":
        return "COM5"  # Update this to your port
    elif sys.platform == "darwin":
        return "/dev/tty.usbserial-0001"
    else:
        return "/dev/ttyUSB0"

def deploy(port=None):
    """Deploy all files to ESP32"""
    if port is None:
        port = find_port()
    
    print(f"Deploying to ESP32 on port {port}...")
    
    # Build the command
    cmd = ["mpremote", "connect", port]
    
    # Add each file copy command
    for i, file in enumerate(FILES):
        if not Path(file).exists():
            print(f"Warning: {file} not found, skipping...")
            continue
            
        # For lib files, ensure the directory exists
        if file.startswith("lib/"):
            target = f":{file}"
        else:
            target = f":{Path(file).name}"
        
        cmd.extend(["cp", file, target])
        
        # Add + between commands (except for the last one)
        if i < len(FILES) - 1:
            cmd.append("+")
    
    # Add reset at the end
    cmd.extend(["+", "reset"])
    
    # Run the command
    try:
        print("Running:", " ".join(cmd[:4]) + "...")
        result = subprocess.run(cmd, check=True)
        print("Deployment complete!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Deployment failed: {e}")
        return False
    except FileNotFoundError:
        print("Error: mpremote not found. Install it with: pip install mpremote")
        return False

if __name__ == "__main__":
    # Allow port override from command line
    port = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Check if we have all required files
    missing = [f for f in FILES if not Path(f).exists() and f != "lib/st7789py.py"]
    if missing:
        print("Missing required files:")
        for f in missing:
            print(f"  - {f}")
        print("\nMake sure all project files are in the current directory.")
        sys.exit(1)
    
    # Deploy
    if deploy(port):
        print("\nTo monitor output, run:")
        print(f"  mpremote connect {port or find_port()} repl")
    else:
        sys.exit(1)