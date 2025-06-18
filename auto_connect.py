'''
Copyright (C) 2025

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
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

    nmcli.disable_use_sudo()

    device = next((device for device in nmcli.device() if device.device == iface), None)
    if device == None:
        print(f"Device {iface} not found.")
        return -1
    if device.connection != None:
        print(f"Device was connected to: {device.connection}")
        if ap_name in device.connection:
            print(f"This is the drone. Nothing more to be done.")
            return 0

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
                return 0
            else:
                print("Unexpected error: Connection failed")
                return -1

    return 0

if __name__ == "__main__":
    auto_connect()
