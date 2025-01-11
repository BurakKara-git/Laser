from zaber_motion import Units
from zaber_motion.ascii import Device as ZaberDevice
from turtle import Turtle, Screen
from random import random
from typing import List
import numpy as np
import package.constants as constants
from package.classes.Device import Device
from package.classes.Point import Point
from package.classes.Ring import Ring
import time, csv, math


def fresnel(device_list: List[ZaberDevice]):
    # Initialize Device
    axes_list = [device.get_axis(1) for device in device_list]
    device = Device(*axes_list)
    device.set_axes(constants.X_CENTER, constants.Y_CENTER, constants.Z_MAX, 0)
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
            points.append(Point(x, y, constants.INITIAL_Z))

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
                points.append(Point(x, y, constants.INITIAL_Z))

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

            # Get Z values in mm
            z1_diff = data[z1_index][1]
            z2_diff = data[z2_index][1]

            # Calculate Focus Z
            z1 = constants.INITIAL_Z - z1_diff
            z2 = constants.INITIAL_Z - z2_diff

            # Get R Positions in mm
            r1 = RADIUS_LIST[i][0] / 1000
            r2 = RADIUS_LIST[i][1] / 1000

            # Create Ring Object
            ring = Ring(r1, r2, z1, z2, R_VEL, LINEAR_VEL)
            rings.append(ring)

        if view:
            turtle.up()
            screen.exitonclick()

        return (points, thetas, theta_vels, rings)

    R_VEL = 0.02
    LINEAR_VEL = 40
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

    start = time.time()
    for i in range(len(rings)):
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
        #device.axisz.move_absolute(ring.z1, unit=Units.LENGTH_MILLIMETRES)
        device.axisz.move_absolute(constants.INITIAL_Z, unit=Units.LENGTH_MILLIMETRES)

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
