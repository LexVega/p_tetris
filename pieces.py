import random

from collections.abc import Iterator
from enum import Enum, auto


class PieceType(Enum):
    I = auto()
    O = auto()
    T = auto()
    J = auto()
    L = auto()
    S = auto()
    Z = auto()

SHAPES = {
    PieceType.I: [
    "    ",
    "IIII",
    "    ",
    ],
    PieceType.O: [
    "OO",
    "OO",
    ],
    PieceType.T: [
    " T ",
    "TTT",
    ],
    PieceType.J: [
    "  J",
    "JJJ",
    ],
    PieceType.L: [
    "L  ",
    "LLL",
    ],
    PieceType.S: [
    "SS ",
    " SS",
    ],
    PieceType.Z: [
    " ZZ", 
    "ZZ ",
    ],
}

class Piece:
    def __init__(self, kind: PieceType, x: int = 0, y: int = 0):
        self.kind = kind
        self.shape = [list(row) for row in SHAPES[kind]]
        self.x = x
        self.y = y
    
    @property
    def width(self):
        return max(len(row) for row in self.shape)
    
    @property
    def height(self):
        return len(self.shape)
    
    @property
    def rotated_shape(self):
        """Return rotated shape (clockwise) without modifying self"""
        return [list(row) for row in zip(*self.shape[::-1])]


def random_piece_generator() -> Iterator[Piece]:
    while True:
        random_kind = random.choice(list(PieceType))
        yield Piece(random_kind)

def bag_piece_generator() -> Iterator[Piece]:
    while True:
        bag = list(PieceType)
        random.shuffle(bag)
        for piece_type in bag:
            yield Piece(piece_type)
            
