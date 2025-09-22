from time import perf_counter

from models import GameModel, GameState
from pieces import Piece


class Game(GameModel):     
    def update_level(self):
        new_level = 1 + self.cleared_lines // self.LEVEL_UP_EVERY_X_LINES
        if new_level > self.level:
            self.level = new_level
            self.state = GameState.LEVEL_UP
            self.state_timer = perf_counter()
    
    def spawn_piece(self):
        self.current_piece = self.next_piece or next(self.piece_gen)
        self.current_piece.x, self.current_piece.y = self.spawning_pos
        self.next_piece = next(self.piece_gen)
        
        if not self.can_move(1, 1):
            self.state = GameState.GAME_OVER
            self.state_timer = perf_counter()
    
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
                    if board_x < 0 or board_x >= self.width or board_y >= self.height:
                        return False
                    if board_y >= 0 and self.field[board_y][board_x] != ' ':
                        return False
        return True
    
    def get_gravity(self):
        return max(self.MIN_GRAVITY, self.MAX_GRAVITY - (self.level -1) * 0.02)
    
    def move(self, x: int = 0, y: int = 0):
        if self.current_piece and (x or y):
            self.current_piece.x += x
            self.current_piece.y += y
            self.redraw_required = True
    
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
    
