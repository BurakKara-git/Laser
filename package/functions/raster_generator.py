import package.constants as constants
from tkinter import *


def raster_generator(win, gcode_text, values):
    """
    Generates G-code for a raster scan and inserts it into a text widget.

    Args:
        win (Tk): The tkinter window instance.
        gcode_text (Text): The tkinter text widget where G-code will be inserted.
        values (list): A list containing:
            - initial_x (float): Initial X position.
            - initial_y (float): Initial Y position.
            - initial_z (float): Initial Z position.
            - initial_rot (float): Initial rotation (A-axis).
            - y_increment (float): Step size in Y direction.
            - dia (float): Total scan width in Y.
            - x_length (float): Length of scan in X (unused).
            - initial_vel (float): Initial velocity.

    Notes:
        - Limits the number of scan lines if velocity exceeds `MAX_X_VEL`.
        - Alternates X direction for each pass (zigzag pattern).
        - Inserts G-code into `gcode_text` and closes the window.
    """
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

    # Generate Raster Scan
    gCode = "G0 X{} Y{} Z{} A{};Initial Positions\n".format(
        initial_x, initial_y, initial_z, initial_rot
    )
    for i in range(total_task):
        if (i + passed) % 2 == 0:
            x_position = constants.X_MAX
        else:
            x_position = initial_x
        feed_rate = total_task - i
        y_position = initial_y + (i + 1) * y_increment

        if i == int(total_task / 2) + 1:
            gCode += ";PASSED\n"
            gCode += "G0 Y{}\n".format(y_position)
            passed += 1

        else:
            gCode += "G1 X{} F{}\n".format(x_position, feed_rate)
            gCode += "G0 Y{}\n".format(y_position)
    gCode += "G0 Z{};Unfocus\n".format(constants.Z_MAX)
    gCode += "G0 X{} Y{};Extract Axes\n".format(constants.X_MAX, constants.Y_MAX)
    gcode_text.delete("1.0", END)
    gcode_text.insert("end", gCode)
    win.destroy()
