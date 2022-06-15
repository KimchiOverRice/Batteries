import time
import struct
from bitarray import bitarray
import can
from can.notifier import MessageRecipient

def to_bytearray() -> bytearray:
    buf = bytearray(8)
    #print(self.max_charging_voltage)
    struct.pack_into('>h', buf, 0, int(200 * 10.0))
    struct.pack_into('>h', buf, 2, int(10 * 10.0))
    struct.pack_into('?', buf, 4, 0)
    return buf

def socketcan_bus():
    return can.Bus(interface='socketcan',
                    channel='can0',
                    bitrate=250000)

bus = socketcan_bus()
while True:
    array = to_bytearray()
    msg = can.Message(arbitration_id=0x1806E5F4, data=array)
    print(msg)
    bus.send(msg)
    time.sleep(1)
    
