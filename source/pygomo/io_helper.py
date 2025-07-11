from queue     import Queue, Empty
from threading import Thread, Lock, Event
from typing    import TextIO, Callable, Dict


class StdoutReader:
    """Asynchronously reads and categorizes stdout from an engine process.

    Attributes:
        max_queue_size: Maximum number of messages per category queue.
    """

    def __init__(self, stream: TextIO):
        self._stream: StdoutReader     = stream
        self._queues: Dict[str, Queue] = {}
        self._filters                  = {}
        self._thread                   = Thread(target=self._populate_queue, daemon=True)
        self._stop_event               = Event()
        self._thread.daemon            = True
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1.0)

    def add_category(self, category: str, filter_func: Callable[[str], bool]) -> None:
        """Add a category with a filter function for output lines.

        Args:
            category: Name of the category.
            filter_func: Function to determine if a line belongs to the category.

        Raises:
            ValueError: If the category already exists.
        """
        if category in self._queues:
            raise ValueError(f"Category '{category}' already exists.")
        self._queues[category]  = Queue()
        self._filters[category] = filter_func

    def _populate_queue(self) -> None:
        """Read lines from the stream and distribute to category queues."""
        while not self._stop_event.is_set():
            line = self._stream.readline()
            if line == "":  # EOF
                break

            line = line.strip().lower()
            if not line:
                continue

            for category, filter_func in self._filters.items():
                if filter_func(line):
                    try:
                        self._queues[category].put(line)
                    except Exception:
                        break
                    break

    def get(self, category: str, timeout: float = 0.0, reset: bool = False) -> str:
        """Retrieve a line from a category queue.

        If reset is True, clears all but the most recent item and returns it.
        If reset is False, returns the next item in the queue.

        Args:
            category: Category to retrieve from.
            timeout: Maximum time to wait for a line (seconds).
            reset: If True, keep only the most recent item.

        Returns:
            The retrieved line, or empty string if none available.

        Raises:
            ValueError: If the category is invalid.
        """
        if category not in self._queues:
            valid_categories = ", ".join(self._queues.keys())
            raise ValueError(f"Unsupported category '{category}'. Valid options: {valid_categories}")

        queue = self._queues[category]

        if reset:
            items = []
            while not queue.empty():
                try:
                    items.append(queue.get_nowait())
                except Empty:
                    break
            
            if items:
                queue.put_nowait(items[-1])

        try:
            return queue.get(block=timeout > 0, timeout=timeout)
        except Empty:
            return ""
        
    def __del__(self):
        self.stop()