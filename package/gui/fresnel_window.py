from tkinter import *
import package.constants as constants
from package.functions.fresnel import fresnel
from package.classes.EntryWithPlaceholder import EntryWithPlaceholder
from package.gui.create_button import create_button
from package.functions.thread_switch import thread_switch
import threading

def fresnel_window(window, device_list):
    # Initialize Thread Events
    start_event = threading.Event()
    start_event.set()
    lock = threading.Lock()

    def get_value():
        radius_list = radius_list_generator(radius_list_text.get("1.0", END))
        values = []
        sets = [set_dt, set_LINEAR_VELOCITY, set_X_CENTER, set_Y_CENTER, set_INITIAL_Z, set_inclination, set_w_offset,set_R_RANGE]
        for set in sets:
            values.append(float(set.get()))
        values.append(radius_list)
        return values
    
    def radius_list_generator(radius_list_str: str):
        result=[]
        for radius in radius_list_str.split("\n")[:-1]:
            pre = []
            for element in radius.split(","):
                pre.append(float(element))
            result.append(pre)
        return result
    
    win = Toplevel()
    win.title("Fresnel")
    window_width = 1280
    window_height = 720

    # get screen dimension
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    # find the center point
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)

    # create the screen on window console
    win.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')


    #set_RADIUS_LIST
    set_X_CENTER = EntryWithPlaceholder(win, constants.X_CENTER, "X_Center", 1, 0)
    set_Y_CENTER = EntryWithPlaceholder(
        win, constants.Y_CENTER, "Y_Center", 2, 0
    )
    set_INITIAL_Z = EntryWithPlaceholder(
        win, constants.INITIAL_Z, "Initial Z", 3, 0
    )
    set_R_RANGE = EntryWithPlaceholder(
        win, constants.R_RANGE, "Range", 4, 0
    )
    set_LINEAR_VELOCITY = EntryWithPlaceholder(
        win, constants.LINEAR_VELOCITY, "Linear Velocity", 5, 0
    )
    set_inclination = EntryWithPlaceholder(
        win, constants.INCLINATION, "Inclination(Degrees)", 6, 0
    )
    set_w_offset = EntryWithPlaceholder(
        win, constants.W_OFFSET, "Angular Offset(Radians)", 7, 0
    )
    set_dt = EntryWithPlaceholder(
        win, constants.dt, "Time Step", 8, 0
    )

    radius_str = "\n".join(str(x)[1:-1] for x in constants.RADIUS_LIST)
    radius_list_label = Label(win, text="Radius List Input", font=("Arial Bold", 20))
    radius_list_text = Text(win, height=20, width=52)
    radius_list_label.grid(column=6, row=1)
    radius_list_text.grid(column=6, row=2)
    radius_list_text.insert("end", radius_str)

    # Fresnel Button Configuration
    fresnel_initial_funcs = [
        lambda: start_btn.config(text="STOP"),
    ]

    fresnel_final_funcs = [
        lambda: start_btn.config(text="START"),
    ]

    fresnel_command = lambda: thread_switch(
        fresnel,
        start_event,
        (device_list, *get_value(),lock,start_event),
        fresnel_initial_funcs,
        fresnel_final_funcs,
    )

    start_btn = create_button(win,"START",fresnel_command, 9,0)
