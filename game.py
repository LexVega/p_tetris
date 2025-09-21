import os
import sys

from collections.abc import Iterator, Callable
from enum import Enum, auto
from time import perf_counter

from pieces import Piece

def clear_screen():
    """
    Clears the terminal screen in a cross-platform way.
    """
    if sys.platform.startswith('win'):
        os.system('cls')  # For Windows
    else:
        # For Linux, macOS, and other Unix-like systems, ANSI escape sequence
        print("\033[2J\033[H", end='')

class Colorizer:
    """Handles cross-platform terminal colorization."""
    
    def __init__(self):
        # Check if we are on Windows AND not a modern terminal
        self.is_windows = sys.platform.startswith('win')
        # A simple check: if on Windows, assume no color unless we detect a modern terminal.
        # For simplicity, we can just disable colors on Windows, or be smarter.
        self.supports_color = not self.is_windows # Simple approach: colors on Unix, off on Win
        # For a more advanced approach, you could check for Windows Terminal here.

    def color(self, color_code):
        """Return the color code if supported, else an empty string."""
        if self.supports_color:
            return color_code
        return ""

    # Define your colors as properties or methods
    @property
    def cyan(self):
        return self.color("\033[96m")
    
    @property
    def yellow(self):
        return self.color("\033[93m")
    
    @property
    def magenta(self):
        return self.color("\033[95m")
    
    @property
    def green(self):
        return self.color("\033[92m")
    
    @property
    def red(self):
        return self.color("\033[91m")
    
    @property
    def blue(self):
        return self.color("\033[94m")
    
    @property
    def orange(self):
        return self.color("\033[33m")
    
    @property
    def reset(self):
        return self.color("\033[0m")
    
COLORS = {
    'I': "\033[96m",  # Cyan
    'O': "\033[93m",  # Yellow
    'T': "\033[95m",  # Magenta
    'S': "\033[92m",  # Green
    'Z': "\033[91m",  # Red
    'J': "\033[94m",  # Blue
    'L': "\033[33m",  # Orange-ish
    'RESET': "\033[0m",
}

class GameState(Enum):
    RUNNING = auto()
    LEVEL_UP = auto()
    GAME_OVER = auto()

class Game:
    WIDTH = 10
    HEIGHT = 20
    
    H_BORDER = f'+{"-"*WIDTH}+'
    W_BORDER_CHAR = "|"
    EMPRY_ROW = f'{W_BORDER_CHAR}{" " * WIDTH}{W_BORDER_CHAR}'
    LEVEL_LINE = 1
    SCORE_LINE = 2
    TIME_LINE = 18
    PREVIEW_BOX_START_LINE = 4
    PREVIEW_BOX_SIZE = 4
    PREVIEW_BOX_END_LINE = PREVIEW_BOX_START_LINE + PREVIEW_BOX_SIZE
    
    GHOST_CHAR = "@"
    FIG_CHAR = "@"
    
    MIN_GRAVITY = 0.05
    MAX_GRAVITY = 0.3
    LEVEL_UP_EVERY_X_LINES = 1
    KICK_OFFSETS = [(0, 0), (1, 0), (-1, 0), (2, 0), (-2, 0), (0, -1)]
    
    def __init__(self, piece_generator: Callable[[], Iterator[Piece]]):
        self.field = [[" "] * self.WIDTH for _ in range(self.HEIGHT)]
        self.piece_gen: Iterator[Piece] = piece_generator()
        self.next_piece: Piece | None = None
        self.current_piece = None
        self.preview_box = []
        
        self.state: GameState = GameState.RUNNING
        self.state_timer = 0.0
        
        self.game_started_at = perf_counter()
        self.score = 0
        self.cleared_lines = 0
        self.level = 1
        self.redraw_required = False
        
        self.colorizer = Colorizer() # Initialize color helper
        self.Colors = { # Redefine the COLORS dict using the colorizer
            'I': self.colorizer.cyan,
            'O': self.colorizer.yellow,
            'T': self.colorizer.magenta,
            'S': self.colorizer.green,
            'Z': self.colorizer.red,
            'J': self.colorizer.blue,
            'L': self.colorizer.orange,
            'RESET': self.colorizer.reset,
        }
    
    @property
    def is_running(self):
        return self.state == GameState.RUNNING
    
    @property
    def is_leveling_up(self):
        return self.state == GameState.LEVEL_UP
    
    @property
    def is_game_over(self):
        return self.state == GameState.GAME_OVER
    
    def get_playtime(self):
        return perf_counter() - self.game_started_at
    
    def get_spawning_pos(self):
        x = (self.WIDTH - self.current_piece.width) // 2
        y = -2
        return x, y
    
    def update_level(self):
        new_level = 1 + self.cleared_lines // self.LEVEL_UP_EVERY_X_LINES
        if new_level > self.level:
            self.level = new_level
            self.state = GameState.LEVEL_UP
            self.state_timer = perf_counter()
        
    def spawn_piece(self):
        self.current_piece = self.next_piece or next(self.piece_gen)
        self.current_piece.x, self.current_piece.y = self.get_spawning_pos()
        self.next_piece = next(self.piece_gen)
        self.update_preview_box()
        
        if not self.can_move(1, 1):
            self.state = GameState.GAME_OVER
            self.state_timer = perf_counter()
    
    def print_empty_rows(self, times):
        for _ in range(times): print(self.EMPRY_ROW)
    
    def draw_message(self, text: str):
        half_height = self.HEIGHT // 2 - 1
        padding = (self.WIDTH // 2 - len(text) // 2)
        padding_left = " " * padding
        padding_right = " " * (self.WIDTH - padding - len(text))
        
        clear_screen()
        print(self.H_BORDER)
        self.print_empty_rows(half_height)
        print(f'{self.W_BORDER_CHAR}{padding_left}{text}{padding_right}{self.W_BORDER_CHAR}')
        self.print_empty_rows(half_height)
        print(self.H_BORDER)
    
    def fill_row(self, row, char="#"):
        if 0 <= row < self.HEIGHT:
            self.field[row] = [char] * self.WIDTH
            self.redraw_required = True
    
    def update_preview_box(self):
        self.preview_box = [[" "] * self.PREVIEW_BOX_SIZE for _ in range(self.PREVIEW_BOX_SIZE)]
        if not self.next_piece:
            return
        for y, row in enumerate(self.next_piece.shape):
            for x, cell in enumerate(row):
                if cell != " ":
                    self.preview_box[y][x] = cell
    
    def rotate(self):
        rotated = self.current_piece.rotated
        
        for dx, dy in self.KICK_OFFSETS:
            if self.can_move(dx, dy, rotated):
                self.current_piece.x += dx
                self.current_piece.y += dy
                self.current_piece.shape = rotated
                self.redraw_required = True
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
                    if board_x < 0 or board_x >= self.WIDTH or board_y >= self.HEIGHT:
                        return False
                    if board_y >= 0 and self.field[board_y][board_x] != ' ':
                        return False
        return True
        
    def get_gravity(self):
        return max(self.MIN_GRAVITY, self.MAX_GRAVITY - (self.level -1) * 0.02)
    
    def move(self, x: int = 0, y: int = 0):
        if x or y:
            self.current_piece.x += x
            self.current_piece.y += y
            self.redraw_required = True
        
    def merge(self):
        targets = []
        for row_idx, row in enumerate(self.current_piece.shape):
            for col_idx, cell in enumerate(row):
                if cell == ' ': continue
                board_y = self.current_piece.y + row_idx
                board_x = self.current_piece.x + col_idx
                self.field[board_y][board_x] = cell
    
    def clear_lines(self):
        new_field = [row for row in self.field if any(c == " " for c in row)]
        cleared_lines = self.HEIGHT - len(new_field)
        self.field = [[' '] * self.WIDTH for _ in range(cleared_lines)] + new_field
        self.score += cleared_lines * cleared_lines * 100
        self.cleared_lines += cleared_lines
        if cleared_lines:
            self.update_level()
    
    def get_drop_y(self):
        y = self.current_piece.y
        while self.can_move(dy=y + 1 - self.current_piece.y):
            y += 1
        return y
    
    def tick_physics(self):
        if self.state != GameState.RUNNING:
            return # no physics on other states
    
        if self.can_move(0, 1):
            self.current_piece.y += 1
        else:
            self.merge()
            self.clear_lines()
            self.spawn_piece()
        self.redraw_required = True

    def draw(self):
        clear_screen()
        buffer = [row[:] for row in self.field]
        self._overlay_current_piece(buffer)
        self._overlay_ghost_piece(buffer)
        
        print(self.H_BORDER)
        for idx, row in enumerate(buffer):
            new_row = [self.W_BORDER_CHAR, *row, self.W_BORDER_CHAR, *list(self._get_sidebar_line(idx))]
            new_row = self._colorize_row(new_row)
            print(''.join(new_row))
        print(self.H_BORDER)
        
        self.redraw_required = False
    
    def _overlay_current_piece(self, temp):
        for row_idx, row in enumerate(self.current_piece.shape):
            for col_idx, cell in enumerate(row):
                if cell != " " and 0 <= self.current_piece.y + row_idx < self.HEIGHT:
                    temp[self.current_piece.y + row_idx][self.current_piece.x + col_idx] = cell

    def _overlay_ghost_piece(self, temp):
        ghost_y = self.get_drop_y()
        for row_idx, row in enumerate(self.current_piece.shape):
            for col_idx, cell in enumerate(row):
                if cell != " ":
                    gy = ghost_y + row_idx
                    gx = self.current_piece.x + col_idx
                    if 0 <= gy < self.HEIGHT and temp[gy][gx] == " ":
                        temp[gy][gx] = self.GHOST_CHAR
    
    def _colorize_row(self, row):
        new_row = []
        for char in row:
            if char in self.Colors:
                new_row.append(f"{self.Colors[char]}{self.FIG_CHAR}{self.Colors['RESET']}")
            elif char == self.GHOST_CHAR:
                new_row.append(f"{self.Colors['RESET']}{self.GHOST_CHAR}{self.Colors['RESET']}")
            else:
                new_row.append(char)
        return new_row
    
    def _get_sidebar_line(self, idx):
        padding = '   '
        lines = {
            self.LEVEL_LINE: f"{padding}level: {self.level}",
            self.SCORE_LINE: f"{padding}score: {self.score}",
            self.TIME_LINE: f"{padding}time: {self.get_playtime():.1f}s",
        }
        if idx in lines:
            return lines[idx]
        elif self.PREVIEW_BOX_START_LINE <= idx < self.PREVIEW_BOX_END_LINE:
            pj = idx - self.PREVIEW_BOX_START_LINE
            return f'{padding}{self._get_preview_row(pj)}'
        else:
            return ''

    def _get_preview_row(self, j):
        if not self.preview_box:
            return " " * self.PREVIEW_BOX_SIZE

        out = ""
        for c in self.preview_box[j]:
            out += c if c != " " else " "
        return out
