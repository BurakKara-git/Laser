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
    """
    Creates the main GUI window for controlling the stage.

    This function initializes a Tkinter window with buttons and text input fields
    to control different functionalities like characterization, Fresnel scanning,
    and GCode execution.

    Args:
        device_list (list): List of connected device objects.

    Returns:
        None
    """

    print(f"Found {len(device_list)} devices")

    # Initialize devices and extract axes
    axes_list = [device.get_axis(1) for device in device_list]
    device = Device(*axes_list)  # Create Device object with extracted axes

    # Initialize Thread Events for managing execution flow
    start_event = threading.Event()
    start_event.set()  # Ensures the main process starts
    pause_event = threading.Event()
    lock = threading.Lock()

    # Create the main GUI window
    window = Tk()
    window.title("Stage Controller")
    window.geometry("1280x720")  # Set window size

    # Characterization Button
    char_btn = create_button(
        window, "Characterisation", lambda: char_window(window, gcode_text), 1, 5
    )

    # Fresnel Scanning Button
    fresnel_btn = create_button(
        window, "Fresnel", lambda: fresnel_window(window, device_list), 2, 5
    )

    # GCode Input Field
    gcode_label = Label(window, text="GCode Input", font=("Arial Bold", 20))
    gcode_text = Text(window, height=5, width=52)

    # Position GCode elements in the grid
    gcode_label.grid(row=0, column=2)
    gcode_text.grid(row=1, column=1, columnspan=3, rowspan=2)
    gcode_text.insert("end", constants.GCODE_PLACEHOLDER)  # Pre-fill placeholder text

    # GCode Execution Button Configuration
    gcode_initial_funcs = [
        lambda: char_btn.config(state=DISABLED),  # Disable Characterization button
        lambda: extract_btn.config(state=DISABLED),  # Disable Extract button
        lambda: fresnel_btn.config(state=DISABLED),  # Disable Fresnel button
        lambda: pause_event.set(),  # Pause event activated
        lambda: gcode_btn.config(text="STOP GCODE"),  # Change button text to indicate running
    ]

    gcode_final_funcs = [
        lambda: char_btn.config(state=NORMAL),  # Enable Characterization button
        lambda: extract_btn.config(state=NORMAL),  # Enable Extract button
        lambda: fresnel_btn.config(state=NORMAL),  # Enable Fresnel button
        lambda: pause_event.clear(),  # Clear pause event
        lambda: pause_btn.config(text="PAUSE"),  # Reset pause button text
        lambda: gcode_btn.config(text="Start GCode"),  # Reset GCode button text
    ]

    gcode_command = lambda: thread_switch(
        Gcode,
        start_event,
        (
            gcode_text.get("1.0", END),  # Get GCode input
            device_list,
            gcode_btn,
            lock,
            start_event,
            pause_event,
        ),
        gcode_initial_funcs,
        gcode_final_funcs,
    )

    # Create GCode execution button
    gcode_btn = create_button(window, "Start GCode", gcode_command, 3, 2)

    # Pause/Resume Button Configuration
    pause_initial_funcs = [
        lambda: pause_btn.config(text="RESUME"),  # Change text to RESUME when paused
    ]

    pause_final_funcs = [
        lambda: pause_btn.config(text="PAUSE"),  # Change back to PAUSE when resumed
    ]

    pause_command = lambda: thread_switch(
        None, pause_event, None, pause_initial_funcs, pause_final_funcs
    )

    # Create Pause button
    pause_btn = create_button(window, "PAUSE", pause_command, 3, 1)

    # Extract Axes Button Configuration
    extract_btn = create_button(window, "EXTRACT", lambda: device.extract_axes(), 3, 3)

    # Run the Tkinter main event loop
    window.mainloop()
