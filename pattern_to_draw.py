import led_drawning as LD

def draw(drone):
    led_draw = LD.led_drawer(drone)
    #Example drawning of R
    #Change code here to whatever pattern you want to draw
    # led_drawer.move(D.UP, 4)
    # led_drawer.move(D.RIGHT, 2)
    # led_drawer.move(D.DOWN, 2)
    # led_drawer.move(D.LEFT, 2)
    # led_drawer.move_and_bank(D.DOWN, D.RIGHT, 2)
    # Busy with O: 
    led_draw.move(LD.Direction.UP, 1)
    # Busy with O: 
    led_draw.move(LD.Direction.RIGHT, 3, speed=50)
    # Busy with O: 
    led_draw.move(LD.Direction.DOWN, 1)
    # Busy with O: 
    led_draw.move(LD.Direction.LEFT, 3, speed=50)

def draw_from_thread(args):
    d_arg = args
    draw(d_arg)
