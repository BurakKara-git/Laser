from tkinter import *
import package.constants as constants
from package.functions.raster_generator import raster_generator
from package.classes.EntryWithPlaceholder import EntryWithPlaceholder
from package.gui.create_button import create_button

def char_window(window, gcode_text):
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

    create_button(win,"GENERATE",lambda: raster_generator(win, gcode_text, get_value()), 9, 0)
