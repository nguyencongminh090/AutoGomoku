import keyboard
import time
from threading import Thread, Lock, Event
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Set, Callable, Optional
import logging

# Type aliases for clarity
ScanCode = int
BitIndex = int
HashKey = str
CallbackFunc = Callable[[], None]

class HotkeyError(Exception):
    """Raised when hotkey registration or removal fails."""
    pass

class AdvancedListener:
    """
    Listens for keyboard hotkey combinations and executes callbacks in a thread-safe manner.

    Features:
        - Background thread for non-blocking key event monitoring.
        - Thread-safe hotkey registration and removal.
        - Optional non-blocking callback execution via a thread pool.
        - Graceful shutdown and resource cleanup.
        - Context manager support for RAII-style usage.
    """
    def __init__(self, max_callback_workers: int = 1, debounce_ms: int = 500, use_executor: bool = True):
        """
        Initialize the hotkey listener.

        Args:
            max_callback_workers: Maximum number of threads for callback execution.
            debounce_ms: Minimum time (ms) between consecutive callback triggers.
            use_executor: If True, run callbacks in a thread pool; else, run in listener thread.

        Raises:
            ValueError: If max_callback_workers or debounce_ms is invalid.
        """
        if max_callback_workers < 1:
            raise ValueError("max_callback_workers must be at least 1")
        if debounce_ms < 0:
            raise ValueError("debounce_ms must be non-negative")

        self._pressed_keys: Set[ScanCode] = set()
        self._hotkey_map: Dict[HashKey, CallbackFunc] = {}
        self._key_to_bit_index: Dict[ScanCode, BitIndex] = {}
        self._available_bit_indices: Set[BitIndex] = set(range(64))  # Limit to 64 bits
        self._lock = Lock()
        self._stop_event = Event()
        self._last_callback_time = 0
        self._debounce_ms = debounce_ms
        self._use_executor = use_executor

        if use_executor:
            self._callback_executor = ThreadPoolExecutor(
                max_workers=max_callback_workers,
                thread_name_prefix='HotkeyCallback'
            )

        self._listener_thread = Thread(target=self._listen_loop, daemon=True)
        self._listener_thread.start()
        logging.debug("Hotkey listener thread started")

    def __enter__(self):
        """Enable context manager usage."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure cleanup on context exit."""
        self.stop()

    def _get_scan_code(self, key_name: str) -> ScanCode:
        """
        Convert a key name to its primary scan code.

        Args:
            key_name: The key name (e.g., 'ctrl', 'left ctrl').

        Returns:
            The primary scan code.

        Raises:
            HotkeyError: If the key name is invalid or has no scan code.
        """
        try:
            scan_codes = keyboard.key_to_scan_codes(key_name)
            if len(scan_codes) > 1:
                logging.debug(f"Multiple scan codes for '{key_name}': {scan_codes}, using {scan_codes[0]}")
            return scan_codes[0]
        except ValueError as e:
            raise HotkeyError(f"Invalid key name '{key_name}': {e}")
        except Exception as e:
            raise HotkeyError(f"Error resolving scan code for '{key_name}': {e}")

    def _calculate_hash(self, scan_codes: Set[ScanCode]) -> HashKey:
        """
        Calculate a hash for a set of scan codes.

        Args:
            scan_codes: Set of scan codes to hash.

        Returns:
            A hexadecimal string representing the hash.
        """
        current_hash = 0
        for code in scan_codes:
            if code in self._key_to_bit_index:
                current_hash |= (1 << self._key_to_bit_index[code])
        return hex(current_hash)

    def _listen_loop(self):
        """Monitor keyboard events and trigger callbacks for hotkey matches."""
        logging.debug("Listener loop started")
        while not self._stop_event.is_set():
            try:
                event = keyboard.read_event()
                if not event.name or event.event_type not in ('down', 'up'):
                    continue
                scan_code = self._get_scan_code(event.name.lower())
                callback_to_run: Optional[CallbackFunc] = None
                with self._lock:
                    is_relevant_key = scan_code in self._key_to_bit_index
                    if event.event_type == 'down' and is_relevant_key and scan_code not in self._pressed_keys:
                        self._pressed_keys.add(scan_code)
                        current_hash = self._calculate_hash(self._pressed_keys)
                        if current_hash in self._hotkey_map:
                            current_time = time.time() * 1000
                            if current_time - self._last_callback_time >= self._debounce_ms:
                                callback_to_run = self._hotkey_map[current_hash]
                                self._last_callback_time = current_time
                    elif event.event_type == 'up' and scan_code in self._pressed_keys:
                        self._pressed_keys.discard(scan_code)
                if callback_to_run:
                    logging.info(f"Hotkey triggered: hash={current_hash}")
                    if self._use_executor:
                        try:
                            self._callback_executor.submit(callback_to_run)
                        except RuntimeError:
                            logging.warning(f"Callback queue full, skipping hotkey: hash={current_hash}")
                    else:
                        try:
                            callback_to_run()
                        except Exception as e:
                            logging.error(f"Callback error: {e}")
            except HotkeyError:
                continue
            except Exception as e:
                if not self._stop_event.is_set():
                    logging.error(f"Listener loop error: {e}")
                    time.sleep(0.05)
        logging.debug("Listener loop stopped")
        if self._use_executor:
            self._callback_executor.shutdown(wait=False, cancel_futures=True)

    def add_hotkey(self, hotkey_str: str, callback: CallbackFunc) -> None:
        """
        Register a hotkey combination and its callback.

        Args:
            hotkey_str: Hotkey string (e.g., "ctrl+shift+a").
            callback: Function to call when the hotkey is pressed.

        Raises:
            HotkeyError: If the hotkey string is invalid or contains invalid keys.
        """
        key_names = [key.strip().lower() for key in hotkey_str.split('+') if key.strip()]
        if not key_names:
            raise HotkeyError("Hotkey string cannot be empty")
        scan_codes = set()
        with self._lock:
            for name in key_names:
                scan_code = self._get_scan_code(name)
                scan_codes.add(scan_code)
                if scan_code not in self._key_to_bit_index:
                    if not self._available_bit_indices:
                        raise HotkeyError("Maximum number of unique keys (64) reached")
                    bit_index = min(self._available_bit_indices)
                    self._available_bit_indices.remove(bit_index)
                    self._key_to_bit_index[scan_code] = bit_index
            target_hash = self._calculate_hash(scan_codes)
            if target_hash in self._hotkey_map:
                logging.warning(f"Overwriting callback for hotkey '{hotkey_str}' (hash={target_hash})")
            self._hotkey_map[target_hash] = callback
            logging.info(f"Registered hotkey '{hotkey_str}' (hash={target_hash})")

    def remove_hotkey(self, hotkey_str: str) -> None:
        """
        Unregister a hotkey combination.

        Args:
            hotkey_str: Hotkey string to remove (e.g., "ctrl+shift+a").

        Raises:
            HotkeyError: If the hotkey string is invalid or not registered.
        """
        key_names = [key.strip().lower() for key in hotkey_str.split('+') if key.strip()]
        if not key_names:
            raise HotkeyError("Hotkey string cannot be empty")
        scan_codes = set()
        with self._lock:
            for name in key_names:
                scan_codes.add(self._get_scan_code(name))
            target_hash = self._calculate_hash(scan_codes)
            if target_hash not in self._hotkey_map:
                raise HotkeyError(f"Hotkey '{hotkey_str}' (hash={target_hash}) not found")
            del self._hotkey_map[target_hash]
            logging.info(f"Removed hotkey '{hotkey_str}' (hash={target_hash})")

    def signal_stop(self) -> None:
        """
        Signal the listener to stop processing events and prepare for shutdown.
        Safe to call from callbacks.
        """
        with self._lock:
            if not self._stop_event.is_set():
                logging.debug("Stop signal received")
                self._stop_event.set()

    def stop(self) -> None:
        """
        Stop the listener and clean up resources.
        """
        self.signal_stop()
        if self._listener_thread.is_alive():
            logging.debug("Waiting for listener thread to stop")
            self._listener_thread.join(timeout=1.0)
            if self._listener_thread.is_alive():
                logging.warning("Listener thread did not stop within timeout")
        if self._use_executor:
            self._callback_executor.shutdown(wait=False, cancel_futures=True)
        logging.debug("Listener stopped")

    def __del__(self):
        """Attempt cleanup when the object is deleted."""
        self.stop()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("hotkey_app.log")
    ]
)

def main():
    """
    Simple application using AdvancedListener to handle hotkeys with minimal CPU usage.
    Simulates screen capture and board processing actions.
    """
    def start_capture():
        logging.info("Starting screen capture simulation")
        logging.info("Captured image (simulated)")

    def process_board():
        logging.info("Processing board simulation")
        time.sleep(0.5)  # Simulate heavy task
        logging.info("Processed 5 contour groups (simulated)")

    def exit_app():
        logging.info("Requesting application exit")
        listener.signal_stop()

    with AdvancedListener(max_callback_workers=1, debounce_ms=500, use_executor=False) as listener:
        try:
            listener.add_hotkey("ctrl+shift+s", start_capture)
            listener.add_hotkey("alt+p", process_board)
            listener.add_hotkey("ctrl+q", exit_app)
            logging.info("Hotkeys registered: Ctrl+Shift+S (capture), Alt+P (board), Ctrl+Q (exit)")
            while not listener._stop_event.is_set():
                time.sleep(0.1)
        except HotkeyError as e:
            logging.error(f"Hotkey setup failed: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise
        finally:
            logging.info("Application shutting down")

if __name__ == "__main__":
    main()