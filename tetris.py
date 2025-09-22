from time import sleep, perf_counter

from pieces import bag_piece_generator
from input import Input
from models import GameState
from game import Game
from renderer import Renderer

GAME_FIELD_WIDTH = 10
GAME_FIELD_HEIGHT = 20

key_reader = Input()
game = Game(GAME_FIELD_WIDTH, GAME_FIELD_HEIGHT, bag_piece_generator)
renderer = Renderer()

game.spawn_piece()

last = perf_counter()
acc = 0.0
REFRESH_RATE = 0.01

while True:
    now = perf_counter()
    acc += now - last
    last = now

    if game.is_running:
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
    
    elif game.is_leveling_up:
        if perf_counter() - game.state_timer < 0.5:
            renderer.draw_message(game.snapshot, f"LEVEL {game.level}!")
            sleep(REFRESH_RATE)
            continue
        else:
            game.state = GameState.RUNNING
            acc = 0.0

    elif game.is_game_over:
        renderer.draw_game_over(game.snapshot)
        break

    renderer.draw(game.snapshot)
    sleep(REFRESH_RATE)

