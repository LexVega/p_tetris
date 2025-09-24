from dataclasses import dataclass
from pieces import Piece

@dataclass
class GameSnapshot:
    field: list[list[str]]
    current_piece: Piece
    next_piece: Piece
    ghost_y: int
    level: int
    score: int
    playtime: float
