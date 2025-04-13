import keyboard
import time
from threading import Thread, Lock, Event
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Callable, Optional, Set

# Kiểu dữ liệu cho dễ đọc
ScanCode = int
BitIndex = int
HashKey = str
CallbackFunc = Callable[[], None]

class AdvancedListener:
    """
    Listens for keyboard events in a separate thread, allowing registration
    and execution of callbacks for specific hotkey combinations.

    Features:
        - Runs in a background daemon thread.
        - Thread-safe operations using Lock.
        - Flexible hotkey detection (handles intermediate key presses/releases).
        - Non-blocking callback execution using a ThreadPoolExecutor.
        - Methods to add and remove hotkeys dynamically.
        - Graceful shutdown mechanism.
    """
    def __init__(self, max_callback_workers: int = 4):
        """
        Initializes the listener.

        Args:
            max_callback_workers: The maximum number of threads to use for
                                  executing callbacks concurrently.
        """
        self._pressed_keys: Set[ScanCode] = set() # Sử dụng Set để kiểm tra/thêm/xóa O(1)
        self._hotkey_map: Dict[HashKey, CallbackFunc] = {}
        # Map ScanCode tới vị trí bit để tạo hash
        self._key_to_bit_index: Dict[ScanCode, BitIndex] = {}
        self._next_bit_index: BitIndex = 0

        self._lock = Lock() # Bảo vệ các cấu trúc dữ liệu chia sẻ
        self._stop_event = Event() # Dùng để yêu cầu dừng luồng

        # Executor để chạy callbacks không chặn luồng listener
        self._callback_executor = ThreadPoolExecutor(
            max_workers=max_callback_workers,
            thread_name_prefix='HotkeyCallback'
            )

        self._listener_thread = Thread(target=self._listen_loop, daemon=True)
        self._listener_thread.start()
        print("Listener thread started.")

    def _get_scan_code(self, key_name: str) -> Optional[ScanCode]:
        """Converts a key name to its primary scan code."""
        try:
            # key_to_scan_codes trả về tuple, luôn có ít nhất 1 phần tử nếu hợp lệ
            scan_codes = keyboard.key_to_scan_codes(key_name)
            print(f"Debug: Scan codes for '{key_name}': {scan_codes}") # Bỏ comment nếu cần debug
            return scan_codes[0] # Luôn lấy cái đầu tiên cho nhất quán
        except ValueError:
            print(f"Warning: Could not find scan code for key '{key_name}'.")
            return None
        except Exception as e:
            print(f"Error getting scan code for '{key_name}': {e}")
            return None

    def _calculate_hash(self, scan_codes: Set[ScanCode]) -> HashKey:
        """Calculates the hash key for a set of pressed scan codes."""
        current_hash = 0
        for code in scan_codes:
            if code in self._key_to_bit_index:
                current_hash |= (1 << self._key_to_bit_index[code])
        return hex(current_hash)

    def _listen_loop(self):
        """The main loop running in the listener thread."""
        print("Listener loop running...")
        while not self._stop_event.is_set():
            try:
                event = keyboard.read_event()

                # Bỏ qua nếu không có tên phím hoặc sự kiện không phải up/down
                if not event.name or event.event_type not in ('down', 'up'):
                    continue

                scan_code = self._get_scan_code(event.name.lower())
                if scan_code is None:
                    continue # Bỏ qua nếu không lấy được scan code

                callback_to_run: Optional[CallbackFunc] = None

                with self._lock:
                    is_relevant_key = scan_code in self._key_to_bit_index

                    if event.event_type == 'down':
                        # Chỉ thêm nếu là phím hợp lệ và chưa được nhấn
                        if is_relevant_key and scan_code not in self._pressed_keys:
                            self._pressed_keys.add(scan_code)
                            current_hash = self._calculate_hash(self._pressed_keys)
                            # print(f"Debug: Down {event.name}, Hash: {current_hash}, Pressed: {self._pressed_keys}")
                            if current_hash in self._hotkey_map:
                                callback_to_run = self._hotkey_map[current_hash]
                        # Không làm gì nếu phím đã được nhấn hoặc không liên quan

                    elif event.event_type == 'up':
                        # Chỉ xóa nếu phím này đang được nhấn
                        if scan_code in self._pressed_keys:
                            self._pressed_keys.discard(scan_code)
                            # print(f"Debug: Up   {event.name}, Pressed: {self._pressed_keys}")
                        # Không làm gì nếu phím không được nhấn

                # Thực thi callback bên ngoài lock để không chặn listener
                if callback_to_run:
                    print(f"Hotkey detected, submitting callback...")
                    try:
                        # Chạy callback trong một luồng khác
                        self._callback_executor.submit(callback_to_run)
                    except Exception as e:
                        print(f"Error submitting callback to executor: {e}")

            except ImportError:
                 print("Listener loop stopped: Keyboard library potentially unloaded.")
                 break # Thoát vòng lặp nếu thư viện keyboard không dùng được nữa
            except Exception as e:
                if not self._stop_event.is_set(): # Chỉ in lỗi nếu không phải do đang dừng
                    print(f"Error in listener loop: {e}")
                    # Ngủ một chút để tránh vòng lặp lỗi quá nhanh
                    time.sleep(0.05)

        print("Listener loop finished.")
        # Dọn dẹp executor khi luồng kết thúc
        self._callback_executor.shutdown(wait=False, cancel_futures=True)
        print("Callback executor shutdown.")


    def add_hotkey(self, hotkey_str: str, callback: CallbackFunc) -> bool:
        """
        Registers a hotkey combination and its callback function.

        Args:
            hotkey_str: The hotkey string (e.g., "ctrl+shift+a").
            callback: The function to call when the hotkey is pressed.

        Returns:
            True if the hotkey was added successfully, False otherwise.
        """
        key_names = [key.strip().lower() for key in hotkey_str.split('+') if key.strip()]
        if not key_names:
            print("Error: Hotkey string cannot be empty.")
            return False

        scan_codes_for_hotkey: Set[ScanCode] = set()
        success = True

        with self._lock:
            for name in key_names:
                scan_code = self._get_scan_code(name)
                if scan_code is None:
                    print(f"Error: Could not register hotkey '{hotkey_str}' due to invalid key '{name}'.")
                    success = False
                    break # Dừng xử lý hotkey này nếu có phím không hợp lệ

                scan_codes_for_hotkey.add(scan_code)

                # Gán chỉ số bit nếu phím này chưa có
                if scan_code not in self._key_to_bit_index:
                    self._key_to_bit_index[scan_code] = self._next_bit_index
                    self._next_bit_index += 1
                    # Kiểm tra tràn bit nếu cần (ví dụ > 64 phím)
                    if self._next_bit_index >= 64:
                         print("Warning: Approaching maximum number of unique keys for hashing (64).")


            if success:
                target_hash = self._calculate_hash(scan_codes_for_hotkey)
                if target_hash in self._hotkey_map:
                    print(f"Warning: Overwriting existing callback for hotkey '{hotkey_str}' (Hash: {target_hash}).")
                self._hotkey_map[target_hash] = callback
                print(f"Successfully added hotkey '{hotkey_str}' (Hash: {target_hash})")

        return success

    def remove_hotkey(self, hotkey_str: str) -> bool:
        """
        Unregisters a hotkey combination.

        Args:
            hotkey_str: The hotkey string to remove (e.g., "ctrl+shift+a").

        Returns:
            True if the hotkey was found and removed, False otherwise.
        """
        key_names = [key.strip().lower() for key in hotkey_str.split('+') if key.strip()]
        if not key_names:
            print("Error: Hotkey string cannot be empty for removal.")
            return False

        scan_codes_for_hotkey: Set[ScanCode] = set()
        possible = True
        with self._lock:
            # Chỉ cần lấy scan code, không cần thêm vào _key_to_bit_index
            for name in key_names:
                scan_code = self._get_scan_code(name)
                # Quan trọng: Phím phải tồn tại trong _key_to_bit_index thì mới có khả năng hotkey tồn tại
                if scan_code is None or scan_code not in self._key_to_bit_index:
                    possible = False
                    break
                scan_codes_for_hotkey.add(scan_code)

            if not possible:
                 print(f"Info: Hotkey '{hotkey_str}' cannot exist (contains unknown/unused keys), skipping removal.")
                 return False # Không thể tồn tại nên coi như không xóa được

            target_hash = self._calculate_hash(scan_codes_for_hotkey)

            if target_hash in self._hotkey_map:
                del self._hotkey_map[target_hash]
                print(f"Successfully removed hotkey '{hotkey_str}' (Hash: {target_hash}).")
                # Lưu ý: Không xóa key khỏi _key_to_bit_index vì nó có thể đang được dùng bởi hotkey khác
                return True
            else:
                print(f"Info: Hotkey '{hotkey_str}' (Hash: {target_hash}) not found for removal.")
                return False

    def stop(self, wait: bool = True):
        """
        Signals the listener thread to stop and cleans up resources.

        Args:
            wait: If True, waits for the listener thread to finish.
        """
        if not self._stop_event.is_set():
            print("Stopping listener...")
            self._stop_event.set()

            # Có thể cần gửi một sự kiện phím giả để đánh thức read_event nếu nó đang block
            # Tuy nhiên, việc này phức tạp và phụ thuộc nền tảng.
            # Cách đơn giản hơn là chờ đợi hoặc dựa vào daemon thread tự thoát.

            if wait and self._listener_thread.is_alive():
                print("Waiting for listener thread to finish...")
                # Không join vô thời hạn, đặt timeout hợp lý
                self._listener_thread.join(timeout=1.0)
                if self._listener_thread.is_alive():
                     print("Warning: Listener thread did not finish within timeout.")

            # Shutdown executor (đã có trong _listen_loop nhưng gọi lại ở đây cho chắc)
            # wait=False để không chặn hàm stop quá lâu
            self._callback_executor.shutdown(wait=False, cancel_futures=True)
            print("Listener stopped.")
        else:
            print("Listener already stopped.")

    # Có thể thêm __del__ để cố gắng stop khi đối tượng bị hủy, nhưng không đảm bảo
    def __del__(self):
       print("Listener object deleted, attempting to stop...")
       self.stop(wait=False)

# --- Ví dụ sử dụng ---
if __name__ == "__main__":
    listener = AdvancedListener()

    def action_1():
        print("Action 1: Ctrl+Alt+P triggered!")
        time.sleep(3) # Giả lập công việc tốn thời gian
        print("Action 1 finished.")

    def action_2():
        print("Action 2: Shift+Q triggered!")

    def exit_action():
        print("Exit hotkey triggered! Stopping listener...")
        listener.stop() # Dừng listener từ chính callback

    listener.add_hotkey("ctrl+alt+p", action_1)
    listener.add_hotkey("shift+q", action_2)
    listener.add_hotkey("ctrl+shift+x", exit_action) # Hotkey để thoát

    print("Listener setup complete. Press Ctrl+Alt+P, Shift+Q, or Ctrl+Shift+X.")
    print("(Listener runs in background, this script will wait until listener stops)")

    # Giữ chương trình chính chạy trong khi listener hoạt động
    # Chờ cho đến khi luồng listener thực sự kết thúc (ví dụ, do gọi stop())
    while listener._listener_thread.is_alive():
         try:
             time.sleep(0.5)
         except KeyboardInterrupt: # Cho phép dừng bằng Ctrl+C từ terminal
             print("\nCtrl+C detected, stopping listener...")
             listener.stop()
             break

    print("Main script finished.")