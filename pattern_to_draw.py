import led_drawning as LD

def draw(drone):
    led_draw = LD.led_drawer(drone)
    # #Example drawning of R
    led_draw.move(LD.Direction.UP, 1)
    led_draw.move(LD.Direction.LEFT, 1)
    led_draw.move(LD.Direction.DOWN, 1)
    led_draw.move(LD.Direction.RIGHT, 3)
    led_draw.move_and_bank(LD.Direction.DOWN, 1, LD.Direction.LEFT, 1)
    
    # #Draw an O
    # led_draw.move(LD.Direction.UP, 1)
    # led_draw.move(LD.Direction.RIGHT, 3)
    # led_draw.move(LD.Direction.DOWN, 2)
    # led_draw.move(LD.Direction.LEFT, 1)
    # Code for writing G O R D W

    # Busy with G: Moving drone to turn LED OFF
    # led_draw.move(LD.Direction.YAW, 4)
    # # # Busy with G: 
    # led_draw.move_and_bank(LD.Direction.UP, 1.2, LD.Direction.RIGHT, 1.5)
    # Busy with G: Moving drone to turn LED ON
    # led_draw.move(LD.Direction.YAW, 4)
    # Busy with G: 
    # led_draw.move(LD.Direction.RIGHT, 3)
    # # Busy with G: 
    # led_draw.move(LD.Direction.DOWN, 4.8)
    # # Busy with G: 
    # led_draw.move(LD.Direction.LEFT, 2)
    # # Busy with G: 
    # led_draw.move(LD.Direction.UP, 1)
    # # Busy with G: 
    # led_draw.move(LD.Direction.RIGHT, 1.5)
    # # Busy with G-O spacing: Moving drone to turn LED OFF
    # led_draw.move(LD.Direction.YAW, 4)
    # # Busy with G-O spacing: 
    # led_draw.move_and_bank(LD.Direction.DOWN, 2, LD.Direction.RIGHT, 3.75)
    # Busy with O: Moving drone to turn LED ON
    # led_draw.move(LD.Direction.YAW, 4)
    # # Busy with O: 
    # led_draw.move(LD.Direction.UP, 2.4)
    # # Busy with O: 
    # led_draw.move(LD.Direction.LEFT, 2)
    # # Busy with O: 
    # led_draw.move(LD.Direction.DOWN, 4.8)
    # # Busy with O: 
    # led_draw.move(LD.Direction.RIGHT, 3)
    # # Busy with O-R spacing: Moving drone to turn LED OFF
    # led_draw.move(LD.Direction.YAW, 4)
    # # Busy with O-R spacing: 
    # led_draw.move(LD.Direction.RIGHT, 7.5)
    # # Busy with R: Moving drone to turn LED ON
    # led_draw.move(LD.Direction.YAW, 4)
    # # Busy with R: 
    led_draw.move(LD.Direction.UP, 2.4)
    # Busy with R: 
    led_draw.move(LD.Direction.LEFT, 2)
    # Busy with R: 
    led_draw.move(LD.Direction.DOWN, 2.4)
    # Busy with R: 
    led_draw.move(LD.Direction.RIGHT, 3)
    # Busy with R: 
    # led_draw.move_and_bank(LD.Direction.DOWN, 2.4, LD.Direction.LEFT, 2)
    # # Busy with R-D spacing: Moving drone to turn LED OFF
    # led_draw.move(LD.Direction.YAW, 4)
    # # Busy with R-D spacing: 
    # led_draw.move(LD.Direction.RIGHT, 2.25)
    # # Busy with D: Moving drone to turn LED ON
    # led_draw.move(LD.Direction.YAW, 4)
    # Busy with D: 
    # led_draw.move(LD.Direction.UP, 2)
    # # Busy with D: 
    # led_draw.move(LD.Direction.LEFT, 1)
    # # Busy with D: 
    # led_draw.move_and_bank(LD.Direction.DOWN, 2.4, LD.Direction.LEFT, 1)
    # # Busy with D: 
    # led_draw.move_and_bank(LD.Direction.DOWN, 2.4, LD.Direction.RIGHT, 1.5)
    # # Busy with D: 
    # led_draw.move(LD.Direction.RIGHT, 1.5)
    # # Busy with D-W spacing: Moving drone to turn LED OFF
    # led_draw.move(LD.Direction.YAW, 4)
    # # Busy with D-W spacing: 
    # led_draw.move_and_bank(LD.Direction.UP, 2.4, LD.Direction.RIGHT, 5.25)
    # # Busy with W: Moving drone to turn LED ON
    # led_draw.move(LD.Direction.YAW, 16)
    # Busy with W: 
    # led_draw.move(LD.Direction.DOWN, 4.8)
    # # Busy with W: 
    # led_draw.move_and_bank(LD.Direction.UP, 1.2, LD.Direction.LEFT, 1)
    # # Busy with W: 
    # led_draw.move_and_bank(LD.Direction.DOWN, 2.4, LD.Direction.LEFT, 1)
    # # Busy with W: 
    # led_draw.move(LD.Direction.UP, 2.4)
    # # Busy with W: Moving drone to turn LED OFF
    # led_draw.move(LD.Direction.YAW, 4, speed=50)


def draw_from_thread(args):
    d_arg = args
    draw(d_arg)
