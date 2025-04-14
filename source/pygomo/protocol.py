"""Abstract protocol interfaces and utilities for Gomoku engines."""

from abc    import ABC, abstractmethod
from queue  import Queue
from typing import Callable, Tuple, Union, Dict
from io     import TextIO
from pygomo import PlayResult
from pygomo import StdoutReader


class IProtocol(ABC):
    """Abstract interface for engine communication protocols."""

    @abstractmethod
    def play(self, move: str, time_left: int) -> "PlayResult":
        """Request a move from the engine."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the engine's computation."""
        pass

    @abstractmethod
    def quit(self) -> None:
        """End the engine session."""
        pass

    @abstractmethod
    def send_move(self, move: str) -> None:
        """Send a move to the engine."""
        pass

    @abstractmethod
    def is_ready(self, board_size: int = 15, timeout: float = 0.0) -> bool:
        """Check if the engine is ready."""
        pass

    @abstractmethod
    def send_command(self, *command: str) -> None:
        """Send a generic command to the engine."""
        pass

    @abstractmethod
    def configure(self, options: Dict) -> None:
        """Configure engine options."""
        pass


class IProtocolHandler(ABC):
    """Abstract interface for handling protocol-specific output."""

    @abstractmethod
    def get(self) -> "StdoutReader":
        """Return the stdout reader instance."""
        pass


class ProtocolFactory:
    """Factory for creating protocol instances."""

    @staticmethod
    def create(protocol_type: str, sender: Callable, reader: Callable) -> IProtocol:
        """Create a protocol instance.

        Args:
            protocol_type: Type of protocol (e.g., 'gomocup').
            sender: Function to send commands.
            reader: Function to receive responses.

        Returns:
            An IProtocol instance.

        Raises:
            ValueError: If the protocol type is unsupported.
        """
        from .gomocup import GomocupProtocol  # Avoid circular imports
        if protocol_type == "gomocup":
            return GomocupProtocol(sender, reader)
        raise ValueError(f"Unsupported protocol: {protocol_type}")


class ProtocolHandler:
    """Factory for creating protocol handler instances."""

    @staticmethod
    def create(protocol_type: str, stream: TextIO) -> IProtocolHandler:
        """Create a protocol handler instance.

        Args:
            protocol_type: Type of protocol (e.g., 'gomocup').
            stream: Input stream from the engine.

        Returns:
            An IProtocolHandler instance.

        Raises:
            ValueError: If the protocol type is unsupported.
        """
        from .gomocup import GomocupProtocolHandler  # Avoid circular imports
        if protocol_type == "gomocup":
            return GomocupProtocolHandler(stream)
        raise ValueError(f"Unsupported protocol: {protocol_type}")


class Move:
    """Represents a Gomoku move with multiple format support."""

    def __init__(self, move: Union[Tuple[int, int], str]):
        """Initialize a move from various formats.

        Args:
            move: Move in format (col, row), 'x,y', or 'a1'.

        Raises:
            ValueError: If the move format is invalid.
        """
        match move:
            case str() if "," in move:
                move = move.replace(" ", "")
                try:
                    self.col, self.row = map(int, move.split(","))
                except ValueError:
                    raise ValueError(f"Invalid move format: {move}")
            case str():
                move = move.replace(" ", "")
                if not move or len(move) < 2:
                    raise ValueError(f"Invalid move format: {move}")
                col_letter = move[0].lower()
                if not col_letter.isalpha():
                    raise ValueError(f"Invalid column in move: {move}")
                try:
                    self.row = int(move[1:]) - 1
                except ValueError:
                    raise ValueError(f"Invalid row in move: {move}")
                self.col = ord(col_letter) - 97
            case tuple() if len(move) == 2:
                self.col, self.row = move
            case _:
                raise ValueError(f"Invalid move format: {move}")

    def to_num(self) -> Tuple[int, int]:
        """Return move as (col, row)."""
        return self.col, self.row

    def to_alphabet(self) -> str:
        """Return move in algebraic notation (e.g., 'a1')."""
        return f"{chr(97 + self.col)}{self.row + 1}"

    def to_strnum(self) -> str:
        """Return move as string 'col,row'."""
        return f"{self.col},{self.row}"

    def __str__(self) -> str:
        return self.to_alphabet()

    def __repr__(self) -> str:
        return f"<Move {self.to_alphabet()}>"


class TimeOut(Exception):
    """Exception raised when an engine operation times out."""
    pass