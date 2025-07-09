"""Gomocup protocol implementation for Gomoku engines."""

import re
from typing     import Callable, Dict, TextIO
from .io_helper import StdoutReader
from .types     import PlayResult, TimeOut
from .protocol  import IProtocol, IProtocolHandler


class GomocupProtocolHandler(IProtocolHandler):
    """Handles Gomocup protocol output."""

    def __init__(self, stream: TextIO):
        """Initialize with an engine output stream.

        Args:
            stream: Text stream from the engine.
        """
        self._stdout_reader = StdoutReader(stream)
        self._stdout_reader.add_category("coord"  , self._is_coord)
        self._stdout_reader.add_category("message", self._is_message)
        self._stdout_reader.add_category("output" , self._is_output)

    def _is_coord(self, line: str) -> bool:
        """Check if a line contains coordinates."""
        return bool(re.match(r"^\d+\s*,\s*\d+(\s+\d+\s*,\s*\d+)*$", line))

    def _is_message(self, line: str) -> bool:
        """Check if a line is a message."""
        return line.lower().startswith("message")

    def _is_output(self, line: str) -> bool:
        """Check if a line is general output (not error)."""
        return not line.lower().startswith("error")

    def get(self) -> StdoutReader:
        """Return the stdout reader."""
        return self._stdout_reader


class GomocupProtocol(IProtocol):
    """Implements the Gomocup protocol for Gomoku engines."""

    def __init__(self, sender: Callable, reader: Callable):
        """Initialize with sender and reader functions.

        Args:
            sender: Function to send commands.
            reader: Function to receive responses.
        """
        self._sender = sender
        self._reader = reader

    def play(self, move: str, time_left: int) -> "PlayResult":
        """Request a move from the engine.

        Args:
            move: The last move played (e.g., '5,5').
            time_left: Time remaining in milliseconds.

        Returns:
            PlayResult with the engine's move and info.

        Raises:
            TimeOut: If no move is returned within time_left.
        """
        self.configure({"time_left": time_left})
        self.send_move(move)
        best_move = self._reader("coord"  , timeout=time_left / 1000.0)
        info      = self._reader("message", reset=True, timeout=time_left / 1000.0)
        if not best_move:
            self.stop()
            raise TimeOut(f"Timeout: Engine did not return move after {time_left}ms")
        return PlayResult(best_move, info)

    def stop(self) -> None:
        """Stop the engine's computation."""
        self._sender("stop")

    def quit(self) -> None:
        """End the engine session."""
        self._sender("end")

    def send_move(self, move: str) -> None:
        """Send a move to the engine."""
        self._sender("turn", move)

    def is_ready(self, board_size: int = 15, timeout: float = 0.0) -> bool:
        """Check if the engine is ready.

        Args:
            board_size: Size of the Gomoku board.
            timeout: Maximum time to wait (seconds).

        Returns:
            True if the engine responds with 'ok', False otherwise.
        """
        self._sender("start", board_size)
        return self._reader("output", reset=True, timeout=timeout) == "ok"

    def send_command(self, *command: str) -> None:
        """Send a generic command to the engine."""
        self._sender(*command)

    def configure(self, options: Dict) -> None:
        """Configure engine options.

        Args:
            options: Dictionary of option key-value pairs.
        """
        for key, value in options.items():
            self._sender("info", key, value)
