import enum as e
import time as t
import sys
sys.path.append("..")

class Direction(e.Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    YAW= 5

class led_drawer():

    def __init__(self, drone):
        self.drone = drone

    def __move(self, direction, speed):
        if direction==Direction.UP:
            self.drone.set_throttle(speed)
        elif direction==Direction.DOWN:
            self.drone.set_throttle(-speed)
        elif direction==Direction.RIGHT:
            self.drone.set_roll(speed)
        elif direction==Direction.LEFT:
            self.drone.set_roll(-speed)
        elif direction==Direction.YAW:
            self.drone.set_yaw(speed)
        else:
            print("Direction {} not recognised".format(direction))

    def move(self, direction, dur=1, speed=25):
        print("Moving {} with speed {}", direction, speed)
        self.__move(direction, speed)
        t.sleep(dur)
        self.__move(direction, speed=0)
        t.sleep(0.5)
        print("Done moving {} with speed {}", direction, speed)
        
    def move_and_bank(self, direction, move_dur, bank, bank_dur,speed=25, roll=25):
        self.__move(direction, speed)
        self.__move(bank,roll)
        if(move_dur > bank_dur):
            t.sleep(bank_dur)
            self.__move(bank,0)
            t.sleep(move_dur-bank_dur)
            self.__move(direction,0)
        if(move_dur < bank_dur):
            t.sleep(move_dur)
            self.__move(direction,0)
            t.sleep(bank_dur-move_dur)
            self.__move(bank,0)
        else:
            t.sleep(move_dur)
            self.__move(direction, 0)
            self.__move(bank,0)
