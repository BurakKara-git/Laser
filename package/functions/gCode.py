from tkinter import Button
from zaber_motion import MotionLibException
from zaber_motion.ascii import Device as ZaberDevice
from zaber_motion.gcode import Translator
from gcodeparser import GcodeParser
from package.classes.WindowController import WindowController
from package.classes.Device import Device
import time, threading, package.constants as constants, math
from typing import List

def Gcode(
    gcode: str,
    device_list: List[ZaberDevice],
    button: Button,
    lock: threading.Lock,
    stop_event: threading.Event,
    resume_event: threading.Event,
):
    """
    Executes G-code commands on a list of devices, controlling their movements
    based on the parsed G-code instructions.

    Parameters:
    - gcode (str): The G-code string containing the movement commands.
    - device_list (List[Device]): List of Device objects representing the axes to be controlled.
    - window (classes.WindowController): The window controller for updating UI elements.
    - button (Button): Button to invoke upon completion or error.
    - lock (threading.Lock): Thread lock to control access to shared resources.
    - stop_event (threading.Event): Event to signal stopping the execution.
    - resume_event (threading.Event): Event to signal resuming the execution.

    This function performs the following steps:
    1. Parses the G-code lines.
    2. Sets up the device streams and translators.
    3. Iterates over the parsed G-code lines, controlling the devices accordingly.
    4. Updates the progress bar and text in the UI.
    5. Handles threading for concurrent execution of commands.
    6. Waits for threads to complete and then flushes translators and disables streams.
    7. Releases the lock and invokes the button upon completion or if an error occurs.

    Internal helper functions:
    - axis_stream(translator: Translator, command: str): Sends a command to a specific translator.
    - calculate_speeds(axis_params, previous_positions, speed): Calculates the speeds for each axis based on the parameters.
    - setup_devices(): Sets up the device streams and translators.

    Example usage:
    ```python
    GCode(gcode_str, device_list, window_controller, button, lock, stop_event, resume_event)
    ```

    Note:
    - The function prints and updates the UI in case of errors.
    """

    def axis_stream(translator: Translator, command: str):
        print(f"Command: {command}, Translator: {translator}")
        try:
            translator.translate(command)
            translator.flush()
        except MotionLibException as err:
            print(f"Wrong Command: {command}.")
            print(err)
        finally:
            return

    def calculate_speeds(axis_params, previous_positions, speed):
        check = ["X", "Y", "Z"]
        position_differences = [0, 0, 0]
        pre_sum = 0
        axis_speeds = {axis: 0 for axis in axis_params}

        for i in range(3):
            param, _ = axis_params[check[i]]
            if param is not None:
                dif = abs(previous_positions[i] - param)
                position_differences[i] = dif
                pre_sum += dif**2

        total_len = math.sqrt(pre_sum)

        for i in range(3):
            param, _ = axis_params[check[i]]
            if param is not None:
                axis_speeds[check[i]] = (
                    (position_differences[i] * speed / total_len)
                    if total_len != 0
                    else 0
                )

        param_a, _ = axis_params["A"]
        if param_a is not None and speed != 0:
            radius = math.sqrt(
                (constants.X_CENTER - previous_positions[0]) ** 2
                + (constants.Y_CENTER - previous_positions[1]) ** 2
            )
            rot_speed = speed / radius if radius != 0 else 0
            rot_speed = min(rot_speed, constants.MAX_ROT_VEL)
        else:
            rot_speed = 0
        axis_speeds["A"] = rot_speed * 57.2957795

        return axis_speeds

    def setup_devices():
        try:
            axis_list = [device.get_axis(1) for device in device_list]
            stream_list = [device.streams.get_stream(1) for device in device_list]
            for stream in stream_list:
                stream.setup_live(1)
            translator_list = [Translator.setup(stream) for stream in stream_list]
            return axis_list, stream_list, translator_list
        except MotionLibException as err:
            print(err)
            finalize(translator_list, stream_list)
            return None, None, None
    
    axis_list, stream_list, translator_list = setup_devices()
    lock.acquire()
    lines = GcodeParser(gcode).lines
    total_count = len(lines)
    all_devices = Device(*axis_list)
    threads = []

    def finalize():
        for translator in translator_list:
            translator.flush()
        for stream in stream_list:
            if not stream.check_disabled():
                stream.disable()
        all_devices.stop_axes()
        lock.release()

    count = 0
    for line in lines:
        while not resume_event.is_set():
            time.sleep(1)
            if stop_event.is_set():
                break

        if stop_event.is_set():
            break     
        
        count += 1

        axis_params = {
            "X": (line.get_param("X"), translator_list[0]),
            "Y": (line.get_param("Y"), translator_list[1]),
            "Z": (line.get_param("Z"), translator_list[2]),
            "A": (line.get_param("A"), translator_list[3]),
        }
        print(line.comment)
        speed = (line.get_param("F") or 0) * 60

        previous_positions = all_devices.get_current_positions()
        axis_speeds = calculate_speeds(axis_params, previous_positions, speed)

        if all(param is None for param, _ in axis_params.values()):
            command = line.command_str
            if command in {"M3", "M4"}:
                command = f"G90 G0 X{constants.Z_MAX}"
                thread = threading.Thread(
                    target=axis_stream, args=(translator_list[2], command)
                )
                threads.append(thread)
                thread.start()
            elif command == "M5":
                command = f"G90 G0 X{constants.INITIAL_Z}"
                thread = threading.Thread(
                    target=axis_stream, args=(translator_list[2], command)
                )
                threads.append(thread)
                thread.start()
            else:
                for i in range(4):
                    thread = threading.Thread(
                        target=axis_stream, args=(translator_list[i], command)
                    )
                    threads.append(thread)
                    thread.start()
        else:
            non_none_params = {
                axis: (param, translator)
                for axis, (param, translator) in axis_params.items()
                if param is not None
            }
            for axis, (param, translator) in non_none_params.items():
                if axis == "A":
                    command = f"G91 {line.command_str} X{param*57.2957795}"
                else:
                    command = f"G90 {line.command_str} X{param}"
                if line.get_param("F") is not None and axis_speeds[axis] != 0:
                    command += f" F{axis_speeds[axis]}"
                elif line.get_param("F") is not None and axis_speeds[axis] == 0:
                    continue
                thread = threading.Thread(
                    target=axis_stream, args=(translator, command)
                )
                thread.daemon = True
                threads.append(thread)
                thread.start()
        all_devices.wait_axes()
    
    finalize()
    return
