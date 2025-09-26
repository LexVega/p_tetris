from pieces import Piece
from snapshot import FieldSnapshot


class Field:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[" "] * self.width for _ in range(self.height)]
        
    def merge(self, piece: Piece):
        for row_idx, row in enumerate(piece.shape):
            for col_idx, cell in enumerate(row):
                if cell == ' ': continue
                board_y = piece.y + row_idx
                board_x = piece.x + col_idx
                
                # Only write into actual visible grid cells.
                if 0 <= board_y < self.height and 0 <= board_x < self.width:
                    self.grid[board_y][board_x] = cell
    
    def clear_lines(self):
        new_field = [row for row in self.grid if any(c == " " for c in row)]
        cleared_lines = self.height - len(new_field)
        self.grid = [[' '] * self.width for _ in range(cleared_lines)] + new_field
        return cleared_lines
    
    def can_place(self, piece: Piece, dx=0, dy=0):
        """Check if `piece` can be placed at (x+dx, y+dy)."""
    
        for row_idx, row in enumerate(piece.shape):
            for col_idx, cell in enumerate(row):
                if cell == ' ': continue
                board_x = piece.x + col_idx + dx
                board_y = piece.y + row_idx + dy
                if board_x < 0 or board_x >= self.width or board_y >= self.height:
                    return False
                if board_y >= 0 and self.grid[board_y][board_x] != ' ':
                    return False
        return True
    
    @property
    def snapshot(self):
        return FieldSnapshot(
            width = self.width,
            height = self.height,
            grid = [row[:] for row in self.grid],
        )
