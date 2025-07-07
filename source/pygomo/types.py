import re
import math
from typing import Dict, Tuple, Union


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

class TimeOut(Exception):
    """Exception raised when an engine operation times out."""
    pass