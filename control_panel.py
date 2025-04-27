import pygame
import sys

from blinory import Drone
from ui_colors import *
from ui_elements import Button, Slider

#TODO: add one try-catch around entire program that will send an emergency stop before crashing?

# Initialize Pygame
pygame.init()

# Set up the window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Drone Controller")

def drone_throttle(val):
    #TODO: Which one is it? How does it work?
    # drone.control_throttle(int(val*2.55))
    drone.control_throttle(int(val+125))

def drone_pitch(val):
    drone.control_pitch(int(val+125))

def drone_roll(val):
    drone.control_roll(int(val+125))

def drone_yaw(val):
    drone.control_yaw(int(val+125))

def exit():
    global running
    drone.deactivate()
    running = False

drone = Drone()

# Create UI elements
buttons = [
    Button(50, 50, 120, 40, "Lift Off", GREEN, action=drone.lift_off),
    Button(200, 50, 120, 40, "Land", RED, action=drone.land),
    Button(350, 50, 200, 40, "Emergency Stop", RED, action=drone.emergency_stop),
    Button(600, 50, 120, 40, "Exit", BLUE, action=exit),
    Button(50, 100, 120, 40, "Activate", GREEN, action=drone.activate),
]

sliders = [
    Slider(50, 200, 200, -100, 100, "Throttle", orientation='vertical',
           init_centered=True, snap_back=True, action=drone_throttle),
    Slider(150, 200, 200, -100, 100, "Pitch", orientation='vertical', init_centered=True,
           snap_back=True, action=drone_pitch),
    Slider(50, 450, 200, -100, 100, "Yaw", init_centered=True, snap_back=True,
           action=drone_yaw),
    Slider(50, 550, 200, -100, 100, "Roll", init_centered=True, snap_back=True,
           action=drone_roll),
]


# Main loop
running = True
current_slider = None

while running:
    screen.fill(WHITE)

    #TODO: I'm more of a fan of doing the event handling INSIDE of the UI element classes.
    #       E.g. have an "on_click()" method that calls the action.
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check buttons
            for btn in buttons:
                if btn.rect.collidepoint(event.pos):
                    print(f"Button pressed: {btn.text}")
                    btn.do_action()

            # Check sliders
            for slider in sliders:
                if slider.handle_rect.collidepoint(event.pos):
                    current_slider = slider
                    slider.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if current_slider:
                if current_slider.snap_back:
                    current_slider.reset_to_initial()
                current_slider.dragging = False
                current_slider = None

        elif event.type == pygame.MOUSEMOTION:
            if current_slider and current_slider.dragging:
                current_slider.update_value(event.pos)
                # Add real-time controls here
                current_slider.do_action()
        elif event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_SPACE:
                    drone.emergency_stop()
                case pygame.K_ESCAPE:
                    drone.emergency_stop()
                case pygame.K_r:
                    drone_throttle(20)
                case pygame.K_f:
                    drone_throttle(-20)
                case pygame.K_a:
                    drone_roll(-20)
                case pygame.K_d:
                    drone_roll(20)
                case pygame.K_w:
                    drone_pitch(-20)
                case pygame.K_s:
                    drone_pitch(20)
                case pygame.K_q:
                    drone_yaw(-20)
                case pygame.K_e:
                    drone_yaw(20)
                case pygame.K_RETURN:
                    drone.lift_off()
                case pygame.K_BACKSPACE:
                    drone.land()

    # Draw UI elements
    for btn in buttons:
        btn.draw(screen)

    for slider in sliders:
        slider.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()

