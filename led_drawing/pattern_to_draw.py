from led_drawning import Direction as D
from led_drawing import led_drawer as LD

def draw(drone):
    led_drawer = LD.led_drawer(drone)
    #Example drawning of R
    #Change code here to whatever pattern you want to draw
    led_drawer.move(D.UP, 4)
    led_drawer.move(D.RIGHT, 2)
    led_drawer.move(D.DOWN, 2)
    led_drawer.move(D.LEFT, 2)
    led_drawer.move_and_bank(D.DOWN, D.RIGHT, 2)


def draw_from_thread(args):
    drone = args[0]
    draw(drone)
