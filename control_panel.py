import pygame
import sys

from blinory import Drone
from ui_colors import *
from ui_elements import Button, Slider

# Initialize Pygame
pygame.init()

# Set up the window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Drone Controller")

def stop_ui():
    global running
    running = False

drone = Drone()

# Create UI elements
buttons = [
    Button(50, 50, 120, 40, "Lift Off", GREEN, action=drone.lift_off),
    Button(200, 50, 120, 40, "Land", RED, action=drone.land),
    Button(350, 50, 200, 40, "Emergency Stop", RED, action=drone.emergency_stop),
    Button(600, 50, 120, 40, "Exit", BLUE, action=stop_ui),
]

sliders = [
    Slider(50, 200, 200, 0, 100, "Throttle", orientation='vertical',
           action=drone.control_throttle),
    Slider(150, 200, 200, -100, 100, "Pitch", orientation='vertical', init_centered=True,
           snap_back=True, action=drone.control_pitch),
    Slider(50, 450, 200, -100, 100, "Yaw", init_centered=True, snap_back=True,
           action=drone.control_yaw),
    Slider(50, 550, 200, -100, 100, "Roll", init_centered=True, snap_back=True,
           action=drone.control_roll),
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

    # Draw UI elements
    for btn in buttons:
        btn.draw(screen)

    for slider in sliders:
        slider.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()

