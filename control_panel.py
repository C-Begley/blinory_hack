import cv2  #TODO: restrict? Maybe not even needed if we go through the hoop_detector?
import h264decoder  #Note: this one had to be installed manually!
                    #       https://github.com/DaWelter/h264decoder
                    #       It also proved to be a challenge on Arch, because it's semi-broken
                    #       - Manually install pyBind11 through Pacman
                    #       - Manually run the TWO Cmake commands that failed
                    #           - Note that for the second command,
                    #             it's best to drop the last arguments. (c.f.r README)
import hoop_detector
import numpy as np
import pygame
import pylwdrone
import sys

from blinory import Drone
from threading import Thread
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

KEYBOARD_PRESS_WEIGHT = 60

stream_surface = None  #Used as a way to pass the stream to a different thread
hoop_flying_enabled = False

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
    #TODO: It's still not entirely clear whether Throttle should be 0 - 100, or -125 - +125
    Slider(50, 200, 200, -100, 100, "Throttle", orientation='vertical',
           init_centered=True, snap_back=True, action=drone.set_throttle),
    Slider(150, 200, 200, -100, 100, "Pitch", orientation='vertical', init_centered=True,
           snap_back=True, action=drone.set_pitch),
    Slider(50, 450, 200, -100, 100, "Yaw", init_centered=True, snap_back=True,
           action=drone.set_yaw),
    Slider(50, 550, 200, -100, 100, "Roll", init_centered=True, snap_back=True,
           action=drone.set_roll),
]

def set_stream_surface(frame):
    global stream_surface
    frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB) # cv2 uses BGR -> Convert back to RGB for Pygame
    frame = np.rot90(frame) #Why is this suddenly necessary? Wasn't needed before?
    frame = pygame.surfarray.make_surface(frame)
    #NOTE: stream aspect ratio = 1.7777
    frame = pygame.transform.scale(frame, (500,282))
    stream_surface = frame

def process_stream():
    drone_stream = pylwdrone.LWDrone()
    #TODO: error catching for when drone was not on
    decoder = h264decoder.H264Decoder()
    hoop_detector.set_frame_dimensions((1152, 2048))
    for _frame in drone_stream.start_video_stream():
        if not running:
            break
        framedatas=decoder.decode(bytes(_frame.frame_bytes))
        for framedata in framedatas:
            (frame, w, h, ls) = framedata
            if frame is not None:
                frame = np.frombuffer(frame, dtype=np.ubyte, count=len(frame))
                frame = frame.reshape((h, ls//3, 3))
                frame = frame[:,:w,:]
                # if frame is None:
                #     print("No frame, skipping...")
                #     continue
                frame=cv2.cvtColor(frame,cv2.COLOR_RGB2BGR) # cv2 uses BGR
                frame, suggested_correction = hoop_detector.process_frame(frame)
                set_stream_surface(frame)
                if hoop_flying_enabled:
                    if suggested_correction == None:
                        print("all to 0: ")
                        drone.set_roll(0)
                        drone.set_throttle(0)
                    else:
                        print("Setting_roll: ", suggested_correction[0])
                        drone.set_roll(suggested_correction[0])
                        print("Setting_throttle: ", suggested_correction[1])
                        drone.set_throttle(suggested_correction[1])



# Main loop
running = True
current_slider = None

stream_thread = Thread(target=process_stream, args=())
stream_thread.start()


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
        #TODO: instead of relying on KEYUP and KEYDON events,
        #       I'd say it's way more reliable to just check if a key is pressed in a loop
        #       and set status based on that
        #TODO: Ideally, the sliders also reflect what's going on here.
        elif event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_SPACE:
                    drone.emergency_stop()
                case pygame.K_ESCAPE:
                    drone.emergency_stop()
                case pygame.K_r:
                    drone.set_throttle(KEYBOARD_PRESS_WEIGHT)
                    sliders[0].set_value(KEYBOARD_PRESS_WEIGHT)
                case pygame.K_f:
                    drone.set_throttle(-KEYBOARD_PRESS_WEIGHT)
                    sliders[0].set_value(-KEYBOARD_PRESS_WEIGHT)
                case pygame.K_a:
                    drone.set_roll(-KEYBOARD_PRESS_WEIGHT)
                    sliders[3].set_value(-KEYBOARD_PRESS_WEIGHT)
                case pygame.K_d:
                    drone.set_roll(KEYBOARD_PRESS_WEIGHT)
                    sliders[3].set_value(KEYBOARD_PRESS_WEIGHT)
                case pygame.K_w:
                    drone.set_pitch(KEYBOARD_PRESS_WEIGHT)
                    sliders[1].set_value(KEYBOARD_PRESS_WEIGHT)
                case pygame.K_s:
                    drone.set_pitch(-KEYBOARD_PRESS_WEIGHT)
                    sliders[1].set_value(-KEYBOARD_PRESS_WEIGHT)
                case pygame.K_q:
                    drone.set_yaw(-KEYBOARD_PRESS_WEIGHT)
                    sliders[2].set_value(-KEYBOARD_PRESS_WEIGHT)
                case pygame.K_e:
                    drone.set_yaw(KEYBOARD_PRESS_WEIGHT)
                    sliders[2].set_value(KEYBOARD_PRESS_WEIGHT)
                case pygame.K_RETURN:
                    drone.lift_off()
                case pygame.K_BACKSPACE:
                    drone.land()
                case pygame.K_h:
                    hoop_flying_enabled = not hoop_flying_enabled
                    print("Hoop flying: ", hoop_flying_enabled)
                    #TODO: shop with indicator on UI? Color changing button?
        elif event.type == pygame.KEYUP:
            match event.key:
                case pygame.K_r:
                    drone.set_throttle(0)
                    sliders[0].set_value(0)
                case pygame.K_f:
                    drone.set_throttle(0)
                    sliders[0].set_value(0)
                case pygame.K_a:
                    drone.set_roll(0)
                    sliders[3].set_value(0)
                case pygame.K_d:
                    drone.set_roll(0)
                    sliders[3].set_value(0)
                case pygame.K_w:
                    drone.set_pitch(0)
                    sliders[1].set_value(0)
                case pygame.K_s:
                    drone.set_pitch(0)
                    sliders[1].set_value(0)
                case pygame.K_q:
                    drone.set_yaw(0)
                    sliders[2].set_value(0)
                case pygame.K_e:
                    drone.set_yaw(0)
                    sliders[2].set_value(0)

    # Draw UI elements
    for btn in buttons:
        btn.draw(screen)

    for slider in sliders:
        slider.draw(screen)

    if stream_surface:
        #TODO: I'd like these coords to be better defined. Maybe relative to the UI lements.
        #       On top of that: I'd also like to have the stream in its own UI-element class.
        screen.blit(stream_surface, (275, 150))

    pygame.display.flip()

stream_thread.join()
pygame.quit()
sys.exit()

