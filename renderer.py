from copy import deepcopy
from time import sleep

from output import clear_screen
from colors import Colorizer
from models import GameSnapshot


class Renderer:
    W_BORDER_CHAR = "|"
    LEVEL_LINE = 1
    SCORE_LINE = 2
    TIME_LINE = 18
    PREVIEW_BOX_START_LINE = 4
    PREVIEW_BOX_SIZE = 4
    PREVIEW_BOX_END_LINE = PREVIEW_BOX_START_LINE + PREVIEW_BOX_SIZE
        
    GHOST_CHAR = "@"
    FIG_CHAR = "@"

    def __init__(self):
        self.colorizer = Colorizer()
        self.Colors = {
            'I': self.colorizer.cyan,
            'O': self.colorizer.yellow,
            'T': self.colorizer.magenta,
            'S': self.colorizer.green,
            'Z': self.colorizer.red,
            'J': self.colorizer.blue,
            'L': self.colorizer.orange,
            'RESET': self.colorizer.reset,
        }

    # --- Public API ---
    def draw(self, snapshot: GameSnapshot):
        """Draw the whole field + sidebar."""
        clear_screen()
        temp = [row[:] for row in snapshot.field]
        self._overlay_current_piece(temp, snapshot)
        self._overlay_ghost_piece(temp, snapshot)

        self._print_horizontal_border(snapshot.width)
        for idx, row in enumerate(temp):
            new_row = [self.W_BORDER_CHAR, *row, self.W_BORDER_CHAR, *list(self._get_sidebar_line(idx, snapshot))]
            new_row = self._colorize_row(new_row)
            print(''.join(new_row))
        self._print_horizontal_border(snapshot.width)

    def draw_message(self, snapshot, text: str):
        """Center a message inside the playfield."""
        half_height = snapshot.height // 2 - 1
        padding = (snapshot.width // 2 - len(text) // 2)
        padding_left = " " * padding
        padding_right = " " * (snapshot.width - padding - len(text))

        clear_screen()
        self._print_horizontal_border(snapshot.width)
        self._print_empty_rows(half_height, snapshot.width)
        print(f'{self.W_BORDER_CHAR}{padding_left}{text}{padding_right}{self.W_BORDER_CHAR}')
        self._print_empty_rows(half_height, snapshot.width)
        self._print_horizontal_border(snapshot.width)

    def draw_game_over(self, snapshot, sleep_time=0.05):
        """
        Fill the field row by row with '#', then empty it back to the snapshot.
        Sidebar is preserved because snapshot is used for the 'emptying' phase.
        """
        temp_snapshot = deepcopy(snapshot)
        
        # FILL PHASE
        for y in reversed(range(snapshot.height)):
            temp_snapshot.field[y] = ["#"] * snapshot.width
            self.draw(temp_snapshot)
            sleep(sleep_time)

        # EMPTY PHASE (restore snapshot gradually)
        for y in range(snapshot.height):
            temp_snapshot.field[y] = snapshot.field[y][:]
            self.draw(temp_snapshot)
            sleep(sleep_time)

    # --- Internal helpers ---
    def _overlay_current_piece(self, temp, snapshot):
        for row_idx, row in enumerate(snapshot.current_piece.shape):
            for col_idx, cell in enumerate(row):
                if cell != " " and 0 <= snapshot.current_piece.y + row_idx < snapshot.height:
                    temp[snapshot.current_piece.y + row_idx][snapshot.current_piece.x + col_idx] = cell

    def _overlay_ghost_piece(self, temp, snapshot):
        for row_idx, row in enumerate(snapshot.current_piece.shape):
            for col_idx, cell in enumerate(row):
                if cell != " ":
                    gy = snapshot.ghost_y + row_idx
                    gx = snapshot.current_piece.x + col_idx
                    if 0 <= gy < snapshot.height and temp[gy][gx] == " ":
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

    def _get_sidebar_line(self, idx, snapshot):
        padding = '   '
        sidebar_map = {
            self.LEVEL_LINE: f"{padding}level: {snapshot.level}",
            self.SCORE_LINE: f"{padding}score: {snapshot.score}",
            self.TIME_LINE: f"{padding}time: {snapshot.playtime:.1f}s",
        }
        if idx in sidebar_map:
            return sidebar_map[idx]
        elif self.PREVIEW_BOX_START_LINE <= idx < self.PREVIEW_BOX_END_LINE:
            pj = idx - self.PREVIEW_BOX_START_LINE
            return f'{padding}{self._get_preview_row(pj, snapshot.next_piece)}'
        else:
            return ''

    def _get_preview_row(self, j: int, piece):
        """Return the j-th row of the preview box with the piece centered."""
        if not piece:
            return " " * self.PREVIEW_BOX_SIZE

        # top offset to center vertically
        top_padding = (self.PREVIEW_BOX_SIZE - piece.height) // 2
        # left offset to center horizontally
        left_padding = (self.PREVIEW_BOX_SIZE - piece.width) // 2

        # if j is outside the piece's vertical bounds → empty row
        if not (top_padding <= j < top_padding + piece.height):
            return " " * self.PREVIEW_BOX_SIZE

        # row inside the piece
        piece_row = piece.shape[j - top_padding]
        out = [" "] * self.PREVIEW_BOX_SIZE

        for x, cell in enumerate(piece_row):
            if cell != " " and left_padding + x < self.PREVIEW_BOX_SIZE:
                out[left_padding + x] = cell

        return "".join(out)

    def _print_empty_rows(self, times, width):
        for _ in range(times):
            print(f'{self.W_BORDER_CHAR}{" " * width}{self.W_BORDER_CHAR}')

    def _print_horizontal_border(self, width):
        print(f'+{"-" * width}+')

