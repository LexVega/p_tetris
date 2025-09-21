from time import sleep, perf_counter

from pieces import random_piece_generator, bag_piece_generator
from input import Input
from game import Game, GameState

GAME_FIELD_WIDTH = 10
GAME_FIELD_HEIGHT = 20

key_reader = Input()
game = Game(GAME_FIELD_WIDTH, GAME_FIELD_HEIGHT, bag_piece_generator)
game.spawn_piece()

last = perf_counter()
acc = 0.0
REFRESH_RATE = 0.01

while True:
    now = perf_counter()
    acc += now - last
    last = now

    # --- Handle game states ---
    if game.is_leveling_up:
        if perf_counter() - game.state_timer < 0.5:
            game.draw_message(f"LEVEL {game.level}!")
            sleep(REFRESH_RATE)
            continue
        else:
            game.state = GameState.RUNNING
            acc = 0.0

    elif game.is_game_over:
        original_field = [row[:] for row in game.field]  # save current state
        
        # FILL PHASE (bottom → top)
        for y in reversed(range(GAME_FIELD_HEIGHT)):
            game.field[y] = ["#"] * game.WIDTH
            game.draw()
            sleep(0.05)

        # EMPTY PHASE (top → bottom)
        for y in range(GAME_FIELD_HEIGHT):
            game.field[y] = original_field[y]
            game.draw()
            sleep(0.05)
        break
    
    elif game.is_running:
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

        # --- Gravity ---
        gravity_interval = game.get_gravity()
        if acc >= gravity_interval:
            acc -= gravity_interval
            game.tick_physics()

    # --- Redraw ---
    if game.redraw_required:
        game.draw()

    sleep(REFRESH_RATE)

