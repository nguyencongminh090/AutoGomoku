"""Abstract protocol interfaces and utilities for Gomoku engines."""

from abc        import ABC, abstractmethod
from typing     import Callable, Dict, TextIO
from .types     import PlayResult
from .io_helper import StdoutReader


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
