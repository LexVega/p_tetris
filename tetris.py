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
        self.game_over = False
        self.game_started_at = time.perf_counter()
        self.score = 0
        self.cleared_lines = 0
        self.level = 1
        self._changed = False
    
    @property
    def is_changed(self):
        return self._changed
    
    def get_playtime(self):
        return time.perf_counter() - self.game_started_at
    
    def spawn_piece(self):
        self.current_piece = self.next_piece or next(self.piece_gen) #.get()
        self.next_piece = next(self.piece_gen)#.get()
        self.current_piece.x = (self.WIDTH - self.current_piece.width) // 2
        self.current_piece.y = 0
        if not self.can_move(0, 0):
            self.game_over = True
    
    def rotate(self):
        rotated = self.current_piece.rotated
        
        offsets = [(0, 0), (1, 0), (-1, 0), (2, 0), (-2, 0), (0, -1)]
        for dx, dy in offsets:
            if self.can_move(dx, dy, rotated):
                self.current_piece.x += dx
                self.current_piece.y += dy
                self.current_piece.shape = rotated
                self._changed = True
                break
    
    def can_move(self, dx=0, dy=0, shape=None, x=None, y=None):
        """
        Check if `shape` can be placed at (x+dx, y+dy).
        Defaults: current shape, current position.
        """
        shape = shape or self.current_piece.shape
        x = self.current_piece.x if x is None else x
        y = self.current_piece.y if y is None else y
    
        for j, row in enumerate(shape):
            for i, cell in enumerate(row):
                if cell != ' ':
                    nx = x + i + dx
                    ny = y + j + dy
                    if nx < 0 or nx >= self.WIDTH or ny >= self.HEIGHT:
                        return False
                    if ny >= 0 and self.field[ny][nx] != ' ':
                        return False
        return True
    
    def move(self, x: int = 0, y: int = 0):
        if x or y:
            self.current_piece.x += x
            self.current_piece.y += y
            self._changed = True
        
    def merge(self):
        for j, row in enumerate(self.current_piece.shape):
            for i, cell in enumerate(row):
                if cell != ' ':
                    self.field[self.current_piece.y + j][self.current_piece.x + i] = cell
    
    def clear_lines(self):
        new_field = [row for row in self.field if any(c == " " for c in row)]
        cleared_lines = self.HEIGHT - len(new_field)
        self.field = [[' '] * self.WIDTH for _ in range(cleared_lines)] + new_field
        self.score += cleared_lines * cleared_lines * 100
        self.cleared_lines += cleared_lines
    
    def get_drop_y(self):
        y = self.current_piece.y
        while self.can_move(0, y - self.current_piece.y + 1):
            y += 1
        return y
        
    def process(self):
        if self.can_move(0, 1):
            self.current_piece.y += 1
        else:
            self.merge()
            self.clear_lines()
            self.spawn_piece()
        self._changed = True

    def draw(self):
        os.system(CLEAR)
        temp = self._compose_field_with_current_piece()

        print(self.H_BORDER)

        for y in range(self.HEIGHT):
            row_str = self._render_field_row(temp[y])
            row_str += self._render_sidebar(y)
            print(row_str)

        print(self.H_BORDER)
        self._changed = False

    def _compose_field_with_current_piece(self):
        temp = [row[:] for row in self.field]

        # ghost piece
        ghost_y = self.get_drop_y()
        for j, row in enumerate(self.current_piece.shape):
            for i, cell in enumerate(row):
                if cell != " ":
                    gy = ghost_y + j
                    gx = self.current_piece.x + i
                    if 0 <= gy < self.HEIGHT and temp[gy][gx] == " ":
                        temp[gy][gx] = self.GHOST_CHAR

        # current piece
        for j, row in enumerate(self.current_piece.shape):
            for i, cell in enumerate(row):
                if cell != " " and 0 <= self.current_piece.y + j < self.HEIGHT:
                    temp[self.current_piece.y + j][self.current_piece.x + i] = cell

        return temp

    def _render_field_row(self, row):
        out = ''
        for char in row:
            if char in COLORS:
                out += f"{COLORS[char]}{self.FIG_CHAR}{COLORS['RESET']}"
            elif char == self.GHOST_CHAR:
                out += f"{COLORS['RESET']}{self.GHOST_CHAR}{COLORS['RESET']}"
            else:
                out += " "
        return self.W_BORDER_CHAR + out + self.W_BORDER_CHAR

    def _render_sidebar(self, y):
        sidebar = {
            self.LEVEL_LINE: f"   Level: {self.level}",
            self.SCORE_LINE: f"   Score: {self.score}",
            self.TIME_LINE: f"   Time: {self.get_playtime():.1f}s",
        }
        if y in sidebar:
            return sidebar[y]
        elif self.PREVIEW_BOX_START_LINE <= y < self.PREVIEW_BOX_END_LINE:
            pj = y - self.PREVIEW_BOX_START_LINE
            return "   " + self._render_preview_row(pj)
        return ""

    def _render_preview_row(self, j):
        if not self.next_piece:
            return " " * self.PREVIEW_BOX_SIZE

        preview_box = [[" "] * self.PREVIEW_BOX_SIZE for _ in range(self.PREVIEW_BOX_SIZE)]
        for y, row in enumerate(self.next_piece.shape):
            for x, cell in enumerate(row):
                if cell != " ":
                    preview_box[y][x] = cell

        out = ""
        for c in preview_box[j]:
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
            game.process()
            acc = 0
    
    # Handle gravity
    if acc >= gravity_interval:
        acc -= gravity_interval
        game.process()
    
    if game.is_changed:
        game.draw()
        
    time.sleep(REFRESH_RATE)
    
