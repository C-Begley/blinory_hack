import enum as e
import time as t
import sys
sys.path.append("..")

class Direction(e.Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

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
        else:
            print("Direction {} not recognised".format(direction))

    def move(self, direction, dur=1, speed=25):
        print("Moving {} with speed {}", direction, speed)
        self.__move(direction, speed)
        t.sleep(dur)
        self.__move(direction, speed=0)
        t.sleep(dur*2)
        print("Done moving {} with speed {}", direction, speed)
        
    def move_and_bank(direction, bank, dur=1,speed=25, roll=45):
        self.__move(direction, speed)
        self.__move(bank,roll)
        t.sleep(dur)
        self.__move(direction, 0)
        self.__move(bank,0)
