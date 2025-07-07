"""Engine management for Gomoku engines."""

import subprocess
from .protocol  import ProtocolFactory
from .io_helper import StdoutReader


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
                stdin    = subprocess.PIPE,
                stdout   = subprocess.PIPE,
                bufsize  = 1,
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