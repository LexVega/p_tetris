from collections.abc import Iterator, Callable
from dataclasses import dataclass
from enum import Enum, auto
from time import perf_counter

from input import Action
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

class GameState(Enum):
    RUNNING = auto()
    LEVEL_UP = auto()
    GAME_OVER = auto()

class Game:   
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
   
    def update_level(self):
        new_level = 1 + self.cleared_lines // self.LEVEL_UP_EVERY_X_LINES
        if new_level > self.level:
            self.level = new_level
            self.change_state(GameState.LEVEL_UP, 0.5)
    
    def spawn_piece(self):
        self.current_piece = self.next_piece or next(self.piece_gen)
        self.current_piece.x, self.current_piece.y = self.spawning_pos
        self.next_piece = next(self.piece_gen)
        
        if not self.can_move(1, 1):
            self.change_state(GameState.GAME_OVER)
    
    def rotate(self):
        rotated_shape = self.current_piece.rotated_shape
        
        for dx, dy in self.KICK_OFFSETS:
            if self.can_move(dx, dy, rotated_shape):
                self.current_piece.x += dx
                self.current_piece.y += dy
                self.current_piece.shape = rotated_shape
                break
    
    def can_move(self, dx=0, dy=0, shape=None):
        """
        Check if `shape` can be placed at (x+dx, y+dy).
        Defaults: current shape, current position.
        """
        shape = shape or self.current_piece.shape
    
        for row_idx, row in enumerate(shape):
            for col_idx, cell in enumerate(row):
                if cell != ' ':
                    board_x = self.current_piece.x + col_idx + dx
                    board_y = self.current_piece.y + row_idx + dy
                    if board_x < 0 or board_x >= self.width or board_y >= self.height:
                        return False
                    if board_y >= 0 and self.field[board_y][board_x] != ' ':
                        return False
        return True
    
    def move_current_piece(self, x: int = 0, y: int = 0) -> bool:
        if self.current_piece and (x or y) and self.can_move(dx=x, dy=y):
            self.current_piece.x += x
            self.current_piece.y += y
            return True
        return False
    
    def merge(self):
        for row_idx, row in enumerate(self.current_piece.shape):
            for col_idx, cell in enumerate(row):
                if cell == ' ': continue
                board_y = self.current_piece.y + row_idx
                board_x = self.current_piece.x + col_idx
                self.field[board_y][board_x] = cell
    
    def clear_lines(self):
        new_field = [row for row in self.field if any(c == " " for c in row)]
        cleared_lines = self.height - len(new_field)
        self.field = [[' '] * self.width for _ in range(cleared_lines)] + new_field
        self.score += cleared_lines * cleared_lines * 100
        self.cleared_lines += cleared_lines
        if cleared_lines:
            self.update_level()
    
    def change_state(self, new_state: GameState, timer: float = 0.0):
        if new_state == self._current_state: return
        self._next_state_timer = perf_counter() + timer if timer else 0.0
        self._prev_state = self._current_state
        self._current_state = new_state
    
    def _process_state_transitions(self):
        if self._next_state_timer and self._next_state_timer <= perf_counter():
            self.change_state(self._prev_state)
        
    def _process_physics(self, dt: float):
        if not self.is_running: return
    
        self._physics_acc += dt
        while self._physics_acc >= self.physics_interval:
            self._physics_acc -= self.physics_interval
            if not self.move_current_piece(y=1):
                self.lock_piece()
    
    def lock_piece(self):
        self.merge()
        self.clear_lines()
        self.spawn_piece()

    def process(self, dt: float, action: Action | None = None, ):
        self._process_state_transitions()
        self._process_action(action)
        self._process_physics(dt)
    
    def _process_action(self, action: Action | None):
        if not self.is_running or not action:
            return
        
        if action == Action.MOVE_LEFT:
            self.move_current_piece(x=-1)
        elif action == Action.MOVE_RIGHT:
            self.move_current_piece(x=1)
        elif action == Action.ROTATE:
            self.rotate()
        elif action == Action.SOFT_DROP:
            self.move_current_piece(y=1)
        elif action == Action.HARD_DROP:
            move_by = self.ghost_y - self.current_piece.y
            self.move_current_piece(y=move_by)
            self.lock_piece()
    
    def start(self):
        self.spawn_piece()
