from tkinter import Label, Tk, Button, Text
from tkinter.ttk import Progressbar, Combobox
import package.constants as constants
from package.classes.EntryWithPlaceholder import EntryWithPlaceholder


class WindowController:
    """
    Change/Set Window Components
    """

    def __init__(self, window: Tk):
        """Initializes the Stage Controller application.

        Sets up the main window with buttons, labels, entries, and progress bars for controlling
        a device using the provided Tkinter window.

        Args:
            device (Device): The device object to control.
            window (Tk): The Tkinter main window object.

        Returns:
            None
        """
        self.window = window
        window.title("Stage Controller")
        window.geometry("1280x720")

        self.lbl = Label(
            window,
            text="Stage Controller Is Ready",
            font=("Arial Bold", 20),
            fg="green",
        )
        self.lbl.grid(column=0, row=0)

        self.set_btn = Button(window, text="Set", command=lambda: self.setter())
        self.set_btn.grid(column=1, row=0)

        self.exit_btn = Button(
            self.window, text="EXIT", command=lambda: self.exit_button()
        )
        self.exit_btn.grid(column=3, row=0)

        self.set_initial_x = EntryWithPlaceholder(
            self.window, constants.INITIAL_X, "X", 1, 0
        )
        self.set_initial_y = EntryWithPlaceholder(
            self.window, constants.INITIAL_Y, "Y", 2, 0
        )
        self.set_initial_z = EntryWithPlaceholder(
            self.window, constants.INITIAL_Z, "Z", 3, 0
        )
        self.set_initial_rot = EntryWithPlaceholder(
            self.window, constants.INITIAL_ROT, "Rotation", 4, 0
        )
        self.set_y_increment = EntryWithPlaceholder(
            self.window, constants.INITIAL_INCREMENT, "Y increment", 5, 0
        )
        self.set_dia = EntryWithPlaceholder(
            self.window, constants.INITIAL_DIAMETER, "Diameter", 6, 0
        )
        self.set_x_length = EntryWithPlaceholder(
            self.window, constants.X_MAX, "X Length", 7, 0
        )
        self.set_initial_vel = EntryWithPlaceholder(
            self.window, constants.INITIAL_VELOCITY, "Initial Velocity", 8, 0
        )

        self.set_degree = Combobox(self.window)
        self.set_degree["values"] = constants.DEGREES
        self.set_degree.current(0)
        self.set_degree.grid(column=1, row=9)

        self.gcode_label = Label(window, text="GCode Input", font=("Arial Bold", 20))
        self.gcode_text = Text(window, height=5, width=52)
        self.gcode_label.grid(column=6, row=0)
        self.gcode_text.grid(column=6, row=1)
        self.gcode_text.insert("end", constants.GCODE_PLACEHOLDER)

        self.set_degree_text = Label(
            self.window, text="Degree", font=("Arial Bold", 20)
        )
        self.set_degree_text.grid(column=0, row=9)

        self.set_list = [
            self.set_initial_x,
            self.set_initial_y,
            self.set_initial_z,
            self.set_initial_rot,
            self.set_y_increment,
            self.set_dia,
            self.set_x_length,
            self.set_initial_vel,
            self.set_degree,
        ]

        # Initialize Progress Bar
        self.bar = Progressbar(
            self.window,
            length=constants.PROGRESS_BAR_LENGTH,
            style="black.Horizontal.TProgressbar",
        )
        self.bar["value"] = 0
        self.bar.grid(column=0, row=11)

        self.progress_text = Label(
            self.window, text="", font=("Arial Bold", 10), fg="green"
        )
        self.progress_text.grid(column=1, row=11)

    def destroy(self):
        """Destroys the main window of the Stage Controller application.

        Destroys the Tkinter main window, terminating the application.

        Returns:
            None
        """
        self.window.destroy()

    def exit_button(self):
        """Handler for the exit button of the Stage Controller application.

        Extracts axes positions from the device and destroys the main window,
        effectively terminating the application.

        Args:
            device (Device): The device object to extract axes positions from.

        Returns:
            None
        """
        #device.extract_axes()
        self.window.destroy()

    def get_values(self):
        """Returns current values from entry widgets.

        Returns a list of current numeric values retrieved from the entry widgets
        in the set_list attribute.

        Returns:
            list: A list containing the following float values:
                - Index 0: X position.
                - Index 1: Y position.
                - Index 2: Z position.
                - Index 3: Rotation.
                - Index 4: Increment.
                - Index 5: Diameter.
                - Index 6: X Length.
                - Index 7: Initial Velocity.
                - Index 8: Degree.
                - Index 9: Energy corresponding to the selected degree.
        """
        values = []
        for i in range(len(self.set_list)):
            values.append(float(self.set_list[i].get()))
        deg = values[8]
        energy = constants.ENERGIES[deg]
        values.append(energy)

        return values

    def config_progress_text(self, value, total):
        """Configures the progress text label.

        Updates the progress text label to display the current task and total tasks.

        Args:
            value (int): The current task number.
            total (int): The total number of tasks.

        Returns:
            None
        """
        self.progress_text.config(text="Task: {}/{}".format(value, total), fg="green")

    def print_msg(self, MSG, color):
        """Updates the label text and color.

        Updates the text and color of the label (`self.lbl`) with the provided message and color.

        Args:
            MSG (str): The message to display.
            color (str): The color to set for the label text.

        Returns:
            None
        """
        self.lbl.configure(text=MSG, fg=color)

    def position_msg(self, values):
        """Updates the message labels with new values.

        Clears existing message labels in columns 2 and 3, and then updates them
        with new labels based on the provided values.

        Args:
            values (list): A list of messages to display.

        Returns:
            None
        """
        # Destroy the previous Messages at column 2
        for widget in self.window.grid_slaves(column=2):
            if widget in self.window.grid_slaves(row=0):
                pass
            else:
                widget.destroy()

        # Destroy the previous Messages at column 3
        for widget in self.window.grid_slaves(column=3):
            if widget in self.window.grid_slaves(row=0):
                pass
            else:
                widget.destroy()

        # Print Set Messages
        for i in range(len(values) - 1):
            text = Label(self.window, font=("Arial Bold", 20), fg="green")
            text.configure(text=values[i])
            text.grid(column=2, row=i + 1)

        text_energy = Label(
            self.window,
            text="({} W)".format(values[9]),
            font=("Arial Bold", 20),
            fg="green",
        )
        text_energy.grid(column=3, row=9)

    def setter(self):
        self.print_msg("INITIAL VALUES ARE SET", "green")
    """
    def setter(self, device: Device):

        # Stop Axes
        device.stop_axes()

        # Get Initial Position Values
        values = self.get_values()

        # Configure Messages
        self.position_msg(values)

        # Move Axes
        initial_x = values[0]
        initial_y = values[1]
        initial_z = values[2]
        initial_rot = values[3]
        device.set_axes(initial_x, initial_y, initial_z, initial_rot)

        # Print Msg
        self.print_msg("INITIAL VALUES ARE SET", "green")
    
    """
    
