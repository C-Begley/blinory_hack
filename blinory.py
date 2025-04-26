import socket
import sys
from functools import reduce
from operator import xor
from time import sleep

BASE_MSG = [ 0x66, 0x14, 0x80, 0x80, 0x80, 0x80, 0x00, 0x00, 0x00, 0x00, \
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x99]
CODE_LIFT_OFF = 0x01
CODE_LAND = 0x80
CODE_STOP = 0x2
COMMAND_SEND_N = 21
COMMAND_SEND_DELTA = 0.049

VERBOSE = True
VVERBOSE = False


class Drone:
    #TODO: Ideally we would also let the app detect whether or not the drone is connected, and if not: connect it automatically
    def __init__(self):
        self.drone_ip = "192.168.0.1"
        self.drone_port = 50000
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def send_msg(self, data):
        if VVERBOSE:
            print(" ".join(hex(n) for n in data))
        self.socket.sendto(bytes(data), (self.drone_ip, self.drone_port))

    def craft_msg(self, cmd=0, roll=0x80, pitch=0x80, throttle=0x80, yaw=0x80):
        msg = BASE_MSG
        msg[2] = roll
        msg[3] = pitch
        msg[4] = throttle
        msg[5] = yaw
        msg[6] = cmd
        msg[18] = reduce(xor, msg[2:17])
        return msg

    def lift_off(self):
        if VERBOSE:
            print("Lift off")
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(cmd=CODE_LIFT_OFF))
            sleep(COMMAND_SEND_DELTA)

    def land(self):
        if VERBOSE:
            print("Land")
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(cmd=CODE_LAND))
            sleep(COMMAND_SEND_DELTA)

    def emergency_stop(self):
        if VERBOSE:
            print("Emergency_stop")
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(cmd=CODE_STOP))
            sleep(COMMAND_SEND_DELTA)

    def send_idle(self):
        self.send_msg(self.craft_msg())

    """
    Controls throttle RELATIVELY to what it is now
    v: change in throttle (unsigned int: 0-255. No change = 128)
    """
    #TODO:  I guess we could improve this interface towards the user so that
    #       a more user friendly value can be passed (e.g. -100 to +100)
    def control_throttle(self, v=128):
        if VERBOSE:
            print(f"Change throttle: {v}")
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(throttle=v))
            # sleep(COMMAND_SEND_DELTA)
        self.send_idle()

    def control_roll(self, v=128):
        if VERBOSE:
            print(f"Roll: {v}")
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(roll=v))
            # sleep(COMMAND_SEND_DELTA)
        self.send_idle()

    def control_pitch(self, v=128):
        if VERBOSE:
            print(f"Pitch: {v}")
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(pich=v))
            # sleep(COMMAND_SEND_DELTA)
        self.send_idle()

    def control_yaw(self, v=128):
        if VERBOSE:
            print(f"Pitch: {v}")
        for _ in range(COMMAND_SEND_N):
            self.send_msg(self.craft_msg(yaw=v))
            # sleep(COMMAND_SEND_DELTA)
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
