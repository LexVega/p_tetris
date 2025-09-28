import random

from collections.abc import Iterator
from enum import Enum, auto

EMPTY = 0

class PieceType(Enum):
    I = 1
    O = 2
    T = 3
    J = 4
    L = 5
    S = 6
    Z = 7

SHAPES = {
    PieceType.I: [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
    ],
    PieceType.O: [
        [1, 1],
        [1, 1],
    ],
    PieceType.T: [
        [0, 1, 0],
        [1, 1, 1]
    ],
    PieceType.J: [
        [0, 0, 1],
        [1, 1, 1],
    ],
    PieceType.L: [
        [1, 0, 0],
        [1, 1, 1],
    ],
    PieceType.S: [
        [1, 1, 0],
        [0, 1, 1],
    ],
    PieceType.Z: [
        [0, 1, 1],
        [1, 1, 0],
    ],
}

class Piece:
    def __init__(self, kind: PieceType, x: int = 0, y: int = 0):
        self.kind = kind
        self.shape = [
            [kind.value if c else EMPTY for c in row]
            for row in SHAPES[kind]
        ]
        
        self.x = x
        self.y = y
    
    @property
    def width(self):
        return max(len(row) for row in self.shape)
    
    @property
    def height(self):
        return len(self.shape)
    
    @property
    def rotated(self):
        """Return new Piece with rotated shape (clockwise)"""
        new_piece = Piece(
            kind = self.kind,
            x = self.x,
            y = self.y
        )
        new_piece.shape = [list(row) for row in zip(*self.shape[::-1])]
        return new_piece


def random_piece_generator() -> Iterator[Piece]:
    while True:
        yield Piece(random.choice(list(PieceType)))

def bag_piece_generator() -> Iterator[Piece]:
    while True:
        bag = list(PieceType)
        random.shuffle(bag)
        for piece_type in bag:
            yield Piece(piece_type)
            
