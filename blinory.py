import socket
import sys
from functools import reduce
from operator import xor
from threading import Thread
from time import sleep

BASE_MSG = [ 0x66, 0x14, 0x80, 0x80, 0x80, 0x80, 0x00, 0x00, 0x00, 0x00, \
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x99]
CODE_LIFT_OFF = 0x01
CODE_LAND = 0x80
CODE_STOP = 0x2
CODE_MYSTERY = 0x4
COMMAND_SEND_N = 21
COMMAND_SEND_DELTA = 0.049


ROLL_INDEX = 2
PITCH_INDEX = 3
THROTTLE_INDEX = 4
YAW_INDEX = 5
CMD_INDEX = 6
CRC_INDEX = 18

VERBOSE = True
VVERBOSE = False


class Drone:
    #TODO: Ideally we would also let the app detect whether or not the drone is connected, and if not: connect it automatically
    def __init__(self):
        self.drone_ip = "192.168.0.1"
        self.drone_port = 50000
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.active = False
        self.msg_thread = Thread(target=self.message_send_task, args=(10,))
        # self.msg_queue = Queue()

        self.throttle_val = 128
        self.pitch_val = 128
        self.roll_val = 128
        self.yaw_val = 128

        self.pause_idle = False #Stop sending idle commands during commands

    def __del__(self):
        self.active = False
        try:
            self.msg_thread.join()
        except RuntimeError as e:
            print("Couldn't stop thread: wasn't running?")

    def activate(self):
        self.active = True
        try:
            self.msg_thread.start()
        except:
            print("Tried starting a new Blinory thread while it was already running?")
        #TODO: is this safe? What happens if we start a new thread while we were trying to stop?

    def deactivate(self):
        self.active = False
        try:
            self.msg_thread.join()
        except RuntimeError as e:
            print("Couldn't stop thread: wasn't running?")

    def message_send_task(self, arg):
        while self.active:
            if not self.pause_idle:
                # if not self.msg_queue.empty():
                    #These always have priority over scalar commands
                    # and will block them for a full second
                    # for _ in range(COMMAND_SEND_N):
                    #     self.send_msg(self.craft_msg(cmd=self.msg_queue.get(block=False)))
                    #     sleep(COMMAND_SEND_DELTA)
                    #TODO: I wonder, can't we just send them outside of the thread directly?
                    #      Or will this interfer with the commands sent inside of the thread?
                    # pass
                # else:
                self.send_msg(self.craft_msg(throttle=self.throttle_val,
                                             roll=self.roll_val,
                                             pitch=self.pitch_val,
                                             yaw=self.yaw_val))



            sleep(COMMAND_SEND_DELTA)

    #TODO: Formulas aren't perfect yet, but I'm too lazy4mathz
    # 0 - 100 --> 0 - 255
    def set_throttle(self, val):
        #TODO: Which one is it? How does it work?
        # drone.control_throttle(int(val*2.55))
        self.throttle_val = int((val*1.25)+125)

    # -100 - +100 --> 0 - 255
    def set_pitch(self, val):
        self.pitch_val = int((val*1.25)+125)

    # -100 - +100 --> 0 - 255
    def set_roll(self, val):
        self.roll_val = int((val*1.25)+125)

    # -100 - +100 --> 0 - 255
    def set_yaw(self, val):
        self.yaw_val = int((val*1.25)+125)


    def send_msg(self, data):
        if VVERBOSE:
            print(" ".join(hex(n) for n in data))
        self.socket.sendto(bytes(data), (self.drone_ip, self.drone_port))

    def craft_msg(self, cmd=0, roll=0x80, pitch=0x80, throttle=0x80, yaw=0x80):
        msg = BASE_MSG
        msg[ROLL_INDEX]     = roll
        msg[PITCH_INDEX]    = pitch
        msg[THROTTLE_INDEX] = throttle
        msg[YAW_INDEX]      = yaw
        msg[CMD_INDEX]      = cmd
        msg[CRC_INDEX]      = reduce(xor, msg[2:17])
        return msg

    def lift_off(self):
        if VERBOSE:
            print("Lift off")
        self.pause_idle = True
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(cmd=CODE_LIFT_OFF))
            sleep(COMMAND_SEND_DELTA)
        self.pause_idle = False
        self.activate()

    def land(self):
        if VERBOSE:
            print("Land")
        self.pause_idle = True
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(cmd=CODE_LAND))
            sleep(COMMAND_SEND_DELTA)
        self.pause_idle = False
        self.deactivate()

    def emergency_stop(self):
        if VERBOSE:
            print("Emergency_stop")
        self.pause_idle = True
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(cmd=CODE_STOP))
            sleep(COMMAND_SEND_DELTA)
        self.pause_idle = False
        self.deactivate()

    def mystery_command(self):
        if VERBOSE:
            print("Mystery command")
        self.pause_idle = True
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(cmd=CODE_MYSTERY))
            sleep(COMMAND_SEND_DELTA)
        self.pause_idle = False
        self.activate()

    def send_idle(self):
        self.send_msg(self.craft_msg())

    """
    Controls throttle RELATIVELY to what it is now
    v: change in throttle (unsigned int: 0-255. No change = 128)
    """
    #TODO:  I guess we could improve this interface towards the user so that
    #       a more user friendly value can be passed (e.g. -100 to +100)
    #TODO: Or just remove them. They will be deprecated
    def control_throttle(self, v=128):
        if VERBOSE:
            print(f"Change throttle: {v}")
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(throttle=v))
            sleep(COMMAND_SEND_DELTA)
        self.send_idle()

    def control_roll(self, v=128):
        if VERBOSE:
            print(f"Roll: {v}")
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(roll=v))
            sleep(COMMAND_SEND_DELTA)
        self.send_idle()

    def control_pitch(self, v=128):
        if VERBOSE:
            print(f"Pitch: {v}")
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(pitch=v))
            sleep(COMMAND_SEND_DELTA)
        self.send_idle()

    def control_yaw(self, v=128):
        if VERBOSE:
            print(f"Yaw: {v}")
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(yaw=v))
            sleep(COMMAND_SEND_DELTA)
        self.send_idle()





def main():
    drone = Drone()

    if len(sys.argv) == 1:
        print("Please pass list of commands. Possible options:\n"
              " * lift_off\n"
              " * land\n"
              " * STOP\n")
    for i, cmd in enumerate(sys.argv[1:]):
        match cmd:
            case "nop":
                print("Waiting...")
                sleep(5)
            case "lift_off":
                print("Lift off")
                drone.lift_off()
            case "land":
                print("Landing")
                drone.land()
            case "STOP":
                print("STOP")
                drone.emergency_stop()
            case "throttle_up":
                print("Increasing throttle")
                drone.control_throttle(200)
            case "throttle_down":
                print("Decreasing throttle")
                drone.control_throttle(50)
            case "pitch_up":
                print("Pitching up")
                drone.control_pitch(200)
            case "pitch_down":
                print("Pitching down")
                drone.control_pitch(50)
            case "roll_left":
                print("Rolling left")
                drone.control_roll(50)
            case "roll_right":
                print("Rolling right")
                drone.control_pitch(200)
            case "rot_left":
                print("Rotating left")
                drone.control_yaw(50)
            case "rot_right":
                print("Rotating right")
                drone.control_yaw(200)
            case "off":     #Better way to land than "land", but not 100% reliable it seems
                print("Decreasing throttle to 0")
                for _ in range(COMMAND_SEND_N):
                    drone.control_throttle(0)
                    sleep(COMMAND_SEND_DELTA)
            case _:
                print(f"Unkown command {cmd}. Ignoring")
        if i+1 != len(sys.argv[1:]):
            sleep(5)


if __name__ == "__main__":
    main()
