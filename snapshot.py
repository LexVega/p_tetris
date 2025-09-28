from dataclasses import dataclass
from pieces import Piece

@dataclass
class FieldSnapshot:
    width: int
    height: int
    grid: list[list[int]]

@dataclass
class GameSnapshot:
    field: FieldSnapshot
    current_piece: Piece
    next_piece: Piece
    ghost_y: int
    level: int
    score: int
    playtime: float
    
