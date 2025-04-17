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


class Drone:
    def __init__(self):
        self.drone_ip = "192.168.0.1"
        self.drone_port = 50000
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def send_msg(self, data):
        if VERBOSE:
            print(" ".join(hex(n) for n in data))
        self.socket.sendto(bytes(data), (self.drone_ip, self.drone_port))

    def craft_msg(self, cmd=0, bank=0x80, pitch=0x80, throttle=0x80, yaw=0x80):
        msg = BASE_MSG
        msg[2] = bank
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


def main():
    drone = Drone()

    if len(sys.argv) == 1:
        print("Please pass list of commands. Possible options:\n"
              " * lift_off\n"
              " * land\n"
              " * STOP\n")
    for cmd in sys.argv[1:]:
        match cmd:
            case "lift_off":
                drone.lift_off()
            case "land":
                drone.land()
            case "STOP":
                drone.emergency_stop()
            case _:
                print(f"Unkown command {cmd}. Ignoring")
        sleep(5)


if __name__ == "__main__":
    main()
