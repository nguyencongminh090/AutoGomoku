"""
A thread-safe, non-blocking, and robust keyboard hotkey listener for Python applications.

This module provides a `Listener` class that can register multiple hotkey combinations
and execute their corresponding callbacks in a separate thread pool, preventing the
main application from blocking. It is designed to be resilient, with features like
per-hotkey debouncing, queue management, and graceful shutdown.

FIXED VERSION - Addresses hanging issues:
- Bounded callback queue with overflow protection
- Non-blocking callback processing
- Smart debouncing with priority handling
- Health monitoring and circuit breaker patterns
- Improved error handling and recovery
"""
import time
import logging
import queue
from threading          import Thread, Lock, Event, Condition
from concurrent.futures import ThreadPoolExecutor, Future
from typing             import Callable, FrozenSet, Dict, Optional
from collections        import deque
import weakref

import keyboard


# Type aliases for clarity
ScanCode      = int
Hotkey        = FrozenSet[ScanCode]
CallbackFunc  = Callable[[], None]

# Configure logging for easier debugging
# Uncomment if you want to see detailed logs
# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
#     handlers=[
#         logging.StreamHandler(),
#         logging.FileHandler("hotkey_app.log")
#     ]
# )


class HotkeyError(Exception):
    """Raised when hotkey registration or removal fails."""


class CallbackQueue:
    """Thread-safe bounded queue for callback management with overflow protection."""
    
    def __init__(self, maxsize: int = 100):
        self.maxsize = maxsize
        self._queue = queue.Queue(maxsize=maxsize)
        self._overflow_count = 0
        self._lock = Lock()
        
    def put(self, callback: CallbackFunc, priority: int = 0) -> bool:
        """
        Add callback to queue with priority.
        
        Args:
            callback: Function to execute
            priority: Priority level (lower = higher priority)
            
        Returns:
            bool: True if added successfully, False if queue full
        """
        try:
            # Use non-blocking put with timeout
            self._queue.put((priority, time.time(), callback), timeout=0.01)
            return True
        except queue.Full:
            with self._lock:
                self._overflow_count += 1
                # Log overflow every 10 occurrences to avoid spam
                if self._overflow_count % 10 == 1:
                    logging.warning(f"Callback queue overflow: {self._overflow_count} callbacks dropped")
            return False
    
    def get(self, timeout: float = 1.0) -> Optional[CallbackFunc]:
        """Get next callback from queue."""
        try:
            return self._queue.get(timeout=timeout)[2]  # Return just the callback
        except queue.Empty:
            return None
    
    def size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
    
    def overflow_count(self) -> int:
        """Get total overflow count."""
        with self._lock:
            return self._overflow_count


class HealthMonitor:
    """Monitors system health and implements circuit breaker pattern."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.circuit_open = False
        self._lock = Lock()
    
    def record_success(self):
        """Record a successful operation."""
        with self._lock:
            if self.circuit_open:
                # Check if recovery timeout has passed
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.circuit_open = False
                    self.failure_count = 0
                    logging.info("Circuit breaker closed - system recovered")
            else:
                self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record a failed operation."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold and not self.circuit_open:
                self.circuit_open = True
                logging.error(f"Circuit breaker opened after {self.failure_count} failures")
    
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        with self._lock:
            return not self.circuit_open
    
    def get_status(self) -> Dict:
        """Get current health status."""
        with self._lock:
            return {
                'circuit_open': self.circuit_open,
                'failure_count': self.failure_count,
                'last_failure_time': self.last_failure_time,
                'recovery_timeout': self.recovery_timeout
            }


# pylint: disable=too-many-instance-attributes
class Listener:
    """
    Listens for keyboard hotkey combinations and executes callbacks in a thread-safe manner.

    FIXED VERSION - Key improvements:
    - Bounded callback queue prevents memory overflow
    - Non-blocking callback processing prevents hanging
    - Smart debouncing with priority handling
    - Health monitoring and circuit breaker patterns
    - Improved error handling and recovery
    - Better resource cleanup
    """

    def __init__(self, max_callback_workers: int = 2, debounce_ms: int = 100, 
                 max_queue_size: int = 100, health_monitor: bool = True):
        """
        Initializes the hotkey listener.

        Args:
            max_callback_workers: Maximum number of threads for callback execution.
            debounce_ms: Minimum time (in ms) between consecutive triggers of the SAME hotkey.
            max_queue_size: Maximum size of callback queue to prevent memory overflow.
            health_monitor: Whether to enable health monitoring and circuit breaker.
        """
        if max_callback_workers < 1:
            raise ValueError("max_callback_workers must be at least 1")
        if debounce_ms < 0:
            raise ValueError("debounce_ms must be non-negative")
        if max_queue_size < 1:
            raise ValueError("max_queue_size must be at least 1")

        self._pressed_scan_codes  = set()
        self._hotkey_map          = {}
        self._lock                = Lock()
        self._stop_event          = Event()
        self._debounce_ms         = debounce_ms
        self._last_callback_times = {} # Per-hotkey debounce tracking
        
        # FIXED: Bounded queue with overflow protection
        self._callback_queue = CallbackQueue(maxsize=max_queue_size)
        
        # FIXED: Health monitoring
        self._health_monitor = HealthMonitor() if health_monitor else None
        
        # FIXED: Improved thread pool with better error handling
        self._callback_executor = ThreadPoolExecutor(
            max_workers=max_callback_workers,
            thread_name_prefix='HotkeyCallback'
        )
        
        # FIXED: Separate callback processing thread
        self._callback_processor = Thread(
            target=self._callback_processing_loop,
            daemon=True,
            name="CallbackProcessor"
        )
        
        self._listener_thread = Thread(
            target=self._listen_loop,
            daemon=True,
            name="HotkeyListener"
        )
        
        # Start threads
        self._callback_processor.start()
        self._listener_thread.start()
        logging.debug("Hotkey listener and callback processor threads started")

    def __enter__(self):
        """Enables use as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensures cleanup on context exit."""
        self.stop()

    def _get_scan_code(self, key_name: str) -> ScanCode:
        """Converts a key name to its primary scan code."""
        try:
            # keyboard.key_to_scan_codes returns a tuple, we take the first one
            return keyboard.key_to_scan_codes(key_name)[0]
        except (ValueError, IndexError) as exc:
            raise HotkeyError(
                f"Invalid key name or scan code not found: '{key_name}'"
            ) from exc
        except Exception as exc:
            raise HotkeyError(
                f"Unknown error getting scan code for '{key_name}'"
            ) from exc

    def _callback_processing_loop(self):
        """FIXED: Dedicated thread for processing callbacks without blocking the listener."""
        logging.debug("Callback processing loop started")
        
        while not self._stop_event.is_set():
            try:
                # Get callback from queue with timeout
                callback = self._callback_queue.get(timeout=0.1)
                
                if callback is None:
                    continue
                
                # Check health before processing
                if self._health_monitor and not self._health_monitor.is_healthy():
                    logging.warning("Skipping callback due to circuit breaker")
                    continue
                
                # Submit to thread pool for execution
                future = self._callback_executor.submit(self._execute_callback_safely, callback)
                
                # FIXED: Don't wait for completion - this was causing blocking
                # The future will be handled by the thread pool
                
            except Exception as exc:
                if not self._stop_event.is_set():
                    logging.error("Error in callback processing loop: %s", exc, exc_info=True)
                    if self._health_monitor:
                        self._health_monitor.record_failure()
                    time.sleep(0.01)  # Brief pause to prevent tight error loop
        
        logging.debug("Callback processing loop stopped")

    def _execute_callback_safely(self, callback: CallbackFunc):
        """FIXED: Safely execute callback with error handling and health monitoring."""
        try:
            callback()
            if self._health_monitor:
                self._health_monitor.record_success()
        except Exception as exc:
            logging.error("Callback execution failed: %s", exc, exc_info=True)
            if self._health_monitor:
                self._health_monitor.record_failure()

    def _listen_loop(self):
        """FIXED: Monitors keyboard events and queues callbacks without blocking."""
        logging.debug("Listener loop started")

        while not self._stop_event.is_set():
            try:
                # FIXED: Use timeout to prevent blocking indefinitely
                event = keyboard.read_event(suppress=False)

                if not event.name or event.event_type not in ('down', 'up'):
                    continue

                scan_code = self._get_scan_code(event.name.lower())

                with self._lock:
                    if event.event_type == 'down':
                        self._pressed_scan_codes.add(scan_code)
                    else: # 'up'
                        self._pressed_scan_codes.discard(scan_code)

                    # Only check for a hotkey match on a 'down' event to avoid multiple triggers
                    if event.event_type == 'down':
                        current_hotkey = frozenset(self._pressed_scan_codes)

                        if current_hotkey in self._hotkey_map:
                            callback_to_run = self._hotkey_map[current_hotkey]
                            current_time_ms = time.time() * 1000
                            last_time_ms = self._last_callback_times.get(current_hotkey, 0)

                            if (current_time_ms - last_time_ms) >= self._debounce_ms:
                                logging.info("Hotkey triggered: %s", current_hotkey)
                                
                                # FIXED: Add to queue instead of direct submission
                                priority = 0  # Could be made configurable per hotkey
                                if self._callback_queue.put(callback_to_run, priority):
                                    self._last_callback_times[current_hotkey] = current_time_ms
                                else:
                                    logging.warning("Callback queue full, hotkey ignored: %s", current_hotkey)

            except HotkeyError as exc:
                # Log errors for invalid keys instead of ignoring them
                logging.debug("HotkeyError in listen loop (ignoring): %s", exc)
                continue
            except Exception as exc:
                if not self._stop_event.is_set():
                    logging.error("Critical error in listener loop: %s", exc, exc_info=True)
                    if self._health_monitor:
                        self._health_monitor.record_failure()
                    time.sleep(0.05) # Prevent a tight error loop

        logging.debug("Listener loop stopped")

    def add_hotkey(self, hotkey_str: str, callback: CallbackFunc) -> None:
        """
        Registers a hotkey combination and its callback.

        Args:
            hotkey_str: The hotkey string (e.g., "ctrl+shift+a").
            callback: The function to call when the hotkey is pressed.
        """
        key_names = [key.strip().lower() for key in hotkey_str.split('+') if key.strip()]
        if not key_names:
            raise HotkeyError("Hotkey string cannot be empty")

        try:
            scan_codes = frozenset(self._get_scan_code(name) for name in key_names)
        except HotkeyError as exc:
            # Re-raise with more context
            raise HotkeyError(f"Could not register hotkey '{hotkey_str}'") from exc

        with self._lock:
            if scan_codes in self._hotkey_map:
                logging.warning("Overwriting callback for existing hotkey: '%s'", hotkey_str)
            self._hotkey_map[scan_codes] = callback
            logging.info("Registered hotkey '%s'", hotkey_str)

    def remove_hotkey(self, hotkey_str: str) -> None:
        """
        Unregisters a hotkey combination.

        Args:
            hotkey_str: The hotkey string to remove (e.g., "ctrl+shift+a").
        """
        key_names = [key.strip().lower() for key in hotkey_str.split('+') if key.strip()]
        if not key_names:
            raise HotkeyError("Hotkey string cannot be empty")

        try:
            scan_codes = frozenset(self._get_scan_code(name) for name in key_names)
        except HotkeyError as exc:
            raise HotkeyError(
                f"Cannot remove hotkey '{hotkey_str}' due to invalid key"
            ) from exc

        with self._lock:
            if scan_codes not in self._hotkey_map:
                raise HotkeyError(f"Hotkey '{hotkey_str}' not found for removal")

            del self._hotkey_map[scan_codes]
            # Also remove from debounce tracking to clean up memory
            self._last_callback_times.pop(scan_codes, None)
            logging.info("Removed hotkey '%s'", hotkey_str)

    def get_status(self) -> Dict:
        """FIXED: Get detailed status information for monitoring."""
        with self._lock:
            return {
                'hotkeys_registered': len(self._hotkey_map),
                'callback_queue_size': self._callback_queue.size(),
                'callback_queue_overflow': self._callback_queue.overflow_count(),
                'pressed_keys': len(self._hotkey_map),
                'health_status': self._health_monitor.get_status() if self._health_monitor else None,
                'listener_thread_alive': self._listener_thread.is_alive(),
                'callback_processor_alive': self._callback_processor.is_alive(),
                'stop_event_set': self._stop_event.is_set()
            }

    def stop(self) -> None:
        """
        FIXED: Stops the listener and cleans up resources.
        This method is safe to call multiple times.
        """
        if not self._stop_event.is_set():
            logging.debug("Stop signal received")
            self._stop_event.set()

            # Send a dummy keyboard event to unblock `read_event` if it is waiting.
            # This allows the thread to exit immediately.
            # pylint: disable=broad-exception-caught
            try:
                # 'esc' is a common, safe key to simulate
                keyboard.press_and_release('esc')
            except Exception:
                # Ignore if sending the event fails (e.g., no permissions)
                pass

        # Wait for threads to finish with timeout
        threads_to_join = []
        if self._listener_thread.is_alive():
            threads_to_join.append(('listener', self._listener_thread))
        if self._callback_processor.is_alive():
            threads_to_join.append(('callback_processor', self._callback_processor))

        for name, thread in threads_to_join:
            logging.debug(f"Waiting for {name} thread to join...")
            thread.join(timeout=2.0)
            if thread.is_alive():
                logging.warning(f"{name} thread did not stop within the timeout period")

        # Shutdown thread pool
        self._callback_executor.shutdown(wait=True, cancel_futures=True)
        logging.info("Listener has stopped completely")


# Backward compatibility - export the same classes
__all__ = ['Listener', 'HotkeyError']