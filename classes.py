from tkinter import Entry, Label, Tk, Button
from tkinter.ttk import Progressbar, Combobox
from zaber_motion import Units, MotionLibException
from zaber_motion.ascii import Axis
import constants


class EntryWithPlaceholder(Entry):
    """
    Entry With PlaceHolder Class
    https://stackoverflow.com/questions/27820178/how-to-add-placeholder-to-an-entry-in-tkinter
    """

    def __init__(
        self,
        master=None,
        placeholder="PLACEHOLDER",
        axis="PLACEHOLDER",
        row=0,
        col=0,
        color="grey",
    ):
        """Initializes the widget with a placeholder and axis label.

        Args:
            master (Widget): The parent widget.
            placeholder (str): The placeholder text.
            axis (str): The axis label text.
            row (int): The row position in the grid. Defaults to 0.
            col (int): The column position in the grid. Defaults to 0.
            color (str): The placeholder text color. Defaults to 'grey'.

        Returns:
            None
        """
        super().__init__(master)

        initial_text = Label(master, text=axis, font=("Arial Bold", 20))
        initial_text.grid(column=col, row=row)
        self.grid(column=col + 1, row=row)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["fg"]

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        """Inserts placeholder text and sets its color.

        Inserts the placeholder text at the start and sets its color.

        Returns:
            None
        """
        self.insert(0, self.placeholder)
        self["fg"] = self.placeholder_color

    def foc_in(self, *args):
        """Removes placeholder text on focus.

        Deletes the placeholder text and resets the text color when the widget gains focus.

        Args:
            *args: Variable length argument list.

        Returns:
            None
        """
        if self["fg"] == self.placeholder_color:
            self.delete("0", "end")
            self["fg"] = self.default_fg_color

    def foc_out(self, *args):
        """Adds placeholder text on losing focus.

        Inserts the placeholder text if the widget is empty when it loses focus.

        Args:
            *args: Variable length argument list.

        Returns:
            None
        """

        if not self.get():
            self.put_placeholder()


class Device:
    """
    Create an object to control axes
    """

    def __init__(self, axisx: Axis, axisy: Axis, axisz: Axis, axisrot: Axis):
        """Initializes the class with axis objects.

        Args:
            axisx (Axis): The X-axis object.
            axisy (Axis): The Y-axis object.
            axisz (Axis): The Z-axis object.
            axisrot (Axis): The rotational axis object.

        Returns:
            None
        """
        self.axisx = axisx
        self.axisy = axisy
        self.axisz = axisz
        self.axisrot = axisrot
        self.axes = [self.axisx, self.axisy, self.axisz, self.axisrot]

    def get_current_positions(self):
        """Returns the current positions of all axes.

        Returns:
            list: A list containing the current positions of the axes:
                - Index 0: X position in millimeters (float).
                - Index 1: Y position in millimeters (float).
                - Index 2: Z position in millimeters (float).
                - Index 3: Rotation position in native units (float).
        """
        x_pos = self.axisx.get_position(Units.LENGTH_MILLIMETRES)
        y_pos = self.axisy.get_position(Units.LENGTH_MILLIMETRES)
        z_pos = self.axisz.get_position(Units.LENGTH_MILLIMETRES)
        rot_pos = self.axisrot.get_position(Units.NATIVE)
        return [x_pos, y_pos, z_pos, rot_pos]

    def extract_axes(self):
        """Moves the axes to their maximum positions.

        This method moves the z-axis, y-axis, and x-axis to their respective
        maximum positions defined in the `constants` module. The units used
        for the movements are millimeters.

        Returns:
            None
        """
        self.axisz.move_absolute(constants.Z_MAX, Units.LENGTH_MILLIMETRES)
        self.axisy.move_absolute(constants.Y_MAX, Units.LENGTH_MILLIMETRES)
        self.axisx.move_absolute(constants.X_MAX, Units.LENGTH_MILLIMETRES)

    def set_axes(self, x_pos, y_pos, z_pos, rot_pos):
        """Moves the axes to specified positions.

        Args:
            x_pos (float): The target position for the X-axis in millimeters.
            y_pos (float): The target position for the Y-axis in millimeters.
            z_pos (float): The target position for the Z-axis in millimeters.
            rot_pos (float): The target position for the rotational axis in native units.

        Returns:
            None
        """
        self.axisx.move_absolute(x_pos, Units.LENGTH_MILLIMETRES)
        self.axisy.move_absolute(y_pos, Units.LENGTH_MILLIMETRES)
        self.axisz.move_absolute(z_pos, Units.LENGTH_MILLIMETRES)
        self.axisrot.move_absolute(rot_pos, Units.NATIVE)

    def stop_axes(self):
        """Stops all axis movements.

        Stops the movement of the X, Y, Z axes, and the rotational axis.

        Returns:
            None
        """
        for axis in self.axes:
            axis.stop()

    def wait_axes(self):
        """Waits all axis movements.

        Waits the movement of the X, Y, Z axes, and the rotational axis.

        Returns:
            None
        """
        for axis in self.axes:
            axis.wait_until_idle()

    def move_try_except(
        self,
        axis: Axis,
        type: str,
        position: float,
        unit,
        wait_until_idle: bool = True,
        velocity: float = 0,
        velocity_unit=Units.NATIVE,
        acceleration: float = 0,
        acceleration_unit=Units.NATIVE,
    ):
        """
        Safely attempts to move an axis with specified parameters, handling any
        MotionLibException that may occur.

        Args:
        - axis (Axis): The axis to move.
        - type (str): The type of movement, such as 'move_absolute' or 'move_relative'.
        - position (float): The target position for the movement.
        - unit: The unit of measurement for the position.
        - wait_until_idle (bool, optional): Whether to wait until the axis is idle after the move. Default is True.
        - velocity (float, optional): The velocity for the movement. Default is 0.
        - velocity_unit (optional): The unit of measurement for the velocity. Default is Units.NATIVE.
        - acceleration (float, optional): The acceleration for the movement. Default is 0.
        - acceleration_unit (optional): The unit of measurement for the acceleration. Default is Units.NATIVE.

        Returns:
        - None

        This method tries to perform a movement operation on the given axis using the specified parameters.
        If a MotionLibException is encountered, the exception is caught, and the error message is printed.

        Example usage:
        ```python
        move_try_except(
            axis=my_axis,
            type='move_absolute',
            position=10.0,
            unit=Units.LENGTH_MILLIMETRES,
            velocity=5.0,
            velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND,
            acceleration=2.0,
            acceleration_unit=Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED
        )
        ```
        """
        try:
            movement = getattr(axis, type)
            movement(
                position=position,
                unit=unit,
                wait_until_idle=wait_until_idle,
                velocity=velocity,
                velocity_unit=velocity_unit,
                acceleration=acceleration,
                acceleration_unit=acceleration_unit,
            )

        except MotionLibException as err:
            print(err)


class WindowController:
    """
    Change/Set Window Components
    """

    def __init__(self, device: Device, window: Tk):
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

        self.set_btn = Button(window, text="Set", command=lambda: self.setter(device))
        self.set_btn.grid(column=1, row=0)

        self.exit_btn = Button(
            self.window, text="EXIT", command=lambda: self.exit_button(device)
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

    def exit_button(self, device: Device):
        """Handler for the exit button of the Stage Controller application.

        Extracts axes positions from the device and destroys the main window,
        effectively terminating the application.

        Args:
            device (Device): The device object to extract axes positions from.

        Returns:
            None
        """
        device.extract_axes()
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
            text="({} µJ)".format(values[9]),
            font=("Arial Bold", 20),
            fg="green",
        )
        text_energy.grid(column=3, row=9)

    def setter(self, device: Device):
        """Sets initial values and moves axes.

        Stops the axes, retrieves initial position values, updates message labels with these values,
        sets the axes to the initial positions, and prints a confirmation message.

        Args:
            device (Device): The device object to control.

        Returns:
            None
        """

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
