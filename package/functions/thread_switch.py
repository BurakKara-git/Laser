import threading

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

