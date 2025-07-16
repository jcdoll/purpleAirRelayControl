# Connection retry utilities for ESP32 MicroPython
# Common retry patterns for network operations

import time

def retry_operation(func, max_attempts=3, delay_ms=500, context="operation", *args, **kwargs):
    """
    Retry an operation with exponential backoff
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts  
        delay_ms: Initial delay in milliseconds
        context: Description for error messages
        *args, **kwargs: Arguments for the function
    Returns:
        Function result on success, None on failure
    """
    for attempt in range(max_attempts):
        try:
            if attempt > 0:
                print(f"  Retry {attempt}/{max_attempts-1} for {context}...")
                time.sleep_ms(delay_ms * (2 ** (attempt - 1)))  # Exponential backoff
            
            result = func(*args, **kwargs)
            if attempt > 0:
                print(f"  {context} succeeded on retry {attempt}")
            return result
            
        except Exception as e:
            if attempt == max_attempts - 1:
                print(f"  {context} failed after {max_attempts} attempts: {e}")
                return None
            else:
                print(f"  {context} attempt {attempt + 1} failed: {e}")
    
    return None

def retry_with_timeout(func, timeout_sec=10, max_attempts=3, context="operation", *args, **kwargs):
    """
    Retry an operation with both timeout and retry logic
    Args:
        func: Function to retry
        timeout_sec: Timeout for each attempt in seconds
        max_attempts: Maximum number of attempts
        context: Description for error messages  
        *args, **kwargs: Arguments for the function
    Returns:
        Function result on success, None on failure
    """
    for attempt in range(max_attempts):
        try:
            if attempt > 0:
                print(f"  Timeout retry {attempt}/{max_attempts-1} for {context}...")
                time.sleep(1)  # Brief delay between timeout retries
            
            start_time = time.time()
            result = func(*args, **kwargs)
            
            # Simple timeout check (not perfect but works for many cases)
            if time.time() - start_time > timeout_sec:
                raise TimeoutError(f"{context} exceeded {timeout_sec}s timeout")
                
            return result
            
        except Exception as e:
            if attempt == max_attempts - 1:
                print(f"  {context} failed after {max_attempts} attempts: {e}")
                return None
            else:
                error_type = "timeout" if "timeout" in str(e).lower() else "error"
                print(f"  {context} {error_type} on attempt {attempt + 1}: {e}")
    
    return None

def wait_for_condition(check_func, timeout_sec=30, check_interval=0.5, context="condition"):
    """
    Wait for a condition to become true with timeout
    Args:
        check_func: Function that returns True when condition is met
        timeout_sec: Maximum time to wait in seconds
        check_interval: Time between checks in seconds
        context: Description for messages
    Returns:
        True if condition met, False if timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout_sec:
        try:
            if check_func():
                return True
        except Exception as e:
            print(f"  Error checking {context}: {e}")
        
        time.sleep(check_interval)
        
        # Show progress for long waits
        if int(time.time() - start_time) % 5 == 0:
            elapsed = int(time.time() - start_time)
            print(f"  Waiting for {context}... ({elapsed}s elapsed)")
    
    print(f"  Timeout waiting for {context} after {timeout_sec}s")
    return False

def check_connection_quality(get_signal_func, min_signal=-70, context="connection"):
    """
    Check if connection quality is acceptable
    Args:
        get_signal_func: Function that returns signal strength (dBm)
        min_signal: Minimum acceptable signal strength in dBm
        context: Description for messages
    Returns:
        True if connection quality is good, False otherwise
    """
    try:
        signal = get_signal_func()
        if signal is None:
            print(f"  {context} signal strength unavailable")
            return False
            
        if signal >= min_signal:
            print(f"  {context} signal: {signal} dBm (good)")
            return True
        else:
            print(f"  {context} signal: {signal} dBm (weak, min: {min_signal} dBm)")
            return False
            
    except Exception as e:
        print(f"  Error checking {context} signal: {e}")
        return False

# Connection state management
class ConnectionState:
    """Track connection state and retry counts"""
    
    def __init__(self, name):
        self.name = name
        self.connected = False
        self.last_success = 0
        self.failure_count = 0
        self.total_attempts = 0
    
    def mark_success(self):
        """Mark a successful connection"""
        self.connected = True
        self.last_success = time.time()
        self.failure_count = 0
        self.total_attempts += 1
    
    def mark_failure(self):
        """Mark a failed connection attempt"""
        self.connected = False
        self.failure_count += 1
        self.total_attempts += 1
    
    def should_retry(self, max_failures=5):
        """Check if we should attempt retry based on failure history"""
        return self.failure_count < max_failures
    
    def get_status(self):
        """Get connection status summary"""
        return {
            'name': self.name,
            'connected': self.connected,
            'failure_count': self.failure_count,
            'total_attempts': self.total_attempts,
            'last_success': self.last_success
        } 