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
