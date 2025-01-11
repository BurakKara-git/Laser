from tkinter import *
import package.constants as constants
from package.classes.EntryWithPlaceholder import EntryWithPlaceholder
from package.classes.Device import Device
import threading
from package.functions.thread_switch import thread_switch
from package.functions.gCode import Gcode

def raster(win, gcode_text, values):
    initial_x = values[0]
    initial_y = values[1]
    initial_z = values[2]
    initial_rot = values[3]
    y_increment = values[4]
    dia = values[5]
    x_length = values[6]
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
    gCode = "G0 X{} Y{} Z{} A{};Initial Positions\n".format(initial_x,initial_y,initial_z, initial_rot)
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
    gCode += "G0 Z{};Unfocus\n".format(constants.Z_MAX)    
    gCode += "G0 X{} Y{};Extract Axes\n".format(constants.X_MAX, constants.Y_MAX)  
    gcode_text.delete('1.0', END)
    gcode_text.insert("end", gCode)
    win.destroy()

def create_button(window, text, command, column, row):
        btn = Button(window, text=text, command=command)
        btn.grid(column=column, row=row)
        return btn


def new_window(window, gcode_text):
    def get_value():
        values = []
        sets = [set_initial_x, set_initial_y, set_initial_z, set_initial_rot, set_y_increment, set_dia, set_x_length, set_initial_vel]
        for set in sets:
            values.append(float(set.get()))
        return values
    
    win = Toplevel()
    win.title("New Window")
    window_width = 400
    window_height = 720

    # get screen dimension
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    # find the center point
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)

    # create the screen on window console
    win.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    set_initial_x = EntryWithPlaceholder(win, constants.INITIAL_X, "X", 1, 0)
    set_initial_y = EntryWithPlaceholder(
        win, constants.INITIAL_Y, "Y", 2, 0
    )
    set_initial_z = EntryWithPlaceholder(
        win, constants.INITIAL_Z, "Z", 3, 0
    )
    set_initial_rot = EntryWithPlaceholder(
        win, constants.INITIAL_ROT, "Rotation", 4, 0
    )
    set_y_increment = EntryWithPlaceholder(
        win, constants.INITIAL_INCREMENT, "Y increment", 5, 0
    )
    set_dia = EntryWithPlaceholder(
        win, constants.INITIAL_DIAMETER, "Diameter", 6, 0
    )
    set_x_length = EntryWithPlaceholder(
        win, constants.X_MAX, "X Length", 7, 0
    )
    set_initial_vel = EntryWithPlaceholder(
        win, constants.INITIAL_VELOCITY, "Initial Velocity", 8, 0
    )

    create_button(win,"GENERATE",lambda: raster(win, gcode_text, get_value()), 9, 0)

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

    gcode_label = Label(window, text="GCode Input", font=("Arial Bold", 20))
    gcode_text = Text(window, height=5, width=52)
    gcode_label.grid(column=5, row =5)
    gcode_text.grid(column=5, row =6)
    gcode_text.insert("end", constants.GCODE_PLACEHOLDER)

    
    char_btn = create_button(window, "Characterisation", lambda:new_window(window, gcode_text),0,1)

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

    pause_btn = create_button(window, "PAUSE", pause_command, 0, 10)

    # Extract Button Configuration
    extract_btn = create_button(window, "EXTRACT", lambda: device.extract_axes(), 5, 10)
    
    
    # GCode Button Configuration
    gcode_initial_funcs = [
        lambda: pause_event.set(),
        lambda: gcode_btn.config(text="STOP GCODE"),
    ]

    gcode_final_funcs = [
        lambda: extract_btn.config(state=NORMAL),
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

    gcode_btn = create_button(window, "Start GCode", gcode_command, 6, 3)

    window.mainloop()
    