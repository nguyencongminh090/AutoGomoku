"""Engine management for Gomoku engines."""

import subprocess
from queue import Queue, Empty
from threading import Thread
from typing import TextIO, Callable
from pygomo import IProtocol, ProtocolFactory


class StdoutReader:
    """Asynchronously reads and categorizes stdout from an engine process.

    Attributes:
        max_queue_size: Maximum number of messages per category queue.
    """

    def __init__(self, stream: TextIO):
        self._stream        = stream
        self._queues        = {}
        self._filters       = {}
        self._thread        = Thread(target=self._populate_queue)
        self._thread.daemon = True
        self._thread.start()

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
        while True:
            line = self._stream.readline()
            if line == "":  # EOF
                break

            line = line.strip().lower()
            if not line:
                continue

            for category, filter_func in self._filters.items():
                if filter_func(line):
                    try:
                        self._queues[category].put_nowait(line)
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
            self._reset_queue(queue)

        try:
            return queue.get(block=True, timeout=timeout)
        except Empty:
            return ""

    @staticmethod
    def _reset_queue(queue: Queue) -> None:
        """Keep only the most recent item in the queue."""
        while queue.qsize() > 1:
            queue.get_nowait()

class Engine:
    """Manages a Gomoku engine subprocess.

    Attributes:
        id: Process ID of the engine.
        protocol: Protocol instance for communication.
    """

    def __init__(self, path: str, protocol_type: str):
        """Initialize the engine with a given protocol.

        Args:
            path: Path to the engine executable.
            protocol_type: Type of protocol (e.g., 'gomocup').

        Raises:
            FileNotFoundError: If the engine executable is not found.
            ValueError: If the protocol type is unsupported.
        """
        try:
            self._engine = subprocess.Popen(
                path,
                stdin    =subprocess.PIPE,
                stdout   =subprocess.PIPE,
                bufsize  =1,
                universal_newlines=True,
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Engine executable not found at: {path}")

        self.id           = self._engine.pid
        self._std_reader  = StdoutReader(self._engine.stdout)
        self.protocol     = ProtocolFactory.create(
            protocol_type,
            self._send,
            self._receive,
        )

    def _send(self, *command: str) -> None:
        """Send a command to the engine.

        Args:
            command: Command parts to send.

        Raises:
            RuntimeError: If the engine process has terminated.
        """
        if self._engine.poll() is not None:
            raise RuntimeError("Engine process has terminated unexpectedly")
        cmd = " ".join(str(c).upper() if i == 0 else str(c) for i, c in enumerate(command))
        self._engine.stdin.write(f"{cmd}\n")
        self._engine.stdin.flush()

    def _receive(self, name: str, reset: bool = False, timeout: float = 0.0) -> str:
        """Receive a message from the engine.

        Args:
            name: Category of message to receive.
            reset: If True, clear the category queue.
            timeout: Maximum time to wait (seconds).

        Returns:
            The received message, or empty string if none.
        """
        return self._std_reader.get(name, reset=reset, timeout=timeout)

    def terminate(self) -> None:
        """Terminate the engine process."""

        # Terminate engine by protocol command
        self.protocol.quit()
        self._engine.wait(timeout=1.0)
        # If the engine is still running, forcefully terminate it
        if self._engine.poll() is None:            
            self._engine.terminate()
            self._engine.wait(timeout=1.0)