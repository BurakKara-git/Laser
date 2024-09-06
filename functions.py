from tkinter import *
from zaber_motion import Units, MotionLibException, Measurement
from zaber_motion.ascii import WarningFlags, Device
from zaber_motion.gcode import Translator
from gcodeparser import GcodeParser
from turtle import Turtle, Screen
from random import random
import numpy as np
import time, threading, constants, classes, functions, os, datetime, csv, cv2, math
from typing import List


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


# Print Matrix (In Dev)
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


import pvt_test


# PVT (in dev)
def PVT(device_list: List[Device]):

    # Get the first axis from each device
    axis_list = [device.get_axis(1) for device in device_list]
    all_devices = classes.Device(*axis_list)

    # Retrieve PVT sequences and buffers for each device
    pvt_sequence_list = [device.pvt.get_sequence(1) for device in device_list]
    pvt_buffer_list = [device.pvt.get_buffer(1) for device in device_list]

    # Disable all PVT sequences
    for pvt_seq in pvt_sequence_list:
        pvt_seq.disable()

    # Erase all PVT buffers
    for pvt_buffer in pvt_buffer_list:
        pvt_buffer.erase()

    # Setup store for each PVT sequence
    for i in range(len(pvt_sequence_list)):
        pvt_sequence_list[i].setup_store(pvt_buffer_list[i], 1)

    # Generate PVT points sequence
    generated_sequence = pvt_test.pvt_points()

    # Set initial axes positions and wait for completion
    initial_positions = [generated_sequence.points[0].position[i] for i in range(3)] + [
        0
    ]
    all_devices.set_axes(*initial_positions)
    all_devices.wait_axes()

    # Add points to each PVT sequence
    for point in generated_sequence.points[1:]:
        for i in range(3):
            print("adding points")
            pvt_sequence_list[i].point(
                [
                    Measurement(point.position[i], Units.LENGTH_MILLIMETRES),
                ],
                [
                    Measurement(
                        point.velocity[i], Units.VELOCITY_MILLIMETRES_PER_SECOND
                    ),
                ],
                Measurement(point.time, Units.TIME_SECONDS),
            )

    # Disable all PVT sequences
    for i in range(len(pvt_sequence_list)):
        pvt_sequence_list[i].disable()

    # Setup live mode and call each sequence with its buffer
    for i in range(len(pvt_sequence_list)):
        pvt_sequence_list[i].setup_live(1)
        pvt_sequence_list[i].call(pvt_buffer_list[i])
    return


# Fresnel Rings(In Dev)
def Fresnel(device_list: List[Device]):
    # Initialize Device
    axes_list = [device.get_axis(1) for device in device_list]
    device = classes.Device(*axes_list)
    device.set_axes(constants.X_CENTER, constants.Y_CENTER, constants.INITIAL_Z, 0)

    # Radial distance (m),Sag (m),Height (m)
    with open(constants.HEIGHT_PATH, encoding="utf-8-sig", mode="r") as file:
        csvFile = csv.reader(file, quoting=csv.QUOTE_NONNUMERIC)
        data = list(csvFile)

    # Convert m to mm with µm precision
    data = [[float("%.3f" % (j * 1000)) for j in i] for i in data]

    # Calculate Angular Velocity
    def calculate_theta_velocity(linear_speed, r_velocity, r):
        if linear_speed <= r_velocity:
            return 0
        if r == 0:
            return np.inf
        else:
            return math.sqrt(linear_speed**2 - r_velocity**2) / r

    # Calculate and Simulate Spirals
    def calculate_path(RADIUS_LIST, R_VEL=0.02, LINEAR_VEL=100, view=False):
        if view:
            screen = Screen()
            WIDTH, HEIGHT = screen.window_width(), screen.window_height()
            turtle = Turtle(visible=False)
            turtle.speed("fastest")
            turtle.up()
            turtle.goto(0, 0)
            turtle.down()

        r = 0
        theta = 0
        points = []
        theta_vels = []
        thetas = []
        rings = []

        for i in range(len(RADIUS_LIST)):
            r = RADIUS_LIST[i][0]
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            points.append(classes.Point(x, y, constants.INITIAL_Z))

            if view:
                turtle.up()
                turtle.goto(x / 10, y / 10)
                turtle.color(random(), random(), random())
                turtle.down()

            while r <= RADIUS_LIST[i][1]:
                x = r * math.cos(theta)
                y = r * math.sin(theta)
                r += R_VEL
                theta_vel = calculate_theta_velocity(LINEAR_VEL, R_VEL, r)
                theta += theta_vel
                thetas.append(theta)
                theta_vels.append(theta_vel)
                points.append(classes.Point(x, y, constants.INITIAL_Z))

                if view:
                    linear_vel = math.sqrt(R_VEL**2 + (r * theta_vel) ** 2)
                    print(
                        "Linear Velocity = {}, Rotation Velocity = {}".format(
                            linear_vel, theta_vel
                        )
                    )
                    turtle.goto(x / 10, y / 10)

            # Calculate Z Positions
            z1_index = RADIUS_LIST[i][0]
            z2_index = RADIUS_LIST[i][1]

            z1_diff = data[z1_index][1]
            z2_diff = data[z2_index][1]

            z1 = constants.INITIAL_Z - z1_diff
            z2 = constants.INITIAL_Z - z2_diff

            # Get R Positions
            r1 = RADIUS_LIST[i][0] / 1000
            r2 = RADIUS_LIST[i][1] / 1000

            # Create Ring Object
            ring = classes.Ring(r1, r2, z1, z2, R_VEL, LINEAR_VEL)
            rings.append(ring)

        if view:
            turtle.up()
            screen.exitonclick()

        return (points, thetas, theta_vels, rings)

    R_VEL = 0.1
    LINEAR_VEL = 20
    points, thetas, theta_vels, rings = calculate_path(
        RADIUS_LIST=constants.RADIUS_LIST,
        R_VEL=R_VEL,
        LINEAR_VEL=LINEAR_VEL,
        view=False,
    )

    x_offset = constants.X_CENTER
    r = []
    for point in points:
        r.append(point.r / 1000 + x_offset)

    threads = []
    device.axisz.move_absolute(constants.Z_MAX, unit=Units.LENGTH_MILLIMETRES)
    for i in range(len(rings)):
        ring = rings[i]
        x1 = ring.r1 + x_offset
        x2 = ring.r2 + x_offset
        time = (x2 - x1) / R_VEL
        print(
            "Time = {}, R1 = {}, R2 = {}, Angular Velocity = {}".format(
                time, x1, x2, ring.w
            )
        )

        device.axisx.move_absolute(position=x1, unit=Units.LENGTH_MILLIMETRES)
        device.axisz.move_absolute(ring.z1, unit=Units.LENGTH_MILLIMETRES)

        rot_t = threading.Thread(
            target=device.axisrot.move_relative,
            args=(
                ring.w * time,
                Units.ANGLE_RADIANS,
                True,
                ring.w,
                Units.ANGULAR_VELOCITY_RADIANS_PER_SECOND,
            ),
        )

        x_t = threading.Thread(
            target=device.axisx.move_absolute,
            args=(
                x2,
                Units.LENGTH_MILLIMETRES,
                True,
                R_VEL,
                Units.VELOCITY_MILLIMETRES_PER_SECOND,
            ),
        )

        threads.append(rot_t)
        threads.append(x_t)
        rot_t.start()
        x_t.start()

        for t in threads:
            t.join()

        device.axisz.move_absolute(constants.Z_MAX, unit=Units.LENGTH_MILLIMETRES)


# GCode(In Dev)
def GCode(
    gcode: str,
    device_list: List[Device],
    window: classes.WindowController,
    button: Button,
    lock: threading.Lock,
    stop_event: threading.Event,
    resume_event: threading.Event,
):
    """
    Executes G-code commands on a list of devices, controlling their movements
    based on the parsed G-code instructions.

    Parameters:
    - gcode (str): The G-code string containing the movement commands.
    - device_list (List[Device]): List of Device objects representing the axes to be controlled.
    - window (classes.WindowController): The window controller for updating UI elements.
    - button (Button): Button to invoke upon completion or error.
    - lock (threading.Lock): Thread lock to control access to shared resources.
    - stop_event (threading.Event): Event to signal stopping the execution.
    - resume_event (threading.Event): Event to signal resuming the execution.

    This function performs the following steps:
    1. Parses the G-code lines.
    2. Sets up the device streams and translators.
    3. Iterates over the parsed G-code lines, controlling the devices accordingly.
    4. Updates the progress bar and text in the UI.
    5. Handles threading for concurrent execution of commands.
    6. Waits for threads to complete and then flushes translators and disables streams.
    7. Releases the lock and invokes the button upon completion or if an error occurs.

    Internal helper functions:
    - axis_stream(translator: Translator, command: str): Sends a command to a specific translator.
    - calculate_speeds(axis_params, previous_positions, speed): Calculates the speeds for each axis based on the parameters.
    - setup_devices(): Sets up the device streams and translators.

    Example usage:
    ```python
    GCode(gcode_str, device_list, window_controller, button, lock, stop_event, resume_event)
    ```

    Note:
    - The function prints and updates the UI in case of errors.
    """

    def axis_stream(translator: Translator, command: str):
        print(f"Command: {command}, Translator: {translator}")
        try:
            translator.translate(command)
            translator.flush()
        except MotionLibException as err:
            window.print_msg("Wrong Command", "red")
            print(f"Wrong Command: {command}.")
            print(err)
        finally:
            return

    def calculate_speeds(axis_params, previous_positions, speed):
        check = ["X", "Y", "Z"]
        position_differences = [0, 0, 0]
        pre_sum = 0
        axis_speeds = {axis: 0 for axis in axis_params}

        for i in range(3):
            param, _ = axis_params[check[i]]
            if param is not None:
                dif = abs(previous_positions[i] - param)
                position_differences[i] = dif
                pre_sum += dif**2

        total_len = math.sqrt(pre_sum)

        for i in range(3):
            param, _ = axis_params[check[i]]
            if param is not None:
                axis_speeds[check[i]] = (
                    (position_differences[i] * speed / total_len)
                    if total_len != 0
                    else 0
                )

        param_a, _ = axis_params["A"]
        if param_a is not None and speed != 0:
            radius = math.sqrt(
                (constants.X_CENTER - previous_positions[0]) ** 2
                + (constants.Y_CENTER - previous_positions[1]) ** 2
            )
            rot_speed = speed / radius if radius != 0 else 0
            rot_speed = min(rot_speed, constants.MAX_ROT_VEL)
        else:
            rot_speed = 0
        axis_speeds["A"] = rot_speed * 57.2957795

        return axis_speeds

    def setup_devices():
        try:
            axis_list = [device.get_axis(1) for device in device_list]
            stream_list = [device.streams.get_stream(1) for device in device_list]
            for stream in stream_list:
                stream.setup_live(1)
            translator_list = [Translator.setup(stream) for stream in stream_list]
            return axis_list, stream_list, translator_list
        except MotionLibException as err:
            print(err)
            window.print_msg("ERROR - TASK IS ABORTED!", "red")
            lock.release()
            button.invoke()
            return None, None, None

    axis_list, stream_list, translator_list = setup_devices()
    lock.acquire()
    lines = GcodeParser(gcode).lines
    total_count = len(lines)
    all_devices = classes.Device(*axis_list)
    threads = []

    count = 0
    for line in lines:
        while not resume_event.is_set():
            time.sleep(1)
            if stop_event.is_set():
                break
        if stop_event.is_set():
            break
        count += 1
        window.bar["value"] = (count / total_count) * 100
        window.config_progress_text(count, total_count)

        axis_params = {
            "X": (line.get_param("X"), translator_list[0]),
            "Y": (line.get_param("Y"), translator_list[1]),
            "Z": (line.get_param("Z"), translator_list[2]),
            "A": (line.get_param("A"), translator_list[3]),
        }
        print(line.comment)
        speed = (line.get_param("F") or 0) * 60

        previous_positions = all_devices.get_current_positions()
        axis_speeds = calculate_speeds(axis_params, previous_positions, speed)

        if all(param is None for param, _ in axis_params.values()):
            command = line.command_str
            if command in {"M3", "M4"}:
                command = f"G90 G0 X{constants.Z_MAX}"
                thread = threading.Thread(
                    target=axis_stream, args=(translator_list[2], command)
                )
                threads.append(thread)
                thread.start()
            elif command == "M5":
                command = f"G90 G0 X{constants.INITIAL_Z}"
                thread = threading.Thread(
                    target=axis_stream, args=(translator_list[2], command)
                )
                threads.append(thread)
                thread.start()
            else:
                for i in range(4):
                    thread = threading.Thread(
                        target=axis_stream, args=(translator_list[i], command)
                    )
                    threads.append(thread)
                    thread.start()
        else:
            non_none_params = {
                axis: (param, translator)
                for axis, (param, translator) in axis_params.items()
                if param is not None
            }
            for axis, (param, translator) in non_none_params.items():
                if axis == "A":
                    command = f"G91 {line.command_str} X{param*57.2957795}"
                else:
                    command = f"G90 {line.command_str} X{param}"
                if line.get_param("F") is not None and axis_speeds[axis] != 0:
                    command += f" F{axis_speeds[axis]}"
                elif line.get_param("F") is not None and axis_speeds[axis] == 0:
                    continue
                thread = threading.Thread(
                    target=axis_stream, args=(translator, command)
                )
                thread.daemon = True
                threads.append(thread)
                thread.start()
        all_devices.wait_axes()

    for translator in translator_list:
        translator.flush()
    for stream in stream_list:
        if not stream.check_disabled():
            stream.disable()
    all_devices.stop_axes()
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
            device_list,
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
