import random
from collections.abc import Iterator


class Piece:
    FIGURES = {
        'I': [
        "    ",
        "IIII",
        "    ",
        ],           
        'O': ["OO", "OO"],       # O
        'T': [" T ", "TTT"],     # T
        'J': ["  J", "JJJ"],     # J
        'L': ["L  ", "LLL"],     # L
        'S': ["SS ", " SS"],     # S
        'Z': [" ZZ", "ZZ "],     # Z
    }

    def __init__(self, kind):
        self.kind = kind
        self.shape = [list(row) for row in self.FIGURES[kind]]
        self.x = 0
        self.y = 0
    
    @property
    def width(self):
        return max(len(row) for row in self.shape)
    
    @property
    def height(self):
        return len(self.shape)
    
    @property
    def rotated(self):
        """Return rotated shape (clockwise) without modifying self"""
        return [list(row) for row in zip(*self.shape[::-1])]


def random_piece_generator() -> Iterator[Piece]:
    while True:
        yield Piece(random.choice(list(Piece.FIGURES)))

def bag_piece_generator() -> Iterator[Piece]:
    while True:
        bag = [Piece(kind) for kind in Piece.FIGURES]
        random.shuffle(bag)
        for piece in bag:
            yield piece
            
