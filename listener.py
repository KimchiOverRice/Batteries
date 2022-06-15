import time
import struct
from bitarray import bitarray
import can
from can.notifier import MessageRecipient

def status_flags_keys() -> list:
        return [
            'hardware_failure',         # 0 = normal, 1 = failure
            'temperature_of_charger',   # 0 = normal, 1 = overtemp protection
            'input_voltage',            # 0 = normal, 1 = incorrect input voltage
            'starting_state',           # 0 = normal, 1 = battery disconnected or reverse
            'communication'             # 0 = normal, 1 = communication timeout
        ]

def status_flags_from_bitarray(array: bitarray) -> dict:
    flags = dict()
    for i, key in enumerate(status_flags_keys()):
        flags[key] = array[i]
    return flags

def from_bytearray(buf):
    output_voltage = struct.unpack_from('>h', buf, 0)[0] / 10.0
    output_current = struct.unpack_from('>h', buf, 2)[0] / 10.0
    status_flags_bitarray = bitarray()
    status_flags_bitarray.frombytes(struct.unpack_from('c', buf, 4)[0])
    status_flags = status_flags_from_bitarray(status_flags_bitarray)
    return print("output_voltage=\n", output_voltage,
                "output_current=\n", output_current,
                "status_flags=\n",status_flags)

def socketcan_bus():
    return can.Bus(interface='socketcan',
                    channel='can0',
                    bitrate=250000)

bus = socketcan_bus()
while True:
    msg = bus.recv()
    print(msg)
    from_bytearray(msg.data)


