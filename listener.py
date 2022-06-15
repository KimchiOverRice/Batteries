import time
from bitarray import bitarray
import can
from can.notifier import MessageRecipient

def socketcan_bus(cls):
    return can.Bus(interface='socketcan',
                    channel='can0',
                    bitrate=250000)

bus = socketcan_bus()
while True:
    msg = bus.recv()
    


    

