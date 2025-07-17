"""
A thread-safe, non-blocking, and robust keyboard hotkey listener for Python applications.

This module provides a `Listener` class that can register multiple hotkey combinations
and execute their corresponding callbacks in a separate thread pool, preventing the
main application from blocking. It is designed to be resilient, with features like
per-hotkey debouncing and graceful shutdown.
"""
import time
import logging
from threading          import Thread, Lock, Event
from concurrent.futures import ThreadPoolExecutor
from typing             import Callable, FrozenSet

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


# pylint: disable=too-many-instance-attributes
class Listener:
    """
    Listens for keyboard hotkey combinations and executes callbacks in a thread-safe manner.

    Features:
        - Background thread for non-blocking key event monitoring.
        - Thread-safe hotkey registration and removal.
        - Non-blocking callback execution via a thread pool.
        - Graceful shutdown and resource cleanup.
        - Context manager support for RAII-style usage.
    """

    def __init__(self, max_callback_workers: int = 1, debounce_ms: int = 500):
        """
        Initializes the hotkey listener.

        Args:
            max_callback_workers: Maximum number of threads for callback execution.
            debounce_ms: Minimum time (in ms) between consecutive triggers of the SAME hotkey.
        """
        if max_callback_workers < 1:
            raise ValueError("max_callback_workers must be at least 1")
        if debounce_ms < 0:
            raise ValueError("debounce_ms must be non-negative")

        self._pressed_scan_codes  = set()
        self._hotkey_map          = {}
        self._lock                = Lock()
        self._stop_event          = Event()
        self._debounce_ms         = debounce_ms
        self._last_callback_times = {} # Per-hotkey debounce tracking

        self._callback_executor   = ThreadPoolExecutor(
            max_workers           = max_callback_workers,
            thread_name_prefix    = 'HotkeyCallback'
        )
        self._listener_thread     = Thread(target=self._listen_loop,
                                           daemon=True,
                                           name="HotkeyListener")
        self._listener_thread.start()
        logging.debug("Hotkey listener thread has started")

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

    def _listen_loop(self):
        """Monitors keyboard events and triggers callbacks for hotkey matches."""
        logging.debug("Listener loop started")

        while not self._stop_event.is_set():
            try:
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
                                try:
                                    self._callback_executor.submit(callback_to_run)
                                    self._last_callback_times[current_hotkey] = current_time_ms
                                except RuntimeError:
                                    if not self._stop_event.is_set():
                                        logging.warning(
                                            "Callback queue is full, skipping hotkey: %s",
                                            current_hotkey
                                        )

            except HotkeyError as exc:
                # Log errors for invalid keys instead of ignoring them
                logging.debug("HotkeyError in listen loop (ignoring): %s", exc)
                continue
            except Exception as exc:
                if not self._stop_event.is_set():
                    logging.error("Critical error in listener loop: %s", exc, exc_info=True)
                    time.sleep(0.05) # Prevent a tight error loop

        logging.debug("Listener loop stopped")
        self._callback_executor.shutdown(wait=False, cancel_futures=True)

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

    def stop(self) -> None:
        """
        Stops the listener and cleans up resources.
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

        if self._listener_thread.is_alive():
            logging.debug("Waiting for listener thread to join...")
            self._listener_thread.join(timeout=1.0)
            if self._listener_thread.is_alive():
                logging.warning("Listener thread did not stop within the timeout period")

        # Shutdown is called here and at the end of the loop, which is safe.
        self._callback_executor.shutdown(wait=True, cancel_futures=True)
        logging.info("Listener has stopped completely")
