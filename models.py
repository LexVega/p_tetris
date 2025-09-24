from collections.abc import Iterator, Callable
from dataclasses import dataclass
from enum import Enum, auto
from time import perf_counter

from pieces import Piece

class Action(Enum):
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    SOFT_DROP = auto()
    HARD_DROP = auto()
    ROTATE = auto()

@dataclass
class GameSnapshot:
    field: list[list[str]]
    current_piece: Piece
    next_piece: Piece
    ghost_y: int
    level: int
    score: int
    playtime: float
        

class GameState(Enum):
    RUNNING = auto()
    LEVEL_UP = auto()
    GAME_OVER = auto()

class GameModel:   
    MIN_GRAVITY = 0.05
    MAX_GRAVITY = 0.3
    LEVEL_UP_EVERY_X_LINES = 1
    KICK_OFFSETS = [(0, 0), (1, 0), (-1, 0), (2, 0), (-2, 0), (0, -1)]

    def __init__(self, width:int, height: int, piece_generator: Callable[[], Iterator[Piece]]):
        self.width = width
        self.height = height
        
        self.field = [[" "] * self.width for _ in range(self.height)]
        self.piece_gen: Iterator[Piece] = piece_generator()
        self.next_piece: Piece | None = None
        self.current_piece: Piece | None = None
        
        self._prev_state: GameState | None = None
        self._current_state: GameState = GameState.RUNNING
        self._next_state_timer: float = 0.0
        self._physics_acc: float = 0.0
        
        self.game_started_at: float = perf_counter()
        self.score = 0
        self.cleared_lines = 0
        self.level = 1
    
    @property
    def is_running(self) -> bool:
        return self._current_state == GameState.RUNNING
    
    @property
    def is_leveling_up(self) -> bool:
        return self._current_state == GameState.LEVEL_UP
    
    @property
    def is_game_over(self) -> bool:
        return self._current_state == GameState.GAME_OVER

    @property
    def physics_interval(self) -> float:
        return max(self.MIN_GRAVITY, self.MAX_GRAVITY - (self.level -1) * 0.02)
    
    @property
    def playtime(self) -> float:
        return perf_counter() - self.game_started_at
    
    @property
    def spawning_pos(self) -> tuple[int, int]:
        x = (self.width - self.current_piece.width) // 2
        y = -2
        return x, y
    
    @property
    def ghost_y(self) -> int:
        y = self.current_piece.y
        while self.can_move(dy=y + 1 - self.current_piece.y):
            y += 1
        return y
    
    @property
    def snapshot(self) -> GameSnapshot:
        return GameSnapshot(
            field=[row[:] for row in self.field],
            current_piece=self.current_piece,
            next_piece=self.next_piece,
            ghost_y=self.ghost_y,
            level=self.level,
            score=self.score,
            playtime=self.playtime
        )

