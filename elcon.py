#!/usr/bin/env python

r'''
References:

https://github.com/Lennart-O/TCCharger-voltage-current-control/blob/master/1430%20ALG-CAN%20Protocol.pdf
https://github.com/DanyEarth/TC-Charger-CAN-controller

The Elcon CAN bus specification is attached.  It complies with CAN 2.0B and J1939 protocols.
1.8KW and 3.3KW chargers use 250Kbps baud rate and 29-bit extended frame CAN ID.
6.6KW chargers use 500Kbps.

The charger expects every second to receive a CAN message from the BMS with CAN ID 1806E5F4
and 8 data bytes with voltage and current required.
For example 98V and 16A would be 980 = 03D4 hex and 0160 = 00A0 hex
so the 8 data bytes would be 03D4 00A0 0000 0000.
If the charger does not receive a valid CAN message in 5 seconds,
it stops charging with a green blinking LED.
It starts charging again when it gets a valid CAN message with a red blinking LED.

The charger sends out every second a status message with CAN ID 18FF50E5
 with voltage, current and status information.

Up to four Elcon PFC chargers can be on the same CAN bus with CAN IDs of E5, E7, E8 and E9.

A 120 ohm termination resistor is required between CAN-L and CAN-H.

'''

import asyncio
import logging

from bitarray import bitarray
import can
from can.notifier import MessageRecipient
from dataclasses import dataclass, field
import pprint
from typing import List, Union
import struct

class ElconTcCharger(object):

    LOG = logging.getLogger(__name__)

    @dataclass
    class Message1(object):

        CAN_ID = 0x1806E5F4

        max_charging_voltage: float = 0
        max_charging_current: float = 0
        battery_protection_enabled: bool = 0

        @classmethod
        def from_bytearray(cls, buf):
            #buf = bytearray(8)
            max_charging_voltage = struct.unpack_from('>h', buf, 0)[0] / 10.0
            max_charging_current = struct.unpack_from('>h', buf, 2)[0] / 10.0
            battery_protection_enabled = struct.unpack_from('?', buf, 4)[0]
            return cls(max_charging_voltage=max_charging_voltage,
                       max_charging_current=max_charging_current,
                       battery_protection_enabled=battery_protection_enabled)

        def to_bytearray(self) -> bytearray:
            buf = bytearray(8)
            #print(self.max_charging_voltage)
            struct.pack_into('>h', buf, 0, int(self.max_charging_voltage * 10.0))
            struct.pack_into('>h', buf, 2, int(self.max_charging_current * 10.0))
            struct.pack_into('?', buf, 4, self.battery_protection_enabled)
            return buf

    @dataclass
    class Message2(object):

        CAN_ID = 0x18FF50E5

        output_voltage: float = 0
        output_current: float = 0
        status_flags: dict = field(default_factory=dict)

        @classmethod
        def status_flags_keys(cls) -> list:
            return [
                'hardware_failure',         # 0 = normal, 1 = failure
                'temperature_of_charger',   # 0 = normal, 1 = overtemp protection
                'input_voltage',            # 0 = normal, 1 = incorrect input voltage
                'starting_state',           # 0 = normal, 1 = battery disconnected or reverse
                'communication'             # 0 = normal, 1 = communication timeout
            ]

        @classmethod
        def from_bytearray(cls, buf):
            #buf = bytearray(8)
            output_voltage = struct.unpack_from('>h', buf, 0)[0] / 10.0
            output_current = struct.unpack_from('>h', buf, 2)[0] / 10.0
            status_flags_bitarray = bitarray()
            status_flags_bitarray.frombytes(struct.unpack_from('c', buf, 4)[0])
            status_flags = cls.status_flags_from_bitarray(status_flags_bitarray)
            return cls(output_voltage=output_voltage,
                       output_current=output_current,
                       status_flags=status_flags)

        @classmethod
        def status_flags_from_bitarray(cls, array: bitarray) -> dict:
            flags = dict()
            for i, key in enumerate(cls.status_flags_keys()):
                flags[key] = array[i]
            return flags


        @classmethod
        def bitarray_from_status_flags(cls, flags: dict) -> bitarray:
            array = bitarray('00000000')
            for i, key in enumerate(cls.status_flags_keys()):
                array[i] = flags.get(key, 0)
            return array

        def to_bytearray(self) -> bytearray:
            buf = bytearray(8)
            struct.pack_into('>h', buf, 0, int(self.output_voltage * 10.0))
            struct.pack_into('>h', buf, 2, int(self.output_current * 10.0))
            status_flags_bitarray = self.bitarray_from_status_flags(self.status_flags)
            struct.pack_into('c', buf, 4, status_flags_bitarray.tobytes())
            return buf

    @classmethod
    def virtual_bus(cls):
        return can.Bus(interface='virtual',
                       channel='vcan0',
                       receive_own_messages=True)

    @classmethod
    def socketcan_bus(cls):
        return can.Bus(interface='socketcan',
                       channel='can0',
                       bitrate=250000)

    def __init__(self, bus=None):
        if bus is None:
            bus = self.socketcan_bus()
        self.bus = bus


    def send(self, message: Union[Message1, Message2]):
        bus = self.bus
        msg = can.Message(arbitration_id=message.CAN_ID,
                          data=message.to_bytearray())
        bus.send(msg)

    async def recv(self, msg: can.Message) -> None:

        if msg.arbitration_id == ElconTcCharger.Message1.CAN_ID:
            msg1 = ElconTcCharger.Message1.from_bytearray(msg.data)
            pprint.pprint(msg1)

        elif msg.arbitration_id == ElconTcCharger.Message2.CAN_ID:
            msg2 = ElconTcCharger.Message2.from_bytearray(msg.data)
            pprint.pprint(msg2)

        else:
            ElconTcCharger.LOG.error(f'Unknown CAN message: {msg}')

    async def run(self):
        bus = self.bus

        reader = can.AsyncBufferedReader()
        logger = can.Logger("logfile.asc")
        callback = self.recv

        listeners: List[MessageRecipient] = [
            callback,  # Callback function
            reader,  # AsyncBufferedReader() listener
            logger,  # Regular Listener object
        ]
        # Create Notifier with an explicit loop to use for scheduling of callbacks
        loop = asyncio.get_running_loop()
        notifier = can.Notifier(bus, listeners, loop=loop)

        while True:
            msg = await reader.get_message()

        # Clean-up
        notifier.stop()
