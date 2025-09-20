import sys
import time
import atexit
import select
import random
import os

from collections.abc import Iterator, Callable


if sys.platform.startswith('win'):
    import msvcrt
else:
    import tty
    import termios

CLEAR = 'cls' if os.name == 'nt' else 'clear'
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


class Game:
    WIDTH = 10
    HEIGHT = 20
    
    H_BORDER = "+" + "-" * WIDTH + "+"
    W_BORDER_CHAR = "|"
    LEVEL_LINE = 1
    SCORE_LINE = 2
    TIME_LINE = 18
    PREVIEW_BOX_START_LINE = 4
    PREVIEW_BOX_SIZE = 4
    PREVIEW_BOX_END_LINE = PREVIEW_BOX_START_LINE + PREVIEW_BOX_SIZE
    
    GHOST_CHAR = "@"
    FIG_CHAR = "@"
    
    def __init__(self, piece_generator: Callable[[], Iterator[Piece]]):
        self.field = [[" "] * self.WIDTH for _ in range(self.HEIGHT)]
        self.piece_gen: Iterator[Piece] = piece_generator()
        self.next_piece: Piece | None = None
        self.current_piece = None
        self.preview_box = []
        self.game_over = False
        self.game_started_at = time.perf_counter()
        self.score = 0
        self.cleared_lines = 0
        self.level = 1
        self.redraw_required = False
    
    def get_playtime(self):
        return time.perf_counter() - self.game_started_at
    
    def get_spawning_pos(self):
        x = (self.WIDTH - self.current_piece.width) // 2
        y = -2
        return x, y
    
    def update_level(self):
        difficulty_up_every_x_lines = 10
        new_level = 1 + self.cleared_lines // difficulty_up_every_x_lines
        if new_level > self.level:
            self.level = new_level
        
    def spawn_piece(self):
        self.current_piece = self.next_piece or next(self.piece_gen)
        self.current_piece.x, self.current_piece.y = self.get_spawning_pos()
        self.next_piece = next(self.piece_gen)
        self.update_preview_box()
        
        if not self.can_move(1, 1):
            self.game_over = True
    
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
        
        offsets = [(0, 0), (1, 0), (-1, 0), (2, 0), (-2, 0), (0, -1)]
        for dx, dy in offsets:
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
        if self.can_move(0, 1):
            self.current_piece.y += 1
        else:
            self.merge()
            self.clear_lines()
            self.spawn_piece()
        self.redraw_required = True

    def draw(self):
        os.system(CLEAR)
        buffer = [row[:] for row in self.field]
        self._overlay_current_piece(buffer)
        self._overlay_ghost_piece(buffer)
        
        print(self.H_BORDER)
        for idx, row in enumerate(buffer):
            row = [self.W_BORDER_CHAR, *self._colorize_row(row), self.W_BORDER_CHAR, self._get_sidebar_line(idx)]
            print(''.join(row))
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
            if char in COLORS:
                new_row.append(f"{COLORS[char]}{self.FIG_CHAR}{COLORS['RESET']}")
            elif char == self.GHOST_CHAR:
                new_row.append(f"{COLORS['RESET']}{self.GHOST_CHAR}{COLORS['RESET']}")
            else:
                new_row.append(char)
        return new_row
    
    def _get_sidebar_line(self, idx):
        lines = {
            self.LEVEL_LINE: f"   Level: {self.level}",
            self.SCORE_LINE: f"   Score: {self.score}",
            self.TIME_LINE: f"   Time: {self.get_playtime():.1f}s",
        }
        if idx in lines:
            return lines[idx]
        elif self.PREVIEW_BOX_START_LINE <= idx < self.PREVIEW_BOX_END_LINE:
            pj = idx - self.PREVIEW_BOX_START_LINE
            return "   " + self._get_preview_row(pj)
        else:
            return ''

    def _get_preview_row(self, j):
        if not self.preview_box:
            return " " * self.PREVIEW_BOX_SIZE

        out = ""
        for c in self.preview_box[j]:
            if c in COLORS:
                out += f"{COLORS[c]}{self.FIG_CHAR}{COLORS['RESET']}"
            else:
                out += " "
        return out


class Input:
    def __init__(self):
        """Put terminal into cbreak mode in Unix"""
        if not sys.platform.startswith('win'):
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
            atexit.register(self.restore)

    def restore(self):
        """Restore input mode on Unix"""
        if not sys.platform.startswith('win'):
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)
    
    def get_dir_by_char(self, char: str) -> str | None:
        match char.lower():
            case 'a': return 'LEFT'
            case 'd': return 'RIGHT'
            case 's': return 'DOWN'
            case 'w': return 'UP'
            case ' ': return 'SPACE'
            case _: return None
    
    WIN_KEY_MAP = {
        'K': 'LEFT',
        'M': 'RIGHT',
        'P': 'DOWN',
        'H': 'UP',
    }
    UNIX_KEY_MAP = {
        '[D': 'LEFT',
        '[C': 'RIGHT',
        '[B': 'DOWN',
        '[A': 'UP',
    }
    
    def get_key(self):
        """Return LEFT/RIGHT/DOWN/UP or None"""
        last = None
        if sys.platform.startswith('win'):
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ('\x00', '\xe0'):
                    ch2 = msvcrt.getwch()
                    last = self.WIN_KEY_MAP.get(ch2, None)
                else:
                    last = self.get_dir_by_char(ch)
            return last
        else:
            while select.select([sys.stdin], [], [], 0)[0]:
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    ch2 = sys.stdin.read(2)
                    last = self.UNIX_KEY_MAP.get(ch2, None)
                else:
                    last = self.get_dir_by_char(ch)
            return last

key_reader = Input()
game = Game(bag_piece_generator)
game.spawn_piece()

gravity_interval = 0.3
last = time.perf_counter()
acc = 0.0
REFRESH_RATE = 0.01

while not game.game_over:
    now = time.perf_counter()
    acc += time.perf_counter() - last
    last = now

    # Handle key presses
    key = key_reader.get_key()
    if key:
        if key == 'LEFT' and game.can_move(dx=-1):
            game.move(x=-1)
        elif key == 'RIGHT' and game.can_move(dx=1):
            game.move(x=1)
        elif key == 'UP':
            game.rotate()
        elif key == 'DOWN' and game.can_move(dy=1):
            game.move(y=1)
        elif key == 'SPACE':
            while game.can_move(dy=1):
                game.move(y=1)
            game.tick_physics()
            acc = 0
    
    # Handle gravity
    if acc >= gravity_interval:
        acc -= gravity_interval
        game.tick_physics()
    
    if game.redraw_required:
        game.draw()
    
    time.sleep(REFRESH_RATE)
    
