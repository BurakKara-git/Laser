import time


def sleep(duration, get_time=time.time):
    """
    High-precision busy-wait sleep for very short durations.

    Args:
        duration (float): Time to sleep in seconds.
        get_time (function, optional): Time function (default: time.time).

    Notes:
        - Uses 100% CPU while running.
        - Behavior may vary depending on system performance.
        - Not suitable for long durations; use time.sleep() instead.
    """
    current_time = get_time()
    end = current_time + duration
    while current_time < end:
        current_time = get_time()
