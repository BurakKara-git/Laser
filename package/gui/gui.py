from tkinter import *
import package.constants as constants
import threading
from package.gui.char_window import char_window
from package.gui.create_button import create_button
from package.classes.Device import Device
from package.functions.thread_switch import thread_switch
from package.functions.gCode import Gcode
from package.gui.fresnel_window import fresnel_window


def gui(device_list):
    print(f"Found {len(device_list)} devices")

    # Initialize devices and axes
    axes_list = [device.get_axis(1) for device in device_list]
    device = Device(*axes_list)

    # Initialize Thread Events
    start_event = threading.Event()
    start_event.set()
    pause_event = threading.Event()
    lock = threading.Lock()

    window = Tk()
    window.title("Stage Controller")
    window.geometry("1280x720")

    char_btn = create_button(
        window, "Characterisation", lambda: char_window(window, gcode_text), 1, 5
    )

    fresnel_btn = create_button(
        window, "Fresnel", lambda: fresnel_window(window, device_list), 2, 5
    )

    # GCode Button Configuration
    gcode_label = Label(window, text="GCode Input", font=("Arial Bold", 20))
    gcode_text = Text(window, height=5, width=52)
    gcode_label.grid(row=0, column=2)
    gcode_text.grid(row=1, column=1,  columnspan= 3, rowspan = 2)
    gcode_text.insert("end", constants.GCODE_PLACEHOLDER)

    gcode_initial_funcs = [
        lambda: char_btn.config(state=DISABLED),
        lambda: extract_btn.config(state=DISABLED),
        lambda: fresnel_btn.config(state=DISABLED),
        lambda: pause_event.set(),
        lambda: gcode_btn.config(text="STOP GCODE"),
    ]

    gcode_final_funcs = [
        lambda: char_btn.config(state=NORMAL),
        lambda: extract_btn.config(state=NORMAL),
        lambda: fresnel_btn.config(state=NORMAL),
        lambda: pause_event.clear(),
        lambda: pause_btn.config(text="PAUSE"),
        lambda: gcode_btn.config(text="Start GCode"),
    ]

    gcode_command = lambda: thread_switch(
        Gcode,
        start_event,
        (
            gcode_text.get("1.0", END),
            device_list,
            gcode_btn,
            lock,
            start_event,
            pause_event,
        ),
        gcode_initial_funcs,
        gcode_final_funcs,
    )

    gcode_btn = create_button(window, "Start GCode", gcode_command, 3, 2)

       # Pause Button Configuration
    pause_initial_funcs = [
        lambda: pause_btn.config(text="RESUME"),
    ]

    pause_final_funcs = [
        lambda: pause_btn.config(text="PAUSE"),
    ]

    pause_command = lambda: thread_switch(
        None, pause_event, None, pause_initial_funcs, pause_final_funcs
    )

    pause_btn = create_button(window, "PAUSE", pause_command, 3, 1)

    # Extract Button Configuration
    extract_btn = create_button(window, "EXTRACT", lambda: device.extract_axes(), 3, 3)

    window.mainloop()
