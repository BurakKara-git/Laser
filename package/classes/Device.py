from zaber_motion import Units, MotionLibException
from zaber_motion.ascii import Axis
import package.constants as constants


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
        self.axisrot.move_absolute(rot_pos, Units.ANGLE_RADIANS)

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

    def focus(self):
        """
        Moves the Z-axis to the initial focus position.

        This method calls the `move_try_except` function to move the Z-axis of the device
        to the predefined initial focus position specified by `constants.INITIAL_Z`.

        Parameters:
        None

        Usage:
        Call this method to set the Z-axis to the initial focus position, typically used
        for setting up the initial focus before starting other movements or operations.

        Example:
        ```python
        device.focus()
        ```

        Notes:
        - The `axis` parameter is set to `self.axisz`, representing the Z-axis of the device.
        - The `type` parameter is set to `"move_absolute"`, indicating an absolute move command.
        - The `position` parameter is set to `constants.INITIAL_Z`, specifying the target position.
        - The `unit` parameter is set to `Units.LENGTH_MILLIMETRES`, defining the unit of measurement.

        """
        self.move_try_except(
            axis=self.axisz,
            type="move_absolute",
            position=constants.INITIAL_Z,
            unit=Units.LENGTH_MILLIMETRES,
        )

    def un_focus(self):
        """
        Moves the Z-axis to the maximum Z position.

        This method calls the `move_try_except` function to move the Z-axis of the device
        to the predefined maximum Z position specified by `constants.Z_MAX`.

        Parameters:
        None

        Usage:
        Call this method to set the Z-axis to the maximum Z position, typically used
        for retracting the device to a safe position before starting or ending other operations.

        Example:
        ```python
        device.un_focus()
        ```

        Notes:
        - The `axis` parameter is set to `self.axisz`, representing the Z-axis of the device.
        - The `type` parameter is set to `"move_absolute"`, indicating an absolute move command.
        - The `position` parameter is set to `constants.Z_MAX`, specifying the target position.
        - The `unit` parameter is set to `Units.LENGTH_MILLIMETRES`, defining the unit of measurement.
        """
        self.move_try_except(
            axis=self.axisz,
            type="move_absolute",
            position=constants.Z_MAX,
            unit=Units.LENGTH_MILLIMETRES,
        )
