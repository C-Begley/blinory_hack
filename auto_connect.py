import nmcli
from time import sleep

iface = "wlp6s0"    #TODO: make configurable
ap_name = "BLINORY"

n_attempts = 20     #20 attempts to find network and connect
attempt_delta = 5   #Wait 5s in between every attempt
rescan_delta = 5    #Once every 5 attempts, do a rescan

def auto_connect():
    #TODO: Status of NetworkManager?
    #nmcli.general.status() -> General

    device = next((device for device in nmcli.device() if device.device == iface), None)
    if device == None:
        print(f"Device {iface} not found.")
        return
    if device.connection != None:
        print(f"Device was connected to: {device.connection}")
        if ap_name in device.connection:
            print(f"This is the drone. Nothing more to be done.")
            return

    print("Trying to connect to the drone. Make sure it's on.")
    for i in range(n_attempts):
        networks = nmcli.device.wifi(rescan = not ((i+1) % rescan_delta))
        drone_netw = next((netw for netw in networks if ap_name in netw.ssid), None)
        if not drone_netw:
            print(f"Not found, trying again in {attempt_delta}...")
            sleep(attempt_delta)
        else:
            print("Network found! Connecting...")
            nmcli.device.wifi_connect(ifname=device.device, ssid=drone_netw.ssid, password="")
            sleep(1)
            # Gotta get it again it appears
            device = next((device for device in nmcli.device() if device.device == iface), None)
            if device.connection != None:
                print(f"Successfully connected to {device.connection}")
            else:
                print("Unexpected error: Connection failed")
            return


if __name__ == "__main__":
    auto_connect()
