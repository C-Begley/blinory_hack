import csv
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

# Initialize Pygame here, because otherwise you can't use fonts in libs... (stupid design imho..)
pygame.init()

from argparse import ArgumentParser
from auto_connect import auto_connect
from blinory import Drone
from prefixed import Float
from threading import Thread, Lock
from time import sleep, time
from ui_colors import *
from ui_elements import Button, Slider, Ticker

#TODO: add one try-catch around entire program that will send an emergency stop before crashing?
#TODO: Ideally we also do a continuous ping to check if the drone is still connected. Because
#       right not it can happen that we don't get a video feed anymore, but still keep running the
#       algorithm

# Set up the window
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Drone Controller")

PRINT_LOOPTIME = False  #Can be used to measure the time one full iteration takes

stream_surface = None  #Used as a way to pass the stream to a different thread
hoop_flying_enabled = False

# We will store the frame globally to share it between threads
last_frame = None
last_frame_lock = Lock()

def parse_args():
    parser = ArgumentParser(
                    prog='Control panel',
                    description='RDW Drone Challenge Control Panel')
    parser.add_argument('--no_connect', action='store_true')
    return parser.parse_args()

def exit():
    global running
    drone.deactivate()
    running = False

def drone_land():
    hoop_flying_enabled = False
    drone.land()

def drone_emergency_stop():
    hoop_flying_enabled = False
    drone.emergency_stop()

drone = Drone()

# Create UI elements
buttons = [
    Button(50, 50, 120, 40, "Lift Off", GREEN, action=drone.lift_off),
    Button(200, 50, 120, 40, "Land", RED, action=drone_land),
    Button(350, 50, 200, 40, "Emergency Stop", RED, action=drone_emergency_stop),
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

#TODO: convert the other UI-lists to dicts as well. Will make it much easier in the long run
tickers = {
        "roll":         Ticker(220, 100, -10, 10, 1.2, label_text="×Roll:", step=0.1),
        "throttle":     Ticker(420, 100, -10, 10, 1.2, label_text="×Throttle:", step=0.1),
        "pitch":        Ticker(220, 150, 0, 100, 10, label_text="vPitch:", step=0.1),
        "fwdthresh":    Ticker(420, 150, 0, 50, 0, label_text="ΔThr", step=5),
        "pitch_v_corr": Ticker(620, 150, 0, 10, 0, label_text="↕Pitch", step=0.5),

        "manual_roll_speed":        Ticker(50, 600, 20, 100, 50, label_text="MvRoll", step=10),
        "manual_pitch_speed":       Ticker(250, 600, 20, 100, 50, label_text="MvPitch", step=10),
        "manual_throttle_speed":    Ticker(450, 600, 20, 100, 50, label_text="MvThrottle", step=10),
        "manual_yaw_speed":         Ticker(670, 600, 20, 100, 50, label_text="MvYaw", step=10),

        "smoothing":         Ticker(50, 650, 0, 1, 0.5, label_text="Smoothing", step=0.1),
}

def set_stream_surface(frame):
    global stream_surface
    frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB) # cv2 uses BGR -> Convert back to RGB for Pygame
    frame = np.rot90(frame) #Why is this suddenly necessary? Wasn't needed before?
    frame = pygame.surfarray.make_surface(frame)
    #NOTE: stream aspect ratio = 1.7777
    frame = pygame.transform.scale(frame, (700,394))
    stream_surface = frame

# alpha: smoothing strength. Range: 0-1
# theta: dynamic adjustment of alpha. Used when the prediction is uncertain.
#        Range: 0-1: 1 = take fully into consideration, 0 = ignore this value
def smoothen_correction(avcor, sugcor, alpha=0.1, theta=1):
    assert 0 < alpha < 1
    if alpha == 1:
        alpha = alpha*0.95  #Otherwise there's no actual data used at all...

    alpha = alpha*theta

    avcor0 = alpha * avcor[0] + (1 - alpha) * sugcor[0]
    avcor1 = alpha * avcor[1] + (1 - alpha) * sugcor[1]

    return (avcor0, avcor1)

def hoop_flying():
    # global last_frame
    global last_frame_lock
    prev_correct_cmd = False    # True means that we have sent out a correction to the drone
    avcor = (0,0)   #Moving average for corrections
    csvfile = open('corrections.csv', 'w')
    csvwriter = csv.writer(csvfile)
    while running:
        if not hoop_flying_enabled:
            sleep(0.2)
            continue
        with last_frame_lock:
            frame = last_frame
        if frame is None:
            sleep(0.5)
            continue
        frame, suggested_correction, certainty = hoop_detector.process_frame(frame)
        set_stream_surface(frame)
        if suggested_correction == None and prev_correct_cmd:
            print("all to 0: ")
            drone.set_roll(0)
            drone.set_throttle(0)
            prev_correct_cmd = False
            csvwriter.writerow([time(),0,0,0,0])
        else:
            if suggested_correction \
              and suggested_correction[0] \
              and suggested_correction[1]:
                match(certainty):
                    case hoop_detector.PredictionCertainty.CERTAIN:
                        theta = 1
                    case hoop_detector.PredictionCertainty.RELIABLE:
                        theta = 0.75
                    case hoop_detector.PredictionCertainty.RELIABLE:
                        theta = 0.5
                    case hoop_detector.PredictionCertainty.DIRECTION_GUESS:
                        theta = 0.3
                    case hoop_detector.PredictionCertainty.NOISY_PREDICTION:
                        theta = 0.1
                avcor = smoothen_correction(avcor,
                                            suggested_correction,
                                            tickers['smoothing'].value, theta=theta)
                #TODO: show these on CP instead of printing
                # print("Setting_roll: ",
                #       avcor[0]*tickers['roll'].value)
                drone.set_roll(avcor[0]*tickers['roll'].value)
                # print("Setting_throttle: ",
                #       avcor[1]*tickers['throttle'].value)
                drone.set_throttle(avcor[1]*tickers['throttle'].value)
                prev_correct_cmd = True
                #Determine if we're confident enough to fly through
                #TODO: I think ideally the threshold should be a function of the distance to the hoop.
                #NOTE: This doesn't take into account the corrections for pitch. That's okay for now.
                csvwriter.writerow([time(),
                                    suggested_correction[0],
                                    suggested_correction[1],
                                    avcor[0],
                                    avcor[1],
                                    tickers['smoothing']])
                if avcor[0] < tickers["fwdthresh"].value \
                  and avcor[1] < tickers["fwdthresh"].value:
                    print("Okay, we're close enough... let's go forward!")
                    drone.set_pitch(tickers["pitch"].value)
                    # Reduce correction on vertical axis due to camera going down
                    drone.set_throttle(avcor[1]
                                       * tickers["throttle"].value
                                       / (ticker["pitch_v_corr"]+1))
                else:
                    drone.set_pitch(0)




def process_stream():
    drone_stream = pylwdrone.LWDrone()
    #TODO: heartbeat?
    #TODO: error catching for when drone was not on
    #TODO: sometimes it fails to get the video stream the first time.
    #       Maybe we should add some retry mechanism here for that?
    #       Or maybe a simple sleep of a second or two will do?
    global last_frame
    decoder = h264decoder.H264Decoder()
    hoop_detector.set_frame_dimensions((1152, 2048))
    for _frame in drone_stream.start_video_stream():
        if not running:
            break
        start = time()
        framedatas=decoder.decode(bytes(_frame.frame_bytes))
        for framedata in framedatas:
            (frame, w, h, ls) = framedata
            if frame is not None:
                frame = np.frombuffer(frame, dtype=np.ubyte, count=len(frame))
                frame = frame.reshape((h, ls//3, 3))
                frame = frame[:,:w,:]
                frame=cv2.cvtColor(frame,cv2.COLOR_RGB2BGR) # cv2 uses BGR
                with last_frame_lock:
                    last_frame = frame
                if not hoop_flying_enabled:
                    set_stream_surface(frame)
        if PRINT_LOOPTIME:
            print(f"Elapsed time for full run: {Float(time() - start):.2h}s")


args = parse_args()

# Main loop
running = True
current_slider = None

if not args.no_connect:
    if auto_connect() < 0:  #TODO: maybe make this one configurable? On/Off?
        print("Error connecting to drone. Was it on?")
        exit(1)
    sleep(1)

    stream_thread = Thread(target=process_stream, args=())
    stream_thread.start()

    hoop_fly_thread = Thread(target=hoop_flying, args=())
    hoop_fly_thread.start()


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

            for ticker in tickers.values():
                ticker.handle_event(event)
                #TODO: try to convert the other elements to also use this way of
                #       event handling. It's much cleaner.

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
                    drone_emergency_stop()
                case pygame.K_ESCAPE:
                    drone_emergency_stop()
                case pygame.K_r:
                    drone.set_throttle(tickers['manual_throttle_speed'].value)
                    sliders[0].set_value(tickers['manual_throttle_speed'].value)
                case pygame.K_f:
                    drone.set_throttle(-tickers['manual_throttle_speed'].value)
                    sliders[0].set_value(-tickers['manual_throttle_speed'].value)
                case pygame.K_a:
                    drone.set_roll(-tickers['manual_roll_speed'].value)
                    sliders[3].set_value(-tickers['manual_roll_speed'].value)
                case pygame.K_d:
                    drone.set_roll(tickers['manual_roll_speed'].value)
                    sliders[3].set_value(tickers['manual_roll_speed'].value)
                case pygame.K_w:
                    drone.set_pitch(tickers['manual_pitch_speed'].value)
                    sliders[1].set_value(tickers['manual_pitch_speed'].value)
                case pygame.K_s:
                    drone.set_pitch(-tickers['manual_pitch_speed'].value)
                    sliders[1].set_value(-tickers['manual_pitch_speed'].value)
                case pygame.K_q:
                    drone.set_yaw(-tickers['manual_yaw_speed'].value)
                    sliders[2].set_value(-tickers['manual_yaw_speed'].value)
                case pygame.K_e:
                    drone.set_yaw(tickers['manual_yaw_speed'].value)
                    sliders[2].set_value(tickers['manual_yaw_speed'].value)
                case pygame.K_RETURN:
                    drone.lift_off()
                case pygame.K_BACKSPACE:
                    drone_land()
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

    for ticker in tickers.values():
        ticker.draw(screen)

    if stream_surface:
        #TODO: I'd like these coords to be better defined. Maybe relative to the UI lements.
        #       On top of that: I'd also like to have the stream in its own UI-element class.
        screen.blit(stream_surface, (275, 200))

    pygame.display.flip()

if not args.no_connect:
    stream_thread.join()
    hoop_fly_thread.join()
pygame.quit()
sys.exit()

