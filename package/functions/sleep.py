import time
from typing import Callable


def sleep(duration: float, get_time: Callable[[], float] = time.time):
    """
    High-precision busy-wait sleep for very short durations.

    Args:
        duration (float): Time to sleep in seconds.
        get_time (function, optional): Time function (default: time.time).

    Notes:
        - Uses 100% CPU while running.
        - Behavior may vary depending on system performance.
        - Not suitable for long durations; use `time.sleep()` instead.
        - To determine the best function for your system, run the following command in the terminal:
        
          ```bash
          python -m timeit -s "from time import YOUR_FUNCTION as time" -n 1000000 "time()"
          ```
    """
    current_time = get_time()
    end = current_time + duration
    while current_time < end:
        current_time = get_time()
