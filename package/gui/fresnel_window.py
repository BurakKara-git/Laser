from tkinter import *
import package.constants as constants
from package.functions.fresnel import fresnel
from package.classes.EntryWithPlaceholder import EntryWithPlaceholder
from package.gui.create_button import create_button
from package.functions.thread_switch import thread_switch
import threading

def fresnel_window(window, device_list):
    """
    Creates a Fresnel scanning control window using Tkinter.

    This function initializes a new Tkinter window with input fields for 
    setting Fresnel scanning parameters. It also includes a start/stop 
    button that runs the `fresnel` function in a separate thread.

    Args:
        window (Tk or Toplevel): The main Tkinter window or parent window.
        device_list (list): List of device objects to be controlled.

    Returns:
        None
    """
    
    # Initialize Thread Events for controlling the scanning process
    start_event = threading.Event()
    start_event.set()
    lock = threading.Lock()

    def get_value():
        """
        Retrieves user input values from the GUI and formats them for the Fresnel function.

        Returns:
            list: A list containing numerical values and the parsed radius list.
        """
        radius_list = radius_list_generator(radius_list_text.get("1.0", END))  # Parse radius list
        values = []
        sets = [
            set_dt, set_LINEAR_VELOCITY, set_X_CENTER, set_Y_CENTER, 
            set_INITIAL_Z, set_inclination, set_w_offset, set_R_RANGE, set_linewidth
        ]
        for set in sets:
            values.append(float(set.get()))  # Convert input values to float
        values.append(radius_list)  # Append parsed radius list
        return values
    
    def radius_list_generator(radius_list_str: str):
        """
        Parses the radius list input from the text box into a nested list.

        Args:
            radius_list_str (str): String representation of the radius list.

        Returns:
            list: A nested list of radius values.
        """
        result = []
        for radius in radius_list_str.split("\n")[:-1]:  # Process each line except the last empty one
            pre = [float(element) for element in radius.split(",")]  # Convert each value to float
            result.append(pre)
        return result
    
    # Create the Fresnel window
    win = Toplevel()
    win.title("Fresnel")

    # Window size configuration
    window_width = 1280
    window_height = 720
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    # Center the window on the screen
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    win.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    # Input fields for scanning parameters
    set_X_CENTER = EntryWithPlaceholder(win, constants.X_CENTER, "X Center", 1, 0)
    set_Y_CENTER = EntryWithPlaceholder(win, constants.Y_CENTER, "Y Center", 2, 0)
    set_INITIAL_Z = EntryWithPlaceholder(win, constants.INITIAL_Z, "Initial Z", 3, 0)
    set_R_RANGE = EntryWithPlaceholder(win, constants.R_RANGE, "Range", 4, 0)
    set_LINEAR_VELOCITY = EntryWithPlaceholder(win, constants.LINEAR_VELOCITY, "Linear Velocity", 5, 0)
    set_inclination = EntryWithPlaceholder(win, constants.INCLINATION, "Inclination (Degrees)", 6, 0)
    set_w_offset = EntryWithPlaceholder(win, constants.W_OFFSET, "Angular Offset (Radians)", 7, 0)
    set_dt = EntryWithPlaceholder(win, constants.dt, "Time Step", 8, 0)
    set_linewidth = EntryWithPlaceholder(win, constants.LINE_WIDTH, "Line Width (Separation=LW/2)", 9, 0)

    # Radius List Input
    radius_str = "\n".join(str(x)[1:-1] for x in constants.RADIUS_LIST)  # Convert list to formatted string
    radius_list_label = Label(win, text="Radius List Input", font=("Arial Bold", 20))
    radius_list_text = Text(win, height=20, width=52)

    # Position radius list elements
    radius_list_label.grid(column=2, row=1)
    radius_list_text.grid(column=2, row=2, rowspan=7)
    radius_list_text.insert("end", radius_str)  # Pre-fill with default values

    # Button Configuration for Fresnel Scanning
    fresnel_initial_funcs = [
        lambda: start_btn.config(text="STOP"),  # Update button text to indicate running state
    ]

    fresnel_final_funcs = [
        lambda: start_btn.config(text="START"),  # Reset button text when the process stops
    ]

    fresnel_command = lambda: thread_switch(
        fresnel,
        start_event,
        (device_list, *get_value(), lock, start_event, start_btn),
        fresnel_initial_funcs,
        fresnel_final_funcs,
    )

    # Create and place the Start/Stop button
    start_btn = create_button(win, "START", fresnel_command, 10, 0)
