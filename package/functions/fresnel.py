from zaber_motion import Measurement
from zaber_motion import Units
from zaber_motion.ascii import Axis
from package.classes.Ring import Ring
from package.classes.Device import Device
from package.classes.Point import Point
import package.constants as constants
import time, csv
import numpy as np
from typing import List
import threading


def Fresnel_new(
    axes: List[Axis],
    data,
    dt,
    LINEAR_VELOCITY,
    X_CENTER,
    Y_CENTER,
    INITIAL_Z,
    LINE_WIDTH,
    RADIUS_LIST,
    inclination,
    w_offset,
    R_RANGE,
    stop_event: threading.Event,
):
    if stop_event.is_set():
        return
    SEPARATION = LINE_WIDTH / 2
    max_t = (R_RANGE**2) * np.pi / (LINEAR_VELOCITY * SEPARATION)
    inclination = inclination * np.pi / 180

    # Generate times, angular and linear velocities
    times = np.arange(0, max_t + 1, dt)
    angular_velocity = np.sqrt(np.pi * LINEAR_VELOCITY / (SEPARATION * times))
    angular_velocity[angular_velocity > constants.MAX_ROT_VEL] = constants.MAX_ROT_VEL
    r_velocity = np.sqrt(LINEAR_VELOCITY * SEPARATION / (4 * times * np.pi))
    r_velocity[r_velocity > constants.MAX_X_VEL] = (
        np.sqrt(LINEAR_VELOCITY * SEPARATION * dt / np.pi) / dt
    )
    print(angular_velocity[0], r_velocity[0])
    V = np.sqrt(
        pow((angular_velocity * times * r_velocity * 2), 2) + pow(r_velocity, 2)
    )

    # Initialize devices
    axis_x = axes[0]
    axis_y = axes[1]
    axis_z = axes[2]
    axis_rot = axes[3]

    # Initial Positions
    axis_z.move_absolute(constants.Z_MAX, Units.LENGTH_MILLIMETRES)
    axis_x.move_absolute(X_CENTER, Units.LENGTH_MILLIMETRES)
    axis_y.move_absolute(Y_CENTER, Units.LENGTH_MILLIMETRES)
    axis_rot.home()

    # Wait Rotational axis to reach the speed
    axis_rot.move_velocity(
        constants.MAX_ROT_VEL, Units.ANGULAR_VELOCITY_RADIANS_PER_SECOND
    )
    time.sleep(1)

    # Get Initial Radians
    initial_radians = axis_rot.get_position(Units.ANGLE_RADIANS)

    # Focus/Unfocus Z
    is_focused = False
    if is_focused:
        axis_z.move_absolute(INITIAL_Z, Units.LENGTH_MILLIMETRES)
    else:
        axis_z.move_absolute(constants.Z_MAX, Units.LENGTH_MILLIMETRES)

    # Generate unfocus and stop sin command
    unfocus_command = axis_z.prepare_command(
        "move abs ?", Measurement(constants.Z_MAX, Units.LENGTH_MILLIMETRES)
    )
    stop_sin_command = axis_z.prepare_command("move sin stop")

    initial_sin_command = axis_z.prepare_command(
        "move sin ? ?",
        Measurement(0, Units.LENGTH_MILLIMETRES),
        Measurement(0.2, Units.TIME_MILLISECONDS),
    )

    # axis_z.generic_command_no_response(initial_sin_command)

    # Initial values
    start = time.time()
    radius_num = 0  # will start from second radius array
    current_rel_x = 0  # Current x position
    current_rel_radians = 0

    for i in range(len(times)):
        if stop_event.is_set():
            return
        # Check Focus
        if radius_num == len(RADIUS_LIST) - 1:
            if current_rel_x > RADIUS_LIST[radius_num][1]:
                is_focused = False
        elif current_rel_x > RADIUS_LIST[radius_num][1]:
            if current_rel_x < RADIUS_LIST[radius_num + 1][0]:
                is_focused = False
            else:
                is_focused = True
                radius_num += 1

        # Focus
        # axis_z.generic_command_no_response(stop_sin_command)
        if is_focused:
            z1_index = int(current_rel_x)
            try:
                z1_diff = data[z1_index][1]
            except:
                print("Reached Lens Profile")
                return
            # Calculate Focus Z
            z_c = (
                (current_rel_x * 1e-3)
                * inclination
                * np.cos(w_offset + current_rel_radians - initial_radians)
            )
            z1 = INITIAL_Z - z1_diff - z_c
            focus_command = axis_z.prepare_command(
                "move abs ?", Measurement(z1, Units.LENGTH_MILLIMETRES)
            )

            axis_z.generic_command_no_response(focus_command)
        else:
            z_c = 0
            z1 = constants.Z_MAX
            axis_z.generic_command_no_response(unfocus_command)

        amplitude = current_rel_x * 1e-3 * inclination
        period = round(1e3 * 2 * np.pi / angular_velocity[i], 1)
        sin_command = axis_z.prepare_command(
            "move sin ? ?",
            Measurement(amplitude, Units.LENGTH_MILLIMETRES),
            Measurement(period, Units.TIME_MILLISECONDS),
        )
        # axis_z.generic_command_no_response(sin_command)

        print(
            "x = {}, z = {}, z_c = {}, w = {}, v_r = {}, V = {}".format(
                current_rel_x, z1, z_c, angular_velocity[i], r_velocity[i], V[i]
            )
        )

        # Create Rotational and Linear axes commands
        cmd_rot = axis_rot.prepare_command(
            "move vel ?",
            Measurement(angular_velocity[i], Units.ANGULAR_VELOCITY_RADIANS_PER_SECOND),
        )
        cmd_x = axis_x.prepare_command(
            "move vel ?",
            Measurement(r_velocity[i], Units.VELOCITY_MILLIMETRES_PER_SECOND),
        )

        # Move axes
        axis_rot.generic_command_no_response(cmd_rot)
        axis_x.generic_command_no_response(cmd_x)
        time.sleep(dt)

        # Update position
        current_rel_x += r_velocity[i] * dt * 1000
        current_rel_radians += angular_velocity[i] * dt
    # Stop Axes
    end = time.time()
    axis_z.stop()
    axis_z.move_absolute(constants.Z_MAX, Units.LENGTH_MILLIMETRES)
    axis_rot.stop()
    axis_x.stop()

    # Print Results
    print("Elapsed Time = {}s".format(end - start))
    print(
        "RADIAN DIFFERENCE = {}".format(
            axis_rot.get_position(Units.ANGLE_RADIANS) - initial_radians
        )
    )
    print("FINAL X POSITION = {}".format(axis_x.get_position(Units.LENGTH_MILLIMETRES)))

    print("Calculated Time = {}".format(max_t))
    print("Calculated Radian Difference = {}".format(sum(angular_velocity * dt)))
    print("Calculated Final X Position = {}".format(X_CENTER + R_RANGE))

    return


def Fresnel_old(
    axes, data, X_CENTER, Y_CENTER, INITIAL_Z, RADIUS_LIST, stop_event: threading.Event
):
    if stop_event.is_set():
        return
    # Initialize Device
    axis_x = axes[0]
    axis_y = axes[1]
    axis_z = axes[2]
    axis_rot = axes[3]

    axis_z.move_absolute(constants.Z_MAX, Units.LENGTH_MILLIMETRES)
    axis_x.move_absolute(X_CENTER, Units.LENGTH_MILLIMETRES)
    axis_y.move_absolute(Y_CENTER, Units.LENGTH_MILLIMETRES)
    device = Device(*axes)

    # Calculate Angular Velocity
    def calculate_theta_velocity(linear_speed, r_velocity, r):
        if linear_speed <= r_velocity:
            return 0
        if r == 0:
            return np.inf
        else:
            return np.sqrt(linear_speed**2 - r_velocity**2) / r

    # Calculate and Simulate Spirals
    def calculate_path(RADIUS_LIST, R_VEL=0.02, LINEAR_VEL=100, view=False):

        r = 0
        theta = 0
        points = []
        theta_vels = []
        thetas = []
        rings = []

        for i in range(len(RADIUS_LIST)):
            r = RADIUS_LIST[i][0]
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            points.append(Point(x, y, INITIAL_Z))

            while r <= RADIUS_LIST[i][1]:
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                r += R_VEL
                theta_vel = calculate_theta_velocity(LINEAR_VEL, R_VEL, r)
                theta += theta_vel
                thetas.append(theta)
                theta_vels.append(theta_vel)
                points.append(Point(x, y, INITIAL_Z))

            # Calculate Z Positions
            z1_index = RADIUS_LIST[i][0]
            z2_index = RADIUS_LIST[i][1]

            # Get Z values in mm
            z1_diff = data[z1_index][1]
            z2_diff = data[z2_index][1]

            # Calculate Focus Z
            z1 = INITIAL_Z - z1_diff
            z2 = INITIAL_Z - z2_diff

            # Get R Positions in mm
            r1 = RADIUS_LIST[i][0] / 1000
            r2 = RADIUS_LIST[i][1] / 1000

            # Create Ring Object
            ring = Ring(r1, r2, z1, z2, R_VEL, LINEAR_VEL)
            rings.append(ring)

        return (points, thetas, theta_vels, rings)

    R_VEL = 0.02
    LINEAR_VEL = 40
    points, thetas, theta_vels, rings = calculate_path(
        RADIUS_LIST=RADIUS_LIST,
        R_VEL=R_VEL,
        LINEAR_VEL=LINEAR_VEL,
        view=False,
    )

    x_offset = X_CENTER
    r = []
    for point in points:
        r.append(point.r / 1000 + x_offset)

    start = time.time()
    for i in range(1):
        if stop_event.is_set():
            return

        ring = rings[i]
        x1 = ring.r1 + x_offset
        x2 = ring.r2 + x_offset
        w = ring.w2
        elapsed_time = abs(x2 - x1) / R_VEL
        print(
            "Time = {}, R1 = {}, R2 = {}, Angular Velocity = {}, Z = {}".format(
                elapsed_time, x1, x2, w, ring.z1
            )
        )

        # Start Rotational Movement
        device.axisrot.move_velocity(w, Units.ANGULAR_VELOCITY_RADIANS_PER_SECOND)

        # Go to Rings' X and Z Positions
        device.axisx.move_absolute(position=x1, unit=Units.LENGTH_MILLIMETRES)
        device.axisz.move_absolute(ring.z1, unit=Units.LENGTH_MILLIMETRES)

        # Start X Movement
        device.axisx.move_absolute(
            x2,
            Units.LENGTH_MILLIMETRES,
            True,
            R_VEL,
            Units.VELOCITY_MILLIMETRES_PER_SECOND,
        )

        # Set Z-Axis to Max Position (Unfocus) Will be changed to arduino switch
        device.axisz.move_absolute(constants.Z_MAX, unit=Units.LENGTH_MILLIMETRES)

        # Stop Rotational Movement
        device.axisrot.stop()

    end = time.time()
    print("Elapsed Tİme = {}".format(end - start))
    device.extract_axes()


def fresnel(
    device_list,
    dt,
    LINEAR_VELOCITY,
    X_CENTER,
    Y_CENTER,
    INITIAL_Z,
    inclination,
    w_offset,
    R_RANGE,
    LINE_WIDTH,
    RADIUS_LIST,
    lock: threading.Lock,
    stop_event: threading.Event,
    button,
):
    axes_list = [device.get_axis(1) for device in device_list]

    # Radial distance (m),Sag (m),Height (m)
    with open(constants.HEIGHT_PATH, encoding="utf-8-sig", mode="r") as file:
        csvFile = csv.reader(file, quoting=csv.QUOTE_NONNUMERIC)
        data = list(csvFile)

    # Convert m to mm with µm precision
    data = [[float("%.3f" % (j * 1000)) for j in i] for i in data]
    lock.acquire()
    if not stop_event.is_set():
        # Fresnel_old(axes_list, data, X_CENTER, Y_CENTER, INITIAL_Z, RADIUS_LIST,stop_event)
        Fresnel_new(
            axes_list,
            data,
            dt,
            LINEAR_VELOCITY,
            X_CENTER,
            Y_CENTER,
            INITIAL_Z,
            LINE_WIDTH,
            RADIUS_LIST,
            inclination,
            w_offset,
            R_RANGE,
            stop_event,
        )
    for axes in axes_list:
        axes.stop()
    axes_list[2].move_absolute(constants.Z_MAX, Units.LENGTH_MILLIMETRES)  # Unfocus
    lock.release()
    return
