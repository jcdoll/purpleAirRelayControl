# Common error handling utilities for ESP32 MicroPython
# Standardizes error handling patterns used throughout the application

# Print full stack trace (MicroPython version)
import sys  # type: ignore


def print_exception(e, context=""):
    """
    Print exception details in standardized format
    Args:
        e: Exception object
        context: Optional context string to help identify where error occurred
    """
    error_msg = f"Error: {type(e).__name__}: {e}"
    if context:
        error_msg = f"{context} - {error_msg}"
    print(error_msg)

    sys.print_exception(e)  # type: ignore


def safe_execute(func, *args, context="", default_return=None, **kwargs):
    """
    Safely execute a function with standardized error handling
    Args:
        func: Function to execute
        *args: Positional arguments for function
        context: Context string for error reporting
        default_return: Value to return on error
        **kwargs: Keyword arguments for function
    Returns:
        Function result on success, default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print_exception(e, context)
        return default_return


def handle_network_error(e, operation="network operation"):
    """
    Handle network-specific errors with appropriate messaging
    Args:
        e: Exception object
        operation: Description of the network operation that failed
    """
    if "timeout" in str(e).lower():
        print(f"Network timeout during {operation}")
    elif "connection" in str(e).lower():
        print(f"Connection failed during {operation}")
    elif "host" in str(e).lower():
        print(f"Host unreachable during {operation}")
    else:
        print_exception(e, f"Network error during {operation}")


def handle_hardware_error(e, component="hardware component"):
    """
    Handle hardware-specific errors with appropriate messaging
    Args:
        e: Exception object
        component: Description of the hardware component that failed
    """
    if "pin" in str(e).lower():
        print(f"Pin configuration error with {component}")
    elif "i2c" in str(e).lower() or "spi" in str(e).lower():
        print(f"Communication error with {component}")
    else:
        print_exception(e, f"Hardware error with {component}")
