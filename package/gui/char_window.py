from tkinter import *
import package.constants as constants
from package.functions.raster_generator import raster_generator
from package.classes.EntryWithPlaceholder import EntryWithPlaceholder
from package.gui.create_button import create_button

def char_window(window, gcode_text):
    """
    Creates a new window for user input to configure raster scanning parameters.

    This function generates a Tkinter `Toplevel` window where users can input values
    for raster scanning, such as initial X, Y, Z positions, rotation, Y increment, 
    diameter, X length, and velocity. Once the values are set, the user can click 
    the "GENERATE" button to execute `raster_generator` with the provided inputs.

    Args:
        window (Tk): The main Tkinter window from which this new window is spawned.
        gcode_text (Text): A Tkinter Text widget where generated G-code will be displayed.

    Returns:
        None

    Notes:
        - The function centers the new window on the screen.
        - Default values are fetched from `constants` and displayed in `EntryWithPlaceholder` fields.
        - The "GENERATE" button triggers `raster_generator` with the user-defined values.
    """

    def get_value():
        """
        Retrieves user input values from the entry fields.

        Returns:
            list: A list of float values representing the user-defined raster scan parameters.
        """
        values = []
        sets = [set_initial_x, set_initial_y, set_initial_z, set_initial_rot, 
                set_y_increment, set_dia, set_x_length, set_initial_vel]
        for set in sets:
            values.append(float(set.get()))  # Convert input to float and store in list
        return values

    # Create a new top-level window
    win = Toplevel()
    win.title("Raster Scan Configuration")

    # Define window dimensions
    window_width = 400
    window_height = 720

    # Get screen dimensions
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    # Calculate center position
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)

    # Set window position to center
    win.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    # Create input fields with placeholders
    set_initial_x = EntryWithPlaceholder(win, constants.INITIAL_X, "X", 1, 0)
    set_initial_y = EntryWithPlaceholder(win, constants.INITIAL_Y, "Y", 2, 0)
    set_initial_z = EntryWithPlaceholder(win, constants.INITIAL_Z, "Z", 3, 0)
    set_initial_rot = EntryWithPlaceholder(win, constants.INITIAL_ROT, "Rotation", 4, 0)
    set_y_increment = EntryWithPlaceholder(win, constants.INITIAL_INCREMENT, "Y increment", 5, 0)
    set_dia = EntryWithPlaceholder(win, constants.INITIAL_DIAMETER, "Diameter", 6, 0)
    set_x_length = EntryWithPlaceholder(win, constants.X_MAX, "X Length", 7, 0)
    set_initial_vel = EntryWithPlaceholder(win, constants.INITIAL_VELOCITY, "Initial Velocity", 8, 0)

    # Create the "GENERATE" button to start raster generation
    create_button(win, "GENERATE", lambda: raster_generator(win, gcode_text, get_value()), 9, 0)
