# -*- coding: utf-8 -*-
"""
TI CC2650 SensorTag
-------------------
An example connecting to a TI CC2650 SensorTag.
Created on 2018-01-10 by hbldh <henrik.blidh@nedomkull.com>
"""
import platform
import logging
import asyncio
import binascii
import struct
import os

from bleak import BleakClient
from bleak import _logger as logger
from bleak.uuids import uuid16_dict

import numpy as np
import matplotlib.pyplot as plt



g_CumulativeOld = 10
g_Last_revolution_event_time_Old = 0.0


uuid16_dict = {v: k for k, v in uuid16_dict.items()}

# I/O test points on SensorTag.
IO_DATA_CHAR_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("CSC Measurement")
)



def openPowerCurve(filename):
    file = open(filename)
    output = []
    for line in file:

        if line[-1:] == '\n' :
            tuple = (int(line[:-1].split(',', 1 )[0]),int(line[:-1].split(',', 1 )[1]))
        else :
            tuple = (int(line.split(',', 1 )[0]),int(line.split(',', 1 )[1]))
        output.append(tuple)
            
    return output
    
def getSpeed(CumulRotation,Last_revolution_event_time):
    global g_CumulativeOld
    global g_Last_revolution_event_time_Old
    
    if (g_Last_revolution_event_time_Old >= Last_revolution_event_time):
        delta_event_time = 65536 - Last_revolution_event_time + g_Last_revolution_event_time_Old
    else :
        delta_event_time = Last_revolution_event_time - g_Last_revolution_event_time_Old 
    
    speed = (CumulRotation - g_CumulativeOld)*2096/(delta_event_time/ 1.024) *60*60/1000
    
    g_CumulativeOld = CumulRotation
    g_Last_revolution_event_time_Old = Last_revolution_event_time
    
    return speed
    
def getPower(pointsList,speed):
    # get x and y vectors
    points = np.array(pointsList)
    x = points[:,0]
    y = points[:,1]
    
    # calculate polynomial
    z = np.polyfit(x, y, 3)

    f = np.poly1d(z)
    return f(speed)
    

async def run(address, loop, debug=True):
   
    PowerCurve = openPowerCurve("Satori_4.txt")
        
    if debug:
        import sys


    async with BleakClient(address, loop=loop) as client:

        def notification_handler(sender, data):
            """Simple notification handler which prints the data received."""
            try:
                speed = getSpeed(int.from_bytes(data[1:5], byteorder='little',signed = False),int.from_bytes(data[5:7], byteorder='little',signed = False))
                print("SPEED : {0} , CALCULATED POWER : {1}".format(speed,getPower(PowerCurve,speed)))
                
            except Exception:
                print("EXCEPTION :     {0}".format(data))

            
        await client.start_notify(IO_DATA_CHAR_UUID, notification_handler)
        await asyncio.sleep(360.0, loop=loop)
        await client.stop_notify(IO_DATA_CHAR_UUID)


if __name__ == "__main__":
    

    os.environ["PYTHONASYNCIODEBUG"] = str(1)
    
    address = (
        "FA:CB:39:A5:F5:8C"
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(address, loop, True))