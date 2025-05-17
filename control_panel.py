import cv2  #TODO: restrict? Maybe not even needed if we go through the hoop_detector?
from enum import Enum
import h264decoder  #Note: this one had to be installed manually!
                    #       https://github.com/DaWelter/h264decoder
                    #       It also proved to be a challenge on Arch, because it's semi-broken
                    #       - Manually install pyBind11 through Pacman
                    #       - Manually run the TWO Cmake commands that failed
                    #           - Note that for the second command,
                    #             it's best to drop the last arguments. (c.f.r README)
import hoop_detector
from hoop_detector import HOOP_COLOR
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
last_hoop_detector_frame = None
last_hoop_detector_frame_lock = Lock()


running = True

class HoopFlyState(Enum):
    NONE = 0,
    LOCK = 1,
    LOCK_FWD = 2,
    YOLO_FWD = 3,
    BRAKE = 4,
    END = 5

hoop_fly_state = HoopFlyState.NONE
current_hoop_color = HOOP_COLOR.RED
start_yolo_time = -1
start_brake_time = -1

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

def drone_set_throttle(val):
    val += tickers["cThrottle"].value
    # print("Setting_throttle: ", val)
    drone.set_throttle(val)
    sliders[0].set_value(val)

def drone_set_pitch(val):
    val += tickers["cPitch"].value
    # print("Setting_pitch: ", val)
    drone.set_pitch(val)
    sliders[1].set_value(val)

def drone_set_roll(val):
    val += tickers["cRoll"].value
    # print("Setting_roll: ", val)
    drone.set_roll(val)
    sliders[3].set_value(val)

def drone_set_yaw(val):
    val += tickers["cYaw"].value
    # print("Setting_yaw: ", val)
    drone.set_yaw(val)
    sliders[2].set_value(val)

drone = Drone()

# Create UI elements
buttons = [
    Button(50, 50, 120, 40, "Lift Off", GREEN, action=drone.lift_off),
    Button(200, 50, 120, 40, "Land", RED, action=drone_land),
    Button(350, 50, 200, 40, "Emergency Stop", RED, action=drone_emergency_stop),
    Button(600, 50, 120, 40, "Exit", BLUE, action=exit),
    Button(750, 50, 120, 40, "??", YELLOW, action=drone.mystery_command),
    Button(50, 100, 120, 40, "Activate", GREEN, action=drone.activate),
]

sliders = [
    #TODO: It's still not entirely clear whether Throttle should be 0 - 100, or -125 - +125
    Slider(50, 200, 200, -100, 100, "Throttle", orientation='vertical',
           init_centered=True, snap_back=True, action=drone_set_throttle),
    Slider(150, 200, 200, -100, 100, "Pitch", orientation='vertical', init_centered=True,
           snap_back=True, action=drone_set_pitch),
    Slider(50, 450, 200, -100, 100, "Yaw", init_centered=True, snap_back=True,
           action=drone_set_yaw),
    Slider(50, 550, 200, -100, 100, "Roll", init_centered=True, snap_back=True,
           action=drone_set_roll),
]

#TODO: convert the other UI-lists to dicts as well. Will make it much easier in the long run
tickers = {
        # Hoop fly aggressiveness
        "roll":         Ticker(220, 100, -10, 10, 0.9, label_text="×Roll:", step=0.1),
        "throttle":     Ticker(420, 100, -10, 10, 0.7, label_text="×Throttle:", step=0.1),
        "pitch":        Ticker(620, 100, 0, 100, 20, label_text="vPitch:", step=5),
        # Threshold before moving forward
        #TODO: calibrate
        "fwdthresh":    Ticker(220, 150, 0, 100, 7, label_text="ΔThr", step=2),
        # Correct camera movement when pitching forward
        #TODO: calibrate
        "pitch_v_corr": Ticker(370, 150, 0, 10, 0, label_text="↕Pitch", step=0.5),
        # Distance before YOLO state
        "thr_yolo": Ticker(570, 150, 0, 10, 1.5, label_text="ThrYolo", step=0.5),
        # Yolo forward speed
        "vPitch_yolo": Ticker(770, 150, 0, 100, 50, label_text="vPitchYolo", step=5),

        # Manual flying speeds
        "manual_roll_speed":        Ticker(50, 600, 20, 100, 50, label_text="MvRoll", step=10),
        "manual_pitch_speed":       Ticker(250, 600, 20, 100, 50, label_text="MvPitch", step=10),
        "manual_throttle_speed":    Ticker(450, 600, 20, 100, 50, label_text="MvThrottle", step=10),
        "manual_yaw_speed":         Ticker(670, 600, 20, 100, 50, label_text="MvYaw", step=10),

        # Smoothing factor for hoop flying corrections
        "smoothing":         Ticker(50, 650, 0, 50, 10, label_text="Smoothing", step=1),

        # Manual offsets applied to ALL commands sent. (To compensate for e.g. bad props)
        "cRoll":        Ticker(50, 700, -100, 100, 20, label_text="cRoll", step=5),
        "cPitch":       Ticker(250, 700, -100, 100, 0, label_text="cPitch", step=5),
        "cYaw":         Ticker(450, 700, -100, 100, 3, label_text="cYaw", step=1),
        "cThrottle":    Ticker(650, 700, -100, 100, 0, label_text="cThrottle", step=5),
}

def blit_stream(screen):
    global stream_surface
    if hoop_flying_enabled:
        frame = last_hoop_detector_frame
    else:
        frame = last_frame
    if frame is None:
        return
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB) # cv2 uses BGR -> Convert back to RGB for Pygame
    frame = np.rot90(frame) #Why is this suddenly necessary? Wasn't needed before?
    # For some reason the image feed was mirrored. Fixed it here.
    # HOWEVER! This is under the assumption that the hoop detector still gets the correct feed!
    # If it appears incorrect, we will need to perform this flip before sending it to
    # the hoop detector!
    frame = cv2.flip(frame,0)
    frame = pygame.surfarray.make_surface(frame)
    #NOTE: stream aspect ratio = 1.7777
    frame = pygame.transform.scale(frame, (700,394))
    #TODO: I'd like these coords to be better defined. Maybe relative to the UI lements.
    #       On top of that: I'd also like to have the stream in its own UI-element class.
    screen.blit(frame, (275, 200))

# factor: smoothing strength. Range: 0-...
# theta: dynamic adjustment of alpha. Used when the prediction is uncertain.
#        Range: 0-1: 1 = take fully into consideration, 0 = ignore this value
def smoothen_correction(avcor, sugcor, factor, theta=1):
    assert 0 <= factor
    alpha = 1/(factor+1)    # The higher the factor, the smaller alpha
    alpha = alpha*theta
    avcor0 = alpha * sugcor[0] + (1 - alpha) * avcor[0]
    avcor1 = alpha * sugcor[1] + (1 - alpha) * avcor[1]
    return (avcor0, avcor1)

def smoothen_distance(avdist, estdist, factor):
    assert 0 <= factor
    alpha = 1/(factor+1)    # The higher the factor, the smaller alpha
    avdist = alpha * estdist + (1 - alpha) * avdist
    if avdist < 0:
        drone_land()
    return avdist

def control_drone(corr_x, corr_y, dist):
    '''
        FSM:
            * NONE:
                - Don't do anything. No hoop detected.
                - #TODO: maybe search algorithm?
                - corr != None? --> LOCK
            * LOCK:
                - Detect hoop, align with center
                - corr < corr_fwd_thresh? --> LOCK_FWD
            * LOCK_FWD
                - Stay locked, but slowly pitch forward.
                - Slightly adjust the correction for camera being brought down
                - (distance < dist_thr) && (corr < corr_fwd_thresh)? --> YOLO_FWD
            * YOLO_FWD
                - Stop applying corrections to align with center
                - Go forward at high speed
                - Start counting time
                - time > yolo_time? --> LOCK (on next hoop hoop color)
                - Unless last color, in that case --> END
            * END
                - land command / Emergency stop
    '''
    #TODO: reverse state changes?

    global hoop_fly_state
    global start_yolo_time
    global hoop_flying_enabled
    global current_hoop_color

    yolo_time = 1.25    #1s #TODO: make ticker?

    if hoop_fly_state == HoopFlyState.NONE:
        print(f"In HoopFlyState NONE ({current_hoop_color})")
        if corr_x is not None and corr_y is not None:
            hoop_fly_state = HoopFlyState.LOCK
            #TODO: allow for some stabilization time? Will it help the drone?
    elif hoop_fly_state == HoopFlyState.LOCK:
        print(f"In HoopFlyState LOCK ({current_hoop_color})")
        #TODO: show these on CP instead of printing
        drone_set_roll(corr_x*tickers['roll'].value)
        drone_set_throttle(corr_y*tickers['throttle'].value)
        if max(abs(corr_x), abs(corr_y)) < tickers['fwdthresh'].value:
            hoop_fly_state = HoopFlyState.LOCK_FWD
    elif hoop_fly_state == HoopFlyState.LOCK_FWD:
        print(f"In HoopFlyState LOCK_FWD ({current_hoop_color})")
        drone_set_pitch(tickers["pitch"].value)
        drone_set_roll(corr_x*tickers['roll'].value)
        drone_set_throttle(corr_y
                            * tickers['throttle'].value
                            + (tickers["pitch_v_corr"].value)
        if max(abs(corr_x), abs(corr_y)) > tickers['fwdthresh'].value * 0.8 \
                and dist > tickers['thr_yolo'].value * 1.5:
            hoop_fly_state = HoopFlyState.LOCK
            drone_set_pitch(0)
        elif dist < tickers['thr_yolo'].value:
            # switch over anyways, because we might have flown through already...
            hoop_fly_state = HoopFlyState.YOLO_FWD
            if current_hoop_color == HOOP_COLOR.BLUE:
                # hoop_fly_state = HoopFlyState.END
                print("Blue fwd? Shouldn't happen? I think?")
                pass    #ignore I think? Will not happen? Or will it?
            else:
                if current_hoop_color == HOOP_COLOR.RED:
                    current_hoop_color = HOOP_COLOR.YELLOW
                elif current_hoop_color == HOOP_COLOR.YELLOW:
                    current_hoop_color = HOOP_COLOR.BLUE
                else:
                    print("This shouldn't happen... Stopping...")
                    current_hoop_color = HOOP_COLOR.NONE
                    hoop_flying_enabled = False
                    drone_land()
        # else:
            # print("B", max(abs(corr[0]), abs(corr[1])), corr[0], corr[1], abs(corr[0]), abs(corr[1]), tickers['fwdthresh'].value)
    elif hoop_fly_state == HoopFlyState.YOLO_FWD:
        print(f"In HoopFlyState YOLO_FWD ({current_hoop_color})")
        drone_set_pitch(tickers["vPitch_yolo"].value)
        # drone_set_roll(0)
        # drone_set_throttle(0)
        if start_yolo_time == -1:
            print(f"SETTING START_YOLO_TIME TO {time()}")
            start_yolo_time = time()
        elif (time() - start_yolo_time) < yolo_time:
            print(f"{time()-start_yolo_time}/{yolo_time} ({time()} - {start_yolo_time})")
            drone_set_pitch(tickers["vPitch_yolo"].value)
        else:
            print("DONE YOLO")
            drone_set_pitch(0)
            print(f"SETTING START_YOLO_TIME TO {-1}")
            start_yolo_time = -1
            if current_hoop_color == HOOP_COLOR.BLUE:
                hoop_fly_state.END
            hoop_fly_state = HoopFlyState.BRAKE
            start_brake_time = time()

    elif hoop_fly_state == HoopFlyState.BRAKE:
        print(f"In HoopFlyState BRAKE ({current_hoop_color})")
        drone_set_pitch(-5)
        drone_set_throttle(20)
        # drone_set_throttle(0)
        if time() - start_brake_time > brake_seconds:
            hoop_fly_state = HoopFlyState.LOCK

    elif hoop_fly_state == HoopFlyState.END:
        print("In HoopFlyState END")
        drone_land()
    else:
        print("Unknown state?! What's happening?!")

def hoop_flying():
    global last_frame_lock
    global last_hoop_detector_frame_lock
    global last_hoop_detector_frame
    avcor = (0,0)   #Moving average for corrections
    avdist = 10
    while running:
        start = time()
        if not hoop_flying_enabled:
            avcor = (0,0)
            avdist = 10
            sleep(0.2)
            continue
        with last_frame_lock:
            frame = last_frame
        if frame is None:
            sleep(0.5)
            continue
        frame, suggested_correction, certainty, estimated_distance \
                = hoop_detector.process_frame(frame, current_hoop_color)
        with last_hoop_detector_frame_lock:
            last_hoop_detector_frame = frame
        if suggested_correction \
          and suggested_correction[0] \
          and suggested_correction[1]:
            match(certainty):
                case hoop_detector.PredictionCertainty.CERTAIN:
                    theta = 1
                case hoop_detector.PredictionCertainty.RELIABLE:
                    theta = 0.4
                case hoop_detector.PredictionCertainty.DIRECTION_ESTIMATE:
                    theta = 0.2
                case hoop_detector.PredictionCertainty.DIRECTION_GUESS:
                    theta = 0.1
                case hoop_detector.PredictionCertainty.NOISY_PREDICTION:
                    theta = 0.05
                case hoop_detector.PredictionCertainty.NONE:
                    theta = 0.01
                case default:
                    print("???", certainty)
                    theta = 0
            avcor = smoothen_correction(avcor,
                                        suggested_correction,
                                        tickers['smoothing'].value, theta=theta)
            #TODO: I'm not sure if applying the same smoothing here as with the correction is wise.
            #       It might be too strong?
            # print(f"estimated distance: {estimated_distance}")
            if estimated_distance > 0:
                avdist = smoothen_distance(avdist,
                                           estimated_distance,
                                           tickers['smoothing'].value)
        #TODO: currently, when testing with a recorded video, the avcor is TOTALLY wrong
        #       I'm going to assume this will be automatically fixed when using the cam again, 
        #       but... double check!
        print(f"Avcor: {avcor[0]:.2f},{avcor[1]:.2f}; Avdist: {Float(avdist):.2h}m")
        # print(f"Hoop detection took {Float(time()-start):.2h}s")
        #TODO: on the video one iteration takes 100ms. This is fine. But on the cam it might be faster.
        #       We might want to slow down the "acting" on the commands a bit
        control_drone(avcor[0], avcor[1], avdist)


def process_stream():
    sleep(3)    # Wait a little longer befor actually hooking on to the stream...
    drone_stream = pylwdrone.LWDrone()
    #TODO: heartbeat?
    #TODO: error catching for when drone was not on
    #TODO: sometimes it fails to get the video stream the first time.
    #       Maybe we should add some retry mechanism here for that?
    #       Or maybe a simple sleep of a second or two will do?
    global last_frame
    decoder = h264decoder.H264Decoder()
    hoop_detector.set_frame_dimensions((1152, 2048))
    while running:
        try:
            for _frame in drone_stream.start_video_stream():
                if not running:
                    break
                start = time()
                framedatas=decoder.decode(bytes(_frame.frame_bytes))
                #TODO: In theory we could also move this for-loop out of this thread,
                #       but in practice it appears this one takes less than 1ms.
                for framedata in framedatas:
                    (frame, w, h, ls) = framedata
                    if frame is not None:
                        frame = np.frombuffer(frame, dtype=np.ubyte, count=len(frame))
                        frame = frame.reshape((h, ls//3, 3))
                        frame = frame[:,:w,:]
                        frame=cv2.cvtColor(frame,cv2.COLOR_RGB2BGR) # cv2 uses BGR
                        with last_frame_lock:
                            last_frame = frame
                if PRINT_LOOPTIME:
                    print(f"Elapsed time for full run: {Float(time() - start):.2h}s")
        except Exception as e:  #TODO: narrow exception down
            print("Failed to start video stream. Trying again in 1 second...")
            print(e)
            sleep(1)

def process_events():
    #TODO: I'm more of a fan of doing the event handling INSIDE of the UI element classes.
    #       E.g. have an "on_click()" method that calls the action.
    # Event handling
    global running
    global hoop_flying_enabled
    global hoop_fly_state
    current_slider = None
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                drone_emergency_stop()
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
                        drone_set_throttle(tickers['manual_throttle_speed'].value)
                    case pygame.K_f:
                        drone_set_throttle(-tickers['manual_throttle_speed'].value)
                    case pygame.K_a:
                        drone_set_roll(-tickers['manual_roll_speed'].value)
                    case pygame.K_d:
                        drone_set_roll(tickers['manual_roll_speed'].value)
                    case pygame.K_w:
                        drone_set_pitch(tickers['manual_pitch_speed'].value)
                    case pygame.K_s:
                        drone_set_pitch(-tickers['manual_pitch_speed'].value)
                    case pygame.K_q:
                        drone_set_yaw(-tickers['manual_yaw_speed'].value)
                    case pygame.K_e:
                        drone_set_yaw(tickers['manual_yaw_speed'].value)
                    case pygame.K_RETURN:
                        drone.lift_off()
                    case pygame.K_BACKSPACE:
                        drone_land()
                    case pygame.K_h:
                        hoop_flying_enabled = not hoop_flying_enabled
                        hoop_fly_state = HoopFlyState.NONE
                        current_hoop_color = HOOP_COLOR.RED
                        print("Hoop flying: ", hoop_flying_enabled)
                        #TODO: shop with indicator on UI? Color changing button?
            elif event.type == pygame.KEYUP:
                match event.key:
                    case pygame.K_r:
                        drone_set_throttle(0)
                    case pygame.K_f:
                        drone_set_throttle(0)
                    case pygame.K_a:
                        drone_set_roll(0)
                    case pygame.K_d:
                        drone_set_roll(0)
                    case pygame.K_w:
                        drone_set_pitch(0)
                    case pygame.K_s:
                        drone_set_pitch(0)
                    case pygame.K_q:
                        drone_set_yaw(0)
                    case pygame.K_e:
                        drone_set_yaw(0)
        clock.tick(60)

args = parse_args()


# Before doing anything, show a pretty screen already (instead of a black square)
logo = pygame.image.load("Redwire_logo.png")
logo = pygame.transform.scale_by(logo, 0.8)
screen.fill(WHITE)
screen.blit(logo, [20,125])
pygame.display.flip()

# Main loop
if not args.no_connect:
    if auto_connect() < 0:  #TODO: maybe make this one configurable? On/Off?
        print("Error connecting to drone. Was it on?")
        exit(1)
    sleep(1)

    stream_thread = Thread(target=process_stream, args=())
    stream_thread.start()

    hoop_fly_thread = Thread(target=hoop_flying, args=())
    hoop_fly_thread.start()

events_thread = Thread(target=process_events, args=())
events_thread.start()


clock = pygame.time.Clock()
while running:
    screen.fill(WHITE)

    # Draw UI elements
    for btn in buttons:
        btn.draw(screen)

    for slider in sliders:
        slider.draw(screen)

    for ticker in tickers.values():
        ticker.draw(screen)

    blit_stream(screen)
    pygame.display.flip()
    clock.tick(60)

if not args.no_connect:
    print("Waiting for stream thread to stop...")
    stream_thread.join()
    print("Waiting for hoop fly thread to stop...")
    hoop_fly_thread.join()
    print("Waiting for events thread to stop...")
    events_thread.join()
pygame.quit()
sys.exit()

