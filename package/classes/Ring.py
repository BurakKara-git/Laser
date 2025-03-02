import package.constants as constants
import math

class Ring:
    """
    Represents a ring moving in 3D space with given radial distances and speeds.

    Attributes:
        r1 (float): Inner radius of the ring.
        r2 (float): Outer radius of the ring.
        z1 (float): Z axis of the inner ring.
        z2 (float): Z axis of the outer ring.
        r_speed (float): Radial velocity of the ring.
        linear_speed (float): Linear speed of the ring.

    Methods:
        calculate_theta_velocity(linear_speed: float, r_velocity: float, r: float) -> float:
            Calculates and returns the angular velocity (theta_vel) of the ring.
    """

    def __init__(
        self,
        r1: float,
        r2: float,
        z1: float,
        z2: float,
        r_velocity: float,
        linear_speed: float,
    ):
        """
        Initializes the ring with given radial distances, speeds, and calculates 
        the average angular velocity (w).

        Args:
            r1 (float): Inner radius of the ring.
            r2 (float): Outer radius of the ring.
            z1 (float): Z axis of the inner ring.
            z2 (float): Z axis of the outer ring.
            r_velocity (float): Radial velocity of the ring.
            linear_speed (float): Linear speed of the ring.
        """
        self.r1 = r1
        self.r2 = r2
        self.z1 = z1
        self.z2 = z2
        self.r_speed = r_velocity
        self.linear_speed = linear_speed

        # Calculate the angular velocities for both radii
        self.w1 = self.calculate_theta_velocity(
            linear_speed=linear_speed, r_velocity=r_velocity, r=r1
        )
        self.w2 = self.calculate_theta_velocity(
            linear_speed=linear_speed, r_velocity=r_velocity, r=r2
        )

        # Average angular velocity
        self.w = (self.w1 + self.w2) / 2

    def calculate_theta_velocity(
        self, linear_speed: float, r_velocity: float, r: float
    ) -> float:
        """
        Calculates the angular velocity (theta_vel) based on the ring's linear speed, 
        radial velocity, and radius.

        Args:
            linear_speed (float): Linear speed of the ring.
            r_velocity (float): Radial velocity of the ring.
            r (float): Radius at which the angular velocity is being calculated.

        Returns:
            float: The calculated angular velocity (theta_vel).
        """
        theta_vel = 0

        # If linear speed is less than or equal to radial speed, no angular motion
        if linear_speed <= r_velocity:
            return theta_vel

        # If radius is zero, maximum angular velocity
        if r == 0:
            theta_vel = constants.MAX_ROT_VEL
        else:
            # Calculate angular velocity based on the speed components
            theta_vel = math.sqrt(linear_speed**2 - r_velocity**2) / r

        # Limit angular velocity to a maximum of 50
        if theta_vel > constants.MAX_ROT_VEL:
            theta_vel = constants.MAX_ROT_VEL

        return theta_vel
