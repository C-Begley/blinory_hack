# Drone control protocol

All commands are 20 bytes, sent as a UDP payload.
Event-Commands (such as Take-Off and Land) are sent 21 times with 49.57ms in between, for a total duration of 1.041 seconds.

Byte 0:     Header: 0x66
Byte 1:     Also Header?: 0x14
Byte 2:     Bank L/R
Byte 3:     Pitch U/D
Byte 4:     Throttle U/D
Byte 5:     Yaw L/R
Byte 6:     Command field: 0x01 for take-off, 0x80 for land.
Byte 7:     0 (unknown? unused?)
Byte 8:     0 (unknown? unused?)
Byte 9:     0 (unknown? unused?)
Byte 10:    0 (unknown? unused?)
Byte 11:    0 (unknown? unused?)
Byte 12:    0 (unknown? unused?)
Byte 13:    0 (unknown? unused?)
Byte 14:    0 (unknown? unused?)
Byte 15:    0 (unknown? unused?)
Byte 16:    0 (unknown? unused?)
Byte 17:    0 (unknown? unused?)
Byte 18:    checksum: XOR(B2:B17)
Byte 19: Footer: 0x99.



