from tkinter import *
from package.functions.thread_switch import thread_switch
from package.functions.raster_scan import raster_scan
from package.functions.gCode import Gcode
import threading
from package.classes.WindowController import WindowController
from package.classes.Device import Device

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

    # Configure Main Window
    window = Tk()
    window_controller = WindowController(device, window)

    # Utility function to create button and set grid position
    def create_button(text, command, column, row):
        btn = Button(window, text=text, command=command)
        btn.grid(column=column, row=row)
        return btn

    # Run Button Configuration
    run_initial_funcs = [
        lambda: extract_btn.config(state=DISABLED),
        lambda: window_controller.set_btn.config(state=DISABLED),
        lambda: gcode_btn.config(state=DISABLED),
        lambda: pause_event.set(),
        lambda: window_controller.setter(device),
        lambda: window_controller.print_msg("RUNNING THE TASK", "green"),
        lambda: window_controller.progress_text.config(fg="green"),
        lambda: run_btn.config(text="STOP"),
    ]

    run_final_funcs = [
        lambda: device.extract_axes(),
        lambda: extract_btn.config(state=NORMAL),
        lambda: window_controller.set_btn.config(state=NORMAL),
        lambda: gcode_btn.config(state=NORMAL),
        lambda: pause_event.clear(),
        lambda: pause_btn.config(text="PAUSE"),
        lambda: window_controller.print_msg("STOPPED THE TASK", "red"),
        lambda: window_controller.progress_text.config(fg="red"),
        lambda: run_btn.config(text="RUN"),
    ]

    window_controller.gcode_text
    run_command = lambda: thread_switch(
        raster_scan,
        start_event,
        (window_controller, device_list, run_btn, lock, start_event, pause_event),
        run_initial_funcs,
        run_final_funcs,
    )

    run_btn = create_button("RUN", run_command, 1, 10)

    # Pause Button Configuration
    pause_initial_funcs = [
        lambda: window_controller.print_msg("PAUSED THE TASK", "red"),
        lambda: pause_btn.config(text="RESUME"),
    ]

    pause_final_funcs = [
        lambda: window_controller.print_msg("RESUMED THE TASK", "green"),
        lambda: pause_btn.config(text="PAUSE"),
    ]

    pause_command = lambda: thread_switch(
        None, pause_event, None, pause_initial_funcs, pause_final_funcs
    )

    pause_btn = create_button("PAUSE", pause_command, 0, 10)

    # Extract Button Configuration
    extract_btn = create_button("EXTRACT", lambda: device.extract_axes(), 5, 10)

    # GCode Button Configuration
    gcode_initial_funcs = [
        lambda: extract_btn.config(state=DISABLED),
        lambda: window_controller.set_btn.config(state=DISABLED),
        lambda: run_btn.config(state=DISABLED),
        lambda: pause_event.set(),
        lambda: window_controller.print_msg("STARTED GCode", "green"),
        lambda: gcode_btn.config(text="STOP GCODE"),
    ]

    gcode_final_funcs = [
        lambda: extract_btn.config(state=NORMAL),
        lambda: window_controller.set_btn.config(state=NORMAL),
        lambda: run_btn.config(state=NORMAL),
        lambda: pause_event.clear(),
        lambda: pause_btn.config(text="PAUSE"),
        lambda: window_controller.print_msg("STOPPED GCode", "red"),
        lambda: gcode_btn.config(text="Start GCode"),
    ]

    gcode_command = lambda: thread_switch(
        Gcode,
        start_event,
        (
            window_controller.gcode_text.get("1.0", END),
            device_list,
            window_controller,
            gcode_btn,
            lock,
            start_event,
            pause_event,
        ),
        gcode_initial_funcs,
        gcode_final_funcs,
    )

    gcode_btn = create_button("Start GCode", gcode_command, 6, 3)

    window.mainloop()
