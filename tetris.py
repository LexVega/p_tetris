from time import sleep, perf_counter

from pieces import random_piece_generator, bag_piece_generator
from input import Input
from game import Game


key_reader = Input()
game = Game(bag_piece_generator)
game.spawn_piece()

last = perf_counter()
acc = 0.0
REFRESH_RATE = 0.01

while not game.game_over:
    now = perf_counter()
    acc += perf_counter() - last
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
    gravity_interval = game.get_gravity()
    if acc >= gravity_interval:
        acc -= gravity_interval
        game.tick_physics()
    
    if game.redraw_required:
        game.draw()
    
    sleep(REFRESH_RATE)
    
