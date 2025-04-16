import socket
import time
SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
COMMANDS = {"idle": 0x00,
            "takeoff":0x01,
            "land" : 0x80}
IP = "192.168.0.1"
PORT = 50000
ADDRESS = (IP, PORT)

def send_command(command):
    command_data = bytes([0x66,0x14,0x80,0x80,0x80,0x80,COMMANDS[command],0x00,
            0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
            0x00,COMMANDS[command],0x99])
    print(command_data)
    SOCK.sendto(command_data, ADDRESS)

def main():
    send_command("takeoff")
    for i in range(5):
        send_command("idle")
        time.sleep(1)
    send_command("land")

if __name__ == '__main__':
    main()
