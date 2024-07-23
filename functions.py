from tkinter import *
from zaber_motion import Units, MotionLibException
from zaber_motion.ascii import (
    WarningFlags,
    Device,
)
import time, threading, constants, classes, functions
import os, datetime, csv, cv2
from typing import List
from gcodeparser import GcodeParser
import math


# Logger
def logger(
    log_tail,
    n,
    energy,
    x_position,
    x_velocity,
    y_position,
    y_velocity,
    avg_x_velocity,
    initial_x,
    initial_y,
    initial_z,
    initial_rot,
):
    """Logs data into a list of lists.

    Appends a new log entry consisting of the provided data to the log_tail list,
    representing a log of various parameters over time.

    Args:
        log_tail (list): The list of lists containing logged data entries.
        n (int): The index or number associated with the log entry.
        energy (float): The energy value to log.
        x_position (float): The X-axis position to log.
        x_velocity (float): The X-axis velocity to log.
        y_position (float): The Y-axis position to log.
        y_velocity (float): The Y-axis velocity to log.
        avg_x_velocity (float): The average X-axis velocity to log.
        initial_x (float): The initial X-axis position to log.
        initial_y (float): The initial Y-axis position to log.
        initial_z (float): The initial Z-axis position to log.
        initial_rot (float): The initial rotational position to log.

    Returns:
        list: The updated log_tail list with the new log entry appended.
    """
    log = [
        n,
        energy,
        x_position,
        x_velocity,
        y_position,
        y_velocity,
        avg_x_velocity,
        initial_x,
        initial_y,
        initial_z,
        initial_rot,
    ]
    log_tail.append(log)
    return log_tail


# Write the File
def writer(log_head, log_tail):
    """Writes log data to a CSV file.

    Creates a CSV file named with the current date and time, stores it in a folder
    structure under 'Data' directory, and writes log data with a header and rows.

    Args:
        log_head (list): The header row for the CSV file.
        log_tail (list of lists): The list of data rows to write into the CSV file.

    Returns:
        None
    """
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{current_datetime}.csv"

    date_folder = datetime.datetime.now().strftime("%d-%m-%Y")
    folder = os.path.join("Data", date_folder)
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Define the full file path
    file_path = os.path.join(folder, filename)

    with open(file_path, "w", newline="\n") as f:
        write = csv.writer(f)
        write.writerow(log_head)
        write.writerows(log_tail)


# Switch for Threads
def thread_switch(main_function, start_event, args, initial_functions, final_functions):
    """Controls the switching of a thread's state.

    Executes initial functions, checks the state of a start event, and either starts
    a new thread with the main function or stops the current thread and executes final functions.

    Args:
        main_function (function): The main function to execute in a new thread.
        start_event (threading.Event): The event object controlling the thread's start state.
        args (tuple): Arguments to pass to the main function.
        initial_functions (list): List of functions to execute before starting the main function.
        final_functions (list): List of functions to execute after stopping the main function.

    Returns:
        None
    """
    for initial_function in initial_functions:
        initial_function()

    if start_event.is_set():
        start_event.clear()
        new_thread = threading.Thread(target=main_function, args=args)
        new_thread.daemon = True
        new_thread.start()
    else:
        start_event.set()
        for final_function in final_functions:
            final_function()
            for thread in threading.enumerate():
                try:
                    function_name = main_function.__name__
                    if thread.name.find(function_name) != -1:
                        print("Joining the Thread: " + thread.name)
                        thread.join(1)
                        thread = None
                except:
                    pass


# Change image to binary matrix
def img_2_mat(img_path):
    """Converts an image file to a binary thresholded matrix.

    Reads an image file from the specified path, rotates it 90 degrees counter-clockwise,
    applies a binary threshold to convert it to a binary image, and returns the thresholded matrix.

    Args:
        img_path (str): The file path to the image file.

    Returns:
        numpy.ndarray: The binary thresholded matrix representing the image.
    """

    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    ret, th = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    return th


# Run the task
def runner(
    window: classes.WindowController,
    device: classes.Device,
    button: Button,
    lock: threading.Lock,
    stop_event: threading.Event,
    resume_event: threading.Event,
):
    """Runs a series of tasks controlled by a GUI and synchronized with threading events.

    Executes a series of tasks involving movement of a device controlled by the provided window,
    using specified threading mechanisms for synchronization.

    Args:
        window (classes.WindowController): The GUI window controller object.
        device (classes.Device): The device object controlling physical movements.
        button (Button): The button to invoke upon task completion.
        lock (threading.Lock): The lock object for thread synchronization.
        stop_event (threading.Event): The event signaling to stop the task sequence.
        resume_event (threading.Event): The event signaling to resume or pause the task execution.

    Returns:
        None
    """
    log_tail = []
    values = window.get_values()
    initial_x = values[0]
    initial_y = values[1]
    initial_z = values[2]
    initial_rot = values[3]
    y_increment = values[4]
    dia = values[5]
    x_length = values[6]
    initial_vel = values[7]
    deg = values[8]
    energy = values[9]

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

    # Calculate Max Velocity
    max_velocity = initial_vel * total_task
    passed = 0
    count = 0

    lock.acquire()
    while not stop_event.is_set():
        while not resume_event.is_set():
            time.sleep(1)

        if count == total_task:
            writer(constants.log_head, log_tail)
            lock.release()
            button.invoke()
            return

        else:
            count += 1
            window.bar["value"] = (count / total_task) * 100
            window.config_progress_text(count, total_task)

            # Set Position and Velocities
            x_velocity = max_velocity - initial_vel * (count - passed)  # Fast to Slow
            # x_velocity = initial_vel*(count-passed) #Slow to Fast
            x_position = x_length * (-1) ** (count + 1 + passed)
            y_position = y_increment
            y_velocity = 0
            avg_x_velocity = "EMPTY"

            # Check Ranges
            current_positions = device.get_current_positions()

            if current_positions[0] + x_position > constants.X_MAX:
                writer(constants.log_head, log_tail)
                window.print_msg("Reached Max X Range", "red")
                lock.release()
                return

            if current_positions[0] + x_position < constants.X_MIN:
                writer(constants.log_head, log_tail)
                window.print_msg("Reached Min X Range", "red")
                lock.release()
                return

            if current_positions[1] + y_position > constants.Y_MAX:
                writer(constants.log_head, log_tail)
                window.print_msg("Reached Max Y Range", "red")
                lock.release()
                return

            if current_positions[1] + y_position < constants.Y_MIN:
                writer(constants.log_head, log_tail)
                window.print_msg("Reached Min Y Range", "red")
                lock.release()
                return

            # Start Movement
            if count != int(total_task / 2) + 1:
                start = time.time()

                try:
                    device.axisx.move_relative(
                        position=x_position,
                        unit=Units.LENGTH_MILLIMETRES,
                        velocity=x_velocity,
                        velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND,
                    )

                    end = time.time()
                    avg_x_velocity = x_length / (end - start)
                except MotionLibException as err:
                    print(err)
                    avg_x_velocity = "ERROR"

            # Pass The Middle Movement
            else:
                avg_x_velocity = "PASSED"
                passed += 1

            try:
                device.axisy.move_relative(
                    position=y_position,
                    unit=Units.LENGTH_MILLIMETRES,
                    velocity=y_velocity,
                    velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND,
                )
            except MotionLibException as err:
                print(err)
                avg_x_velocity = "ERROR"

            # Log the Task
            log_tail = functions.logger(
                log_tail,
                count,
                energy,
                x_position,
                x_velocity,
                y_position,
                y_velocity,
                avg_x_velocity,
                initial_x,
                initial_y,
                initial_z,
                initial_rot,
            )
            print("Task: {}/{}, {}".format(count, total_task, avg_x_velocity))

    writer(constants.log_head, log_tail)
    lock.release()
    return


# Check Device Health
def check_device(device: classes.Device, window: classes.WindowController):
    """Checks and monitors the device's warning flags.

    Continuously monitors the warning flags of all axes of the given device. If a critical
    system error or hardware emergency stop flag is detected, displays a warning message
    on the window indefinitely until the issue is resolved or acknowledged.

    Args:
        device (classes.Device): The device object to monitor.
        window (classes.WindowController): The window controller for displaying warning messages.

    Returns:
        None
    """
    axes = device.axes
    for axis in axes:
        warning_flags = axis.warnings.get_flags()
        if WarningFlags.CRITICAL_SYSTEM_ERROR in warning_flags:
            while True:
                window.print_msg("WARNING: CRITICAL SYSTEM ERROR!", "red")
                time.sleep(0.1)
        if WarningFlags.HARDWARE_EMERGENCY_STOP in warning_flags:
            while True:
                window.print_msg("WARNING: HARDWARE EMERGENCY STOP!", "red")
                time.sleep(0.1)
    time.sleep(10)


# Find Z-Axis Focus
def z_test(
    window: classes.WindowController,
    device: classes.Device,
    button: Button,
    lock: threading.Lock,
    stop_event: threading.Event,
    resume_event: threading.Event,
):
    """Performs a Z-axis test procedure.

    Moves the Z-axis of the device in incremental steps towards a minimum Z value while
    updating the progress bar and displaying current position. If stopped, it resumes
    when resumed event is set. Stops and returns if reached minimum Z or interrupted.

    Args:
        window (classes.WindowController): Window controller for UI updates.
        device (classes.Device): Device object controlling the axes.
        button (Button): Button object to invoke actions on completion.
        lock (threading.Lock): Lock to synchronize access to shared resources.
        stop_event (threading.Event): Event to signal stop request.
        resume_event (threading.Event): Event to signal resume after pause.

    Returns:
        None
    """
    initial_z = window.get_values()[2]
    lock.acquire()

    device.axisz.move_absolute(position=initial_z, unit=Units.LENGTH_MILLIMETRES)

    total_step = int((1 + initial_z - constants.Z_MIN) / constants.Z_TEST_STEP)

    if total_step <= 0:
        window.print_msg("SET HIGHER Z VALUE")
        return

    count = 0
    while not stop_event.is_set():
        while not resume_event.is_set():
            time.sleep(1)
        count += 1
        window.bar["value"] = (count) / (total_step) * 100
        window.config_progress_text(count, total_step)
        window.set_initial_z.delete("0", "end")
        window.set_initial_z.insert(
            0, str(device.axisz.get_position(unit=Units.LENGTH_MILLIMETRES))
        )
        new_pos = initial_z - count * constants.Z_TEST_STEP
        if new_pos <= constants.Z_MIN:
            device.axisz.move_absolute(
                position=constants.Z_MIN, unit=Units.LENGTH_MILLIMETRES
            )
            button.invoke()
            window.print_msg("REACHED MINIMUM Z AXIS", "red")
            lock.release()
            return
        else:
            device.axisz.move_absolute(position=new_pos, unit=Units.LENGTH_MILLIMETRES)
    final_z = device.axisz.get_position(unit=Units.LENGTH_MILLIMETRES)
    window.set_initial_z.delete("0", "end")
    window.set_initial_z.insert(0, str(final_z))
    window.position_msg(window.get_values()),
    lock.release()


# Print Matrix
def mat_print(
    device: classes.Device,
    window: classes.WindowController,
    button: Button,
    mat: list[list],
    lock: threading.Lock,
    stop_event: threading.Event,
    resume_event: threading.Event,
):
    """Prints a matrix using device movements based on threshold values.

    Moves the device axes to print a matrix on a surface, controlling movements
    based on threshold values in the matrix. Progress is displayed on the window.
    Stops if interrupted or when the stop button is pressed.

    Args:
        device (classes.Device): Device object controlling the axes.
        window (classes.WindowController): Window controller for UI updates.
        button (Button): Button object to invoke actions on completion.
        mat (list[list]): Matrix to print.
        lock (threading.Lock): Lock to synchronize access to shared resources.
        stop_event (threading.Event): Event to signal stop request.
        resume_event (threading.Event): Event to signal resume after pause.

    Returns:
        None
    """
    threshold = 0
    initial_positions = window.get_values()
    rows = len(mat)
    cols = len(mat[0])
    print("Matrix Dimension: ", rows, cols)

    x_step = (constants.X_MAX - initial_positions[0]) / rows
    y_step = (constants.Y_MAX - initial_positions[1]) / cols

    window.config_progress_text(0, rows * (cols - 1))

    lock.acquire()

    # unfocus
    device.axisz.move_absolute(position=constants.Z_MAX, unit=Units.LENGTH_MILLIMETRES)
    count = 0
    window.bar["value"] = 0

    def focus():
        # Focus
        try:
            device.axisz.move_absolute(
                position=initial_positions[2], unit=Units.LENGTH_MILLIMETRES
            )
        except MotionLibException as err:
            print(err)

    def un_focus():
        # Un-Focus
        try:
            device.axisz.move_absolute(
                position=constants.Z_MAX, unit=Units.LENGTH_MILLIMETRES
            )
        except MotionLibException as err:
            print(err)

    for row in range(0, rows):
        x_pos = x_step * row
        new_y_step = 0

        # move to positions
        try:
            device.axisx.move_relative(position=x_pos, unit=Units.LENGTH_MILLIMETRES)
            device.axisy.move_absolute(
                position=initial_positions[1], unit=Units.LENGTH_MILLIMETRES
            )
        except MotionLibException as err:
            print(err)

        for col in range(0, cols - 1):
            window.bar["value"] = ((count + 1) / (rows * (cols - 1))) * 100
            window.config_progress_text(count + 1, rows * (cols - 1))
            count += 1

            while not resume_event.is_set():
                time.sleep(1)

            # Return if Stop Button is Pressed
            if stop_event.is_set():
                un_focus()
                lock.release()
                return

            if mat[row][col] == threshold:
                new_y_step += y_step
            else:
                if new_y_step == 0:
                    pass
                else:
                    focus()
                    # Move Y-Axis
                    try:
                        device.axisy.move_relative(
                            position=new_y_step,
                            unit=Units.LENGTH_MILLIMETRES,
                            velocity=constants.MATRIX_VELOCITY,
                            velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND,
                        )
                    except MotionLibException as err:
                        print(err)

                    un_focus()
                    new_y_step = 0

        if new_y_step != 0:
            focus()
            # Move Y-Axis
            try:
                device.axisy.move_relative(
                    position=new_y_step,
                    unit=Units.LENGTH_MILLIMETRES,
                    velocity=constants.MATRIX_VELOCITY,
                    velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND,
                )
            except MotionLibException as err:
                print(err)
            un_focus()
        un_focus()
    un_focus()
    lock.release()
    button.invoke()
    return


# GCode(In Dev)
def GCode(
    gcode: str,
    device: classes.Device,
    window: classes.WindowController,
    button: Button,
    lock: threading.Lock,
    stop_event: threading.Event,
    resume_event: threading.Event,
):
    """
    Execute G-code instructions to control the motion of a device.

    Args:
    - gcode (str): The G-code instructions to execute.
    - device (classes.Device): The device to control, containing multiple axes.
    - window (classes.WindowController): The window controller to update UI elements.
    - button (Button): The button to invoke when execution is complete.
    - lock (threading.Lock): A threading lock to synchronize access.
    - stop_event (threading.Event): An event to signal stopping the execution.
    - resume_event (threading.Event): An event to signal resuming the execution.

    Returns:
    - None

    This function reads and parses G-code instructions, then executes the specified movements
    on the provided device. It updates the UI to reflect progress and handles stopping and resuming
    based on the provided events.

    Process:
    1. Parses the G-code into individual lines with movement commands.
    2. Iterates through each G-code line, calculating the required parameters for each axis.
    3. Adjusts the speed for each axis based on the provided feed rate.
    4. Calculates rotational speed if applicable.
    5. Executes the move commands for each axis.
    6. Updates the UI progress bar and text.
    7. Handles pausing and stopping the execution based on events.

    Example usage:
    ```python
    gcode = "G1 X10 Y20 Z5 F1500"
    GCode(gcode, device, window_controller, button, lock, stop_event, resume_event)
    ```

    Note:
    - The function assumes that `device` has methods `move_try_except` and `wait_axes`.
    - The `window` object should have methods `config_progress_text` and a `bar` attribute to update progress.
    - Error handling for file reading and movement execution is implemented.
    """
    # Parse G-code lines
    lines = GcodeParser(gcode).lines
    count = 0
    total_count = len(lines)
    lock.acquire()
    for line in lines:
        while not resume_event.is_set():
            time.sleep(1)

        # Return if Stop Button is Pressed
        if stop_event.is_set():
            lock.release()
            device.stop_axes()
            return
        count += 1
        window.bar["value"] = ((count) / total_count) * 100
        window.config_progress_text(count, total_count)
        speed = line.get_param("F") or 0

        # Get axis parameters
        axis_params = {
            "X": line.get_param("X"),
            "Y": line.get_param("Y"),
            "Z": line.get_param("Z"),
            "R": line.get_param("R"),
        }

        # Calculate total length for speed distribution
        total_len = math.sqrt(
            sum(
                (param or 0) ** 2 for param in axis_params.values() if param is not None
            )
        )

        # Calculate axis speeds
        axis_speeds = {
            axis: (param * speed / total_len if param is not None else 0)
            for axis, param in axis_params.items()
        }

        # Calculate rotational speed
        if axis_params["R"] is not None and speed != 0:
            positions = device.get_current_positions()
            radius = math.sqrt(
                (constants.X_CENTER - positions[0]) ** 2
                + (constants.Y_CENTER - positions[1]) ** 2
            )
            rot_speed = speed / radius if radius != 0 else 0
            rot_speed = min(rot_speed, constants.MAX_ROT_VEL)
        else:
            rot_speed = 0
        axis_speeds["R"] = rot_speed

        # Move commands dictionary
        move_commands = {
            "X": (
                "axisx",
                "move_absolute",
                Units.LENGTH_MILLIMETRES,
                Units.VELOCITY_MILLIMETRES_PER_SECOND,
            ),
            "Y": (
                "axisy",
                "move_absolute",
                Units.LENGTH_MILLIMETRES,
                Units.VELOCITY_MILLIMETRES_PER_SECOND,
            ),
            "Z": (
                "axisz",
                "move_absolute",
                Units.LENGTH_MILLIMETRES,
                Units.VELOCITY_MILLIMETRES_PER_SECOND,
            ),
            "R": (
                "axisrot",
                "move_relative",
                Units.ANGLE_RADIANS,
                Units.ANGULAR_VELOCITY_RADIANS_PER_SECOND,
            ),
        }

        # Execute commands
        for axis, (axis_attr, move_type, unit, velocity_unit) in move_commands.items():
            param = axis_params[axis]
            if param is not None:
                velocity = rot_speed if axis == "R" else speed
                device.move_try_except(
                    axis=getattr(device, axis_attr),
                    type=move_type,
                    position=param,
                    velocity=velocity,
                    unit=unit,
                    velocity_unit=velocity_unit,
                    wait_until_idle=False,
                )
        device.wait_axes()

    lock.release()
    button.invoke()
    return


# GUI
def stage_controller(device_list):
    """
    Sets up and controls a stage controller application with GUI using Tkinter,
    managing multiple devices for automation and testing purposes.

    Args:
    - device_list (list): A list containing four devices in the following order:
      [devicex, devicey, devicez, devicerot], each device having axes for movement.

    Returns:
    - None

    This function initializes a Tkinter window with buttons for controlling different
    automated tasks such as Z-test, running tasks, printing matrices, and extracting
    axes positions. It utilizes threading for concurrent task execution and handles
    synchronization using threading events and locks.

    The GUI allows interaction with the devices through the following buttons:
    - Z-Test: Executes a Z-axis testing procedure to move the Z-axis incrementally.
    - RUN/STOP: Initiates or stops a task running function that moves the X and Y axes.
    - PAUSE/RESUME: Pauses or resumes the current task execution.
    - Matrix Print: Prints a matrix pattern on a surface based on an image file.
    - GCode: Inititates the given GCode commands (In Dev)

    Additionally, the function includes a device health check thread to monitor and
    display warnings related to critical system errors or hardware emergency stops.
    """
    print(f"Found {len(device_list)} devices")

    # Initialize devices and axes
    axes_list = [device.get_axis(1) for device in device_list]
    device = classes.Device(*axes_list)

    # Initialize Thread Events
    start_event = threading.Event()
    start_event.set()
    pause_event = threading.Event()
    lock = threading.Lock()

    # Configure Main Window
    window = Tk()
    window_controller = classes.WindowController(device, window)

    # Check Device Health
    check_device_thread = threading.Thread(
        target=functions.check_device, args=(device, window_controller)
    )
    check_device_thread.daemon = True
    check_device_thread.start()

    # Utility function to create button and set grid position
    def create_button(text, command, column, row):
        btn = Button(window, text=text, command=command)
        btn.grid(column=column, row=row)
        return btn

    # Z-Test Button Configuration
    z_test_initial_funcs = [
        lambda: extract_btn.config(state=DISABLED),
        lambda: window_controller.set_btn.config(state=DISABLED),
        lambda: run_btn.config(state=DISABLED),
        lambda: mat_print_btn.config(state=DISABLED),
        lambda: pause_event.set(),
        lambda: window_controller.print_msg("STARTED Z TEST", "green"),
        lambda: z_test_btn.config(text="Stop Z-Test"),
    ]

    z_test_final_funcs = [
        lambda: extract_btn.config(state=NORMAL),
        lambda: window_controller.set_btn.config(state=NORMAL),
        lambda: run_btn.config(state=NORMAL),
        lambda: mat_print_btn.config(state=NORMAL),
        lambda: window_controller.print_msg("FINISHED Z TEST", "green"),
        lambda: z_test_btn.config(text="Start Z-Test"),
    ]

    z_test_command = lambda: functions.thread_switch(
        functions.z_test,
        start_event,
        (window_controller, device, z_test_btn, lock, start_event, pause_event),
        z_test_initial_funcs,
        z_test_final_funcs,
    )

    z_test_btn = create_button("Start Z-Test", z_test_command, 4, 3)

    # Run Button Configuration
    run_initial_funcs = [
        lambda: extract_btn.config(state=DISABLED),
        lambda: window_controller.set_btn.config(state=DISABLED),
        lambda: z_test_btn.config(state=DISABLED),
        lambda: mat_print_btn.config(state=DISABLED),
        lambda: gcode_btn.config(state=DISABLED),
        lambda: pause_event.set(),
        lambda: window_controller.setter(device),
        lambda: window_controller.print_msg("RUNNING THE TASK", "green"),
        lambda: window_controller.progress_text.config(fg="green"),
        lambda: run_btn.config(text="STOP"),
    ]

    run_final_funcs = [
        lambda: device.extract_axes(),
        lambda: extract_btn.config(state=NORMAL),
        lambda: window_controller.set_btn.config(state=NORMAL),
        lambda: z_test_btn.config(state=NORMAL),
        lambda: mat_print_btn.config(state=NORMAL),
        lambda: gcode_btn.config(state=NORMAL),
        lambda: pause_event.clear(),
        lambda: pause_btn.config(text="PAUSE"),
        lambda: window_controller.print_msg("STOPPED THE TASK", "red"),
        lambda: window_controller.progress_text.config(fg="red"),
        lambda: run_btn.config(text="RUN"),
    ]

    run_command = lambda: functions.thread_switch(
        functions.runner,
        start_event,
        (window_controller, device, run_btn, lock, start_event, pause_event),
        run_initial_funcs,
        run_final_funcs,
    )

    run_btn = create_button("RUN", run_command, 1, 10)

    # Pause Button Configuration
    pause_initial_funcs = [
        lambda: window_controller.print_msg("PAUSED THE TASK", "red"),
        lambda: pause_btn.config(text="RESUME"),
    ]

    pause_final_funcs = [
        lambda: window_controller.print_msg("RESUMED THE TASK", "green"),
        lambda: pause_btn.config(text="PAUSE"),
    ]

    pause_command = lambda: functions.thread_switch(
        None, pause_event, None, pause_initial_funcs, pause_final_funcs
    )

    pause_btn = create_button("PAUSE", pause_command, 0, 10)

    # Matrix Print Button Configuration
    mat = functions.img_2_mat(constants.IMAGE_PATH)
    mat_print_initial_funcs = [
        lambda: extract_btn.config(state=DISABLED),
        lambda: window_controller.set_btn.config(state=DISABLED),
        lambda: z_test_btn.config(state=DISABLED),
        lambda: run_btn.config(state=DISABLED),
        lambda: gcode_btn.config(state=DISABLED),
        lambda: window_controller.setter(device),
        lambda: pause_event.set(),
        lambda: window_controller.print_msg("PRINTING MATRIX", "green"),
        lambda: mat_print_btn.config(text="Stop Matrix Print"),
    ]

    mat_print_final_funcs = [
        lambda: device.extract_axes(),
        lambda: extract_btn.config(state=NORMAL),
        lambda: window_controller.set_btn.config(state=NORMAL),
        lambda: z_test_btn.config(state=NORMAL),
        lambda: run_btn.config(state=NORMAL),
        lambda: gcode_btn.config(state=NORMAL),
        lambda: pause_event.clear(),
        lambda: pause_btn.config(text="PAUSE"),
        lambda: window_controller.print_msg("STOPPED MATRIX", "red"),
        lambda: mat_print_btn.config(text="Start Matrix Print"),
    ]

    mat_print_command = lambda: functions.thread_switch(
        functions.mat_print,
        start_event,
        (device, window_controller, mat_print_btn, mat, lock, start_event, pause_event),
        mat_print_initial_funcs,
        mat_print_final_funcs,
    )

    mat_print_btn = create_button(
        "Start Matrix Print (IN DEVELOPMENT)", mat_print_command, 4, 10
    )

    # Extract Button Configuration
    extract_btn = create_button("EXTRACT", lambda: device.extract_axes(), 5, 10)

    # GCode Button Configuration
    gcode_initial_funcs = [
        lambda: extract_btn.config(state=DISABLED),
        lambda: window_controller.set_btn.config(state=DISABLED),
        lambda: z_test_btn.config(state=DISABLED),
        lambda: run_btn.config(state=DISABLED),
        lambda: mat_print_btn.config(state=DISABLED),
        lambda: pause_event.set(),
        lambda: window_controller.print_msg("STARTED GCode", "green"),
        lambda: gcode_btn.config(text="STOP GCODE"),
    ]

    gcode_final_funcs = [
        lambda: device.extract_axes(),
        lambda: extract_btn.config(state=NORMAL),
        lambda: window_controller.set_btn.config(state=NORMAL),
        lambda: z_test_btn.config(state=NORMAL),
        lambda: run_btn.config(state=NORMAL),
        lambda: mat_print_btn.config(state=NORMAL),
        lambda: pause_event.clear(),
        lambda: pause_btn.config(text="PAUSE"),
        lambda: window_controller.print_msg("STOPPED GCode", "red"),
        lambda: gcode_btn.config(text="Start GCode"),
    ]

    gcode_command = lambda: functions.thread_switch(
        functions.GCode,
        start_event,
        (
            window_controller.gcode_text.get("1.0", END),
            device,
            window_controller,
            gcode_btn,
            lock,
            start_event,
            pause_event,
        ),
        gcode_initial_funcs,
        gcode_final_funcs,
    )

    gcode_btn = create_button("Start GCode", gcode_command, 6, 3)

    window.mainloop()
