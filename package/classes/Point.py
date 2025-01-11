import math

class Point:
    """
    A class to represent a 3D point in Cartesian, Polar, and Cylindrical coordinates.

    Attributes:
    ----------
    x : float
        X-coordinate in the Cartesian coordinate system.
    y : float
        Y-coordinate in the Cartesian coordinate system.
    z : float
        Z-coordinate in the Cartesian coordinate system.
    r : float
        Radial distance in the Polar/Cylindrical coordinate system.
    theta : float
        Angle (in radians) in the Polar/Cylindrical coordinate system.

    Methods:
    -------
    cartesian():
        Returns the point in Cartesian coordinates (x, y, z).

    polar():
        Returns the point in Polar coordinates (r, theta).

    cylindrical():
        Returns the point in Cylindrical coordinates (r, theta, z).
    """

    def __init__(self, x: float, y: float, z: float):
        """
        Initializes the point with Cartesian coordinates and calculates
        the radial distance (r) and angular coordinate (theta) for Polar/Cylindrical coordinates.

        Parameters:
        ----------
        x : float
            The X-coordinate in Cartesian coordinates.
        y : float
            The Y-coordinate in Cartesian coordinates.
        z : float
            The Z-coordinate in Cartesian coordinates.
        """
        self.x = x
        self.y = y
        self.z = z
        self.r = math.sqrt(x**2 + y**2)
        self.theta = math.atan2(
            y, x
        )  # atan2(y, x) gives the correct quadrant for theta
        self.r, self.theta = self.polar()

    def cartesian(self):
        """
        Returns the Cartesian coordinates (x, y, z) of the point.

        Returns:
        -------
        tuple:
            A tuple containing (x, y, z) representing Cartesian coordinates.
        """
        return (self.x, self.y, self.z)

    def polar(self):
        """
        Returns the Polar coordinates (r, theta) of the point.

        Returns:
        -------
        tuple:
            A tuple containing (r, theta)
        """
        return (self.r, self.theta)

    def cylindrical(self):
        """
        Returns the Cylindrical coordinates (r, theta, z) of the point.

        Returns:
        -------
        tuple:
            A tuple containing (r, theta, z)
        """
        return (self.r, self.theta, self.z)
