from copy import deepcopy
from time import sleep

from output import clear_screen
from colors import Colorizer
from pieces import Piece, PieceType
from snapshot import GameSnapshot, FieldSnapshot


class Renderer:
    MSG_PADDING_CHAR = ' '
    W_BORDER_CHAR = "|"
    LEVEL_LINE = 1
    SCORE_LINE = 2
    TIME_LINE = 18
    PREVIEW_BOX_START_LINE = 4
    PREVIEW_BOX_SIZE = 4
    PREVIEW_BOX_END_LINE = PREVIEW_BOX_START_LINE + PREVIEW_BOX_SIZE
        
    GHOST_CHAR = "@"
    BLOCK_CHAR = "@"

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.colorizer = Colorizer()
        self.Colors = {
            PieceType.I.value: self.colorizer.cyan,
            PieceType.O.value: self.colorizer.yellow,
            PieceType.T.value: self.colorizer.magenta,
            PieceType.S.value: self.colorizer.green,
            PieceType.Z.value: self.colorizer.red,
            PieceType.J.value: self.colorizer.blue,
            PieceType.L.value: self.colorizer.orange,
        }
        self.chars = {
            piece_type: f'{color}{self.BLOCK_CHAR}{self.colorizer.reset}' for piece_type, color in self.Colors.items()
        }
    
    @property
    def half_height(self):
        return self.height // 2
    
    # --- Public API ---   
    def draw(self, snapshot: GameSnapshot):
        """Draw the whole field + sidebar."""
        field_representation = self._get_field_representation(snapshot.field.grid)
        
        if snapshot.current_piece:
            for row_idx, row in enumerate(snapshot.current_piece.shape):
                for col_idx, cell in enumerate(row):
                    if cell:
                        # overlay ghost piece first
                        gx = snapshot.current_piece.x + col_idx
                        gy = snapshot.ghost_y + row_idx
                        if 0 <= gy < self.height and 0 <= gx < self.width:
                            field_representation[gy][gx] = self._get_cell_representation(cell, is_ghost=True)
                        
                        # overlay current piece (on top of ghost if overlap)
                        x = snapshot.current_piece.x + col_idx
                        y = snapshot.current_piece.y + row_idx
                        if 0 <= y < self.height and 0 <= x < self.width:
                            field_representation[y][x] = self._get_cell_representation(cell)
        
        self._print_field(field_representation, snapshot)

    def draw_message(self, text: str):
        """Center a message inside the playfield."""
        clear_screen()
        self._print_horizontal_border()
        self._print_empty_rows(self.half_height - 1, self.width)
        self._print_msg(text)
        self._print_empty_rows(self.half_height - 1, self.width)
        self._print_horizontal_border()

    def draw_game_over(self, snapshot, sleep_time=0.05):
        """
        Fill the field row by row with '#', then empty it back to the snapshot.
        Sidebar is preserved because snapshot is used for the 'emptying' phase.
        """
        field_representation = self._get_field_representation(snapshot.field.grid)
        old_field = []
        
        # FILL PHASE
        for y in reversed(range(self.height)):
            old_field.insert(0, field_representation[y])
            field_representation[y] = ["#"] * self.width
            self._print_field(field_representation, snapshot)
            sleep(sleep_time)

        # EMPTY PHASE (restore snapshot gradually)
        for y in range(self.height):
            field_representation[y] = old_field[y][:]
            self._print_field(field_representation, snapshot)
            sleep(sleep_time)

    # --- Internal helpers ---
    def _get_field_representation(self, field_grid: list[list[int]]) -> list[list[str]]:
        return [
            [self._get_cell_representation(cell) for cell in row]
            for row in field_grid
        ]
    
    def _get_cell_representation(self, cell: int, is_ghost=False) -> str:
        if is_ghost:
            # just white ghost char with no coloring
            return self.GHOST_CHAR
        else:
            # block char with pre-applied color or empty space
            return self.chars.get(cell, ' ')
    
    def _print_field(self, field_representation: list[list[str]], snapshot: GameSnapshot | None = None):
        clear_screen()
        
        self._print_horizontal_border()
        if snapshot: # need to render sidebar
            for row_idx, row in enumerate(field_representation):
                print(f'{self.W_BORDER_CHAR}{"".join(row)}{self.W_BORDER_CHAR}{self._get_sidebar_line(row_idx, snapshot)}')
        else: # just render field
            for row in field_representation:
                print(f'{self.W_BORDER_CHAR}{"".join(row)}{self.W_BORDER_CHAR}')
        self._print_horizontal_border()
        
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

    def _get_preview_row(self, j: int, piece: Piece | None):
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
            if cell and left_padding + x < self.PREVIEW_BOX_SIZE:
                out[left_padding + x] = self._get_cell_representation(cell)

        return "".join(out)

    def _print_empty_rows(self, times, width):
        for _ in range(times):
            print(f'{self.W_BORDER_CHAR}{" " * width}{self.W_BORDER_CHAR}')

    def _print_horizontal_border(self):
        print(f'+{"-" * self.width}+')
    
    def _print_msg(self, msg: str):
        padding = (self.width // 2 - len(msg) // 2)
        padding_left = self.MSG_PADDING_CHAR * padding
        padding_right = self.MSG_PADDING_CHAR * (self.width - padding - len(msg))
        
        print(f'{self.W_BORDER_CHAR}{padding_left}{msg}{padding_right}{self.W_BORDER_CHAR}')

