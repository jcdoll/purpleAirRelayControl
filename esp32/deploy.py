#!/usr/bin/env python3
"""
Deploy files to ESP32 running MicroPython
Modern deployment script following 2024/2025 best practices

MODERN DEPLOYMENT BEST PRACTICES:

1. SIMPLIFIED APPROACH:
   - Use individual file operations instead of filesystem formatting
   - Let MicroPython handle filesystem management automatically
   - Avoid complex filesystem manipulation that causes timeouts

2. RELIABLE CONNECTION:
   - Use `mpremote connect auto` for auto-detection
   - Minimal delays between operations (not excessive 2-second waits)
   - Proper error handling without overcomplicating retry logic

3. INCREMENTAL DEPLOYMENT:
   - Only remove/deploy files that actually exist
   - Skip missing files gracefully
   - Allow partial deployments to continue

4. MODERN FILE MANAGEMENT:
   - Use mpremote's built-in file operations
   - Leverage auto soft-reset functionality
   - Simple and clean error reporting

Usage:
  python deploy.py              # Deploy all files
  python deploy.py --clean      # Remove all files first, then deploy
  python deploy.py --retry      # Retry failed files only
  python deploy.py COM3         # Use specific port
"""

import subprocess
import sys
import os
import time
from pathlib import Path

# Files to deploy
FILES = [
    "lib/st7789py.py",  # Display driver
    "lib/vga1_8x8.py",  # 8x8 font for display
    "boot.py",
    "main.py",
    "config.py",
    "secrets.py",  # Your private credentials
    "wifi_manager.py",
    "purple_air.py",
    "ventilation.py",
    "ui_manager.py",  # New unified UI manager
    "google_logger.py",
]

def find_port():
    """Try to find the ESP32 port automatically"""
    # Use mpremote's auto-detection - it's more reliable than manual detection
    return "auto"

def run_mpremote_cmd(cmd_parts, timeout=10, retries=2):
    """Run an mpremote command with proper error handling"""
    for attempt in range(retries + 1):
        try:
            if attempt > 0:
                print(f"  Retry {attempt}/{retries}...")
                time.sleep(0.5)  # Brief pause between retries
            
            result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                return True, result
            else:
                # Check for common recoverable errors
                stderr_text = str(result.stderr) if hasattr(result, 'stderr') and result.stderr else ""
                if "could not enter raw repl" in stderr_text or "timeout" in stderr_text.lower():
                    if attempt < retries:
                        continue
                return False, result
                
        except subprocess.TimeoutExpired as e:
            if attempt < retries:
                print(f"  Timeout, retrying...")
                continue
            return False, e
        except Exception as e:
            return False, e
    
    return False, None

def clean_board(port):
    """Remove all Python files from the board (optional clean start)"""
    print("\nCleaning board (removing Python files)...")
    
    # Get list of files
    success, result = run_mpremote_cmd(["mpremote", "connect", port, "ls"], timeout=5)
    if not success:
        print("  Warning: Could not list files, continuing anyway")
        return True
    
    # Parse file list and remove .py files and directories we know about
    files_to_remove = []
    try:
        if success and result and hasattr(result, 'stdout') and result.stdout:
            stdout_content = str(result.stdout)
            lines = stdout_content.strip().split('\n')
            
            for line in lines:
                line_str = line.strip()
                if line_str.endswith('.py') or line_str in ['lib/', 'lib']:
                    files_to_remove.append(line_str.rstrip('/'))
    except Exception:
        # If parsing fails, just continue
        pass
    
    # Remove files
    removed_count = 0
    for file_path in files_to_remove:
        print(f"  Removing {file_path}...")
        if file_path == 'lib':
            # Remove lib directory
            success, _ = run_mpremote_cmd(["mpremote", "connect", port, "rmdir", "lib"], timeout=5, retries=1)
        else:
            # Remove file
            success, _ = run_mpremote_cmd(["mpremote", "connect", port, "rm", file_path], timeout=5, retries=1)
        
        if success:
            removed_count += 1
        # Continue even if some files fail to remove
    
    print(f"  Removed {removed_count} files/directories")
    return True

def deploy_files(port, files_to_deploy=None):
    """Deploy files to the board"""
    if files_to_deploy is None:
        files_to_deploy = [f for f in FILES if Path(f).exists()]
    
    if not files_to_deploy:
        print("No files to deploy!")
        return True, []
    
    print(f"\nDeploying {len(files_to_deploy)} files to {port}...")
    
    # Ensure lib directory exists for lib files
    lib_files = [f for f in files_to_deploy if f.startswith('lib/')]
    if lib_files:
        print("  Creating lib directory...")
        run_mpremote_cmd(["mpremote", "connect", port, "mkdir", "lib"], timeout=5, retries=1)
    
    failed_files = []
    deployed_count = 0
    
    for i, file_path in enumerate(files_to_deploy, 1):
        if not Path(file_path).exists():
            print(f"  [{i}/{len(files_to_deploy)}] {file_path} - NOT FOUND, skipping")
            continue
        
        print(f"  [{i}/{len(files_to_deploy)}] {file_path} ", end='', flush=True)
        
        # Determine target path
        if file_path.startswith('lib/'):
            target = f":{file_path}"  # Keep lib/ structure
        else:
            target = f":{Path(file_path).name}"  # Root directory
        
        # Copy file with adaptive timeout based on file size
        try:
            file_size_kb = Path(file_path).stat().st_size / 1024
            # Adaptive timeout: 15s base + 2s per KB for files over 10KB
            if file_size_kb > 10:
                timeout = 15 + int((file_size_kb - 10) * 2)
                timeout = min(timeout, 120)  # Cap at 2 minutes
            else:
                timeout = 15
        except:
            timeout = 15  # Fallback if file size check fails
            
        cmd = ["mpremote", "connect", port, "cp", file_path, target]
        success, result = run_mpremote_cmd(cmd, timeout=timeout, retries=2)
        
        if success:
            print("✓")
            deployed_count += 1
        else:
            print("✗")
            failed_files.append(file_path)
            try:
                if result and hasattr(result, 'stderr') and result.stderr:
                    stderr_content = str(result.stderr)
                    print(f"    Error: {stderr_content.strip()}")
            except Exception:
                pass
    
    print(f"\nDeployment complete: {deployed_count}/{len(files_to_deploy)} files deployed")
    
    if failed_files:
        print(f"Failed files: {', '.join(failed_files)}")
        return False, failed_files
    else:
        return True, []

def soft_reset_board(port):
    """Perform a soft reset of the board"""
    print("\nPerforming soft reset...")
    success, _ = run_mpremote_cmd(["mpremote", "connect", port, "soft-reset"], timeout=5, retries=1)
    if success:
        print("  Board reset successfully")
    else:
        print("  Warning: Reset may have failed, but this is often normal")

def main():
    """Main deployment function"""
    # Parse command line arguments
    clean_first = "--clean" in sys.argv
    retry_mode = "--retry" in sys.argv
    list_files = "--list" in sys.argv
    
    # Get port (default to auto)
    port = "auto"
    for arg in sys.argv[1:]:
        if not arg.startswith("--") and arg not in ["--clean", "--retry", "--list"]:
            port = arg
            break
    
    print(f"ESP32 MicroPython Deployment Tool")
    print(f"Port: {port}")
    
    # Handle retry mode
    if retry_mode:
        failed_files_path = Path(".failed_files.txt")
        if failed_files_path.exists():
            print("Retrying failed files from previous deployment...")
            with open(failed_files_path, "r") as f:
                files_to_deploy = [line.strip() for line in f.readlines() if line.strip()]
        else:
            print("No failed files found to retry.")
            return 0
    else:
        files_to_deploy = None
    
    # List files mode
    if list_files:
        print("\nFiles on board:")
        success, result = run_mpremote_cmd(["mpremote", "connect", port, "ls"], timeout=10)
        try:
            if success and result and hasattr(result, 'stdout') and result.stdout:
                stdout_content = str(result.stdout)
                for line in stdout_content.strip().split('\n'):
                    print(f"  {line}")
            else:
                print("  Could not list files")
        except Exception:
            print("  Could not list files")
        return 0
    
    # Check if we have required files
    if not retry_mode:
        missing = [f for f in FILES if not Path(f).exists() and f not in ["secrets.py"]]
        if missing:
            print(f"\nMissing files: {', '.join(missing)}")
            print("Make sure all project files are in the current directory.")
            return 1
    
    # Test connection
    print(f"\nTesting connection to {port}...")
    success, result = run_mpremote_cmd(["mpremote", "connect", port, "exec", "print('Connection OK')"], timeout=5)
    if not success:
        print("  Failed to connect to board!")
        print("  Make sure the board is connected and the port is correct.")
        try:
            if result and hasattr(result, 'stderr') and result.stderr:
                stderr_content = str(result.stderr)
                print(f"  Error: {stderr_content}")
        except Exception:
            pass
        return 1
    print("  Connection successful")
    
    # Clean board if requested
    if clean_first and not retry_mode:
        clean_board(port)
    
    # Deploy files
    success, failed_files = deploy_files(port, files_to_deploy)
    
    # Handle failed files
    failed_files_path = Path(".failed_files.txt")
    if failed_files:
        with open(failed_files_path, "w") as f:
            f.write("\n".join(failed_files))
        print(f"\nTo retry failed files: python {sys.argv[0]} --retry")
    else:
        # Clean up failed files list if all succeeded
        if failed_files_path.exists():
            failed_files_path.unlink()
    
    # Reset board
    if success or (failed_files and len(failed_files) < len(FILES)):
        soft_reset_board(port)
    
    if success:
        print(f"\n✓ Deployment successful!")
        print(f"To monitor output: mpremote connect {port} repl")
        return 0
    else:
        print(f"\n✗ Deployment failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())