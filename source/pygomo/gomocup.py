"""Gomocup protocol implementation for Gomoku engines."""

import re
import math
from typing import Callable, Dict, TextIO, Union, List, Tuple

from pygomo import StdoutReader
from pygomo import IProtocol, IProtocolHandler, Move, TimeOut


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
        return self._reader("output", timeout=timeout) == "ok"

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


class Mate:
    """Represents a mate evaluation (e.g., mate in 5 moves)."""

    def __init__(self, value: str):
        """Initialize with a mate value.

        Args:
            value: Mate value (e.g., '+m5').

        Raises:
            ValueError: If the value is invalid.
        """
        if not value.startswith(("+m", "-m")):
            raise ValueError(f"Invalid mate value: {value}")
        try:
            int(value[2:])
        except ValueError:
            raise ValueError(f"Invalid mate value: {value}")
        self._value = value

    def step(self) -> int:
        """Return the number of moves to mate."""
        return int(self._value[2:])


class Evaluate:
    """Represents an engine evaluation (score or mate)."""

    def __init__(self, value: str):
        """Initialize with an evaluation value.

        Args:
            value: Evaluation value (e.g., '100', '+m5').

        Raises:
            ValueError: If the value is invalid.
        """
        self._value = value

    def score(self) -> Union[str, float, Mate]:
        """Return the evaluation score.

        Returns:
            Float for numeric scores, Mate for mate values, or string if unknown.
        """
        if "m" not in self._value:
            try:
                return float(self._value)
            except ValueError:
                return self._value
        return Mate(self._value)

    def winrate(self) -> float:
        """Calculate the win rate based on the evaluation.

        Returns:
            A value between 0 and 1 representing win probability.
        """
        def _to_score(x: str) -> float:
            if "m" not in x:
                try:
                    return float(x)
                except ValueError:
                    return 0.0
            value = Mate(x).step()
            # Simplified winrate for mate scores
            return (20000 - abs(value)) + (2 * (abs(value) - 20000) & (value >> 31))

        score = float(_to_score(self._value))
        return 1 / (1 + math.e ** (-score / 200))

    def is_winning(self) -> bool:
        """Check if the evaluation indicates a win."""
        return self._value.startswith("+m")

    def is_losing(self) -> bool:
        """Check if the evaluation indicates a loss."""
        return self._value.startswith("-m")


class PlayResult:
    """Represents the result of a play command."""

    def __init__(self, move: str, info: str):
        """Initialize with a move and info string.

        Args:
            move: The engine's move.
            info: Additional info from the engine.

        Raises:
            ValueError: If the move is invalid.
        """
        self.move = Move(move)
        self.info = self._parse_uci(info)

    def _parse_uci(self, info: str) -> Dict:
        """Parse UCI-like info string.

        Args:
            info: Info string from the engine.

        Returns:
            Dictionary with parsed info (e.g., depth, evaluation).
        """
        pattern = re.compile(
            r"depth (\d+)-(\d+) ev ([+-]?\w?\d+) n (\d+)(?:\w) (?:\S*) (\d+) tm (\d+)(?:\S*) pv ((?:[a-zA-Z]\d+\s?)*)"
        )
        match = pattern.search(info)
        if match:
            return {
                "depth": f"{match.group(1)}-{match.group(2)}",
                "ev"   : Evaluate(match.group(3)),
                "node" : match.group(4),
                "nps"  : match.group(5),
                "time" : int(match.group(6)),
                "pv"   : [Move(m) for m in match.group(7).split() if m],
            }
        return {}

    def parse_custom(self, pattern: str, keys: Tuple[str, ...]) -> None:
        """Parse info with a custom regex pattern.

        Args:
            pattern: Regex pattern to match.
            keys: Keys for matched groups.

        Raises:
            ValueError: If the number of keys doesn't match groups.
        """
        pattern_obj = re.compile(pattern)
        match       = pattern_obj.search(self.info)
        obj_dict    = {}
        if match:
            if len(keys) != match.lastindex:
                raise ValueError("Number of keys does not match regex groups")
            for idx, key in enumerate(keys, 1):
                obj_dict[key] = match.group(idx)
        self.info.clear()
        self.info.update(obj_dict)