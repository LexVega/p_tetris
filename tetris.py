from time import sleep, perf_counter

from pieces import random_piece_generator, bag_piece_generator
from input import Input
from game import Game, GameState


key_reader = Input()
game = Game(bag_piece_generator)
game.spawn_piece()

last = perf_counter()
acc = 0.0
REFRESH_RATE = 0.01

while True:
    now = perf_counter()
    acc += now - last
    last = now

    # --- Handle game states ---
    if game.state == GameState.LEVEL_UP:
        if perf_counter() - game.state_timer < 0.5:
            game.draw_message(f"LEVEL {game.level}!")
            sleep(REFRESH_RATE)
            continue
        else:
            game.state = GameState.RUNNING
            acc = 0.0

    if game.state == GameState.GAME_OVER:
        original_field = [row[:] for row in game.field]  # save current state
        
        # FILL PHASE (bottom → top)
        for y in reversed(range(game.HEIGHT)):
            game.field[y] = ["#"] * game.WIDTH
            game.draw()
            sleep(0.05)

        # EMPTY PHASE (top → bottom)
        for y in range(game.HEIGHT):
            game.field[y] = original_field[y]
            game.draw()
            sleep(0.05)

        print("GAME OVER")
        break

    # --- Handle input only when RUNNING ---
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

