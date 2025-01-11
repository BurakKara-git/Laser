from tkinter import Button
from package.functions.writer import writer
from package.functions.logger import logger
from zaber_motion.ascii import Device as ZaberDevice
from zaber_motion import Units, MotionLibException
from package.classes.WindowController import WindowController
from package.classes.Device import Device
import time, threading, package.constants as constants
from package.functions.gCode import Gcode
from typing import List

def raster_scan(
    window: WindowController,
    device_list: List[ZaberDevice],
    button: Button,
    lock: threading.Lock,
    stop_event: threading.Event,
    resume_event: threading.Event,
):
    values = window.get_values()
    initial_x = values[0]
    initial_y = values[1]
    y_increment = values[4]
    dia = values[5]
    initial_vel = values[7]

    # Calculate Total Task
    total_task = int((dia) / y_increment)
    if total_task > constants.MAX_X_VEL:
        print("ERROR - CANNOT DO TASKS WITH VELOCITIES:")
        while total_task > constants.MAX_X_VEL:
            max_velocity = initial_vel * (total_task)
            total_task -= 1
            print(max_velocity, end=", ")
    if total_task % 2 == 0:
        max_velocity = initial_vel * (total_task)
        print(max_velocity)
        total_task -= 1

    passed = 0

    #Generate Raster Scan
    gCode = ";"
    for i in range(total_task):
        if (i+passed)%2 == 0:
            x_position = constants.X_MAX
        else:
            x_position = initial_x
        feed_rate = total_task - i
        y_position = initial_y + (i+1)*y_increment

        if i == int(total_task / 2) + 1:
            gCode += "G0 Y{}\n".format(y_position)
            passed += 1
        
        else:
            gCode += "G1 X{} F{}\n".format(x_position, feed_rate)
            gCode += "G0 Y{}\n".format(y_position)      
    print(gCode)

    Gcode(gCode,device_list,window,button,lock,stop_event,resume_event)

    return
