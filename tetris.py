from time import sleep, perf_counter

from pieces import bag_piece_generator
from input import Input
from field import Field
from game import Game
from renderer import Renderer

GAME_FIELD_WIDTH = 10
GAME_FIELD_HEIGHT = 20
REFRESH_RATE = 0.01

key_reader = Input()
game_field = Field(GAME_FIELD_WIDTH, GAME_FIELD_HEIGHT)
game = Game(game_field, bag_piece_generator)
renderer = Renderer(GAME_FIELD_WIDTH, GAME_FIELD_HEIGHT)
game.start()

last = perf_counter()

while True:
    now = perf_counter()
    delta = now - last
    last = now
    
    action = key_reader.get_action()
    game.process(delta, action)
    
    if game.is_running:
        renderer.draw(game.snapshot)
    elif game.is_leveling_up:
        renderer.draw_message(f"LEVEL {game.level}!")
    elif game.is_game_over:
        renderer.draw_game_over(game.snapshot)
        break
    sleep(REFRESH_RATE)



