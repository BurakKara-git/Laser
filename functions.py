import time, threading, os, datetime, constants, csv, cv2, classes
from tkinter import *
from zaber_motion import Units, MotionLibException
from zaber_motion.ascii import WarningFlags, Connection
import time, threading, constants, classes, functions 

#Logger
def logger(log_tail, n,energy,x_position,x_velocity,y_position,y_velocity, avg_x_velocity,
           initial_x, initial_y, initial_z, initial_rot):
    log = [n,energy,x_position,x_velocity,y_position,y_velocity, avg_x_velocity,
           initial_x, initial_y, initial_z, initial_rot]
    log_tail.append(log)
    return log_tail

#Write the File
def writer(log_head, log_tail):
    current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'{current_datetime}.csv'
    
    date_folder = datetime.datetime.now().strftime('%d-%m-%Y')
    folder = os.path.join('Data', date_folder)
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Define the full file path
    file_path = os.path.join(folder, filename)
    
    with open(file_path, 'w', newline='\n') as f:        
        write = csv.writer(f)
        write.writerow(log_head)
        write.writerows(log_tail)

#Switch for Threads
def thread_switch(main_function, start_event, args, initial_functions, final_functions):
    for initial_function in initial_functions:
        initial_function()

    if start_event.is_set():
        start_event.clear()
        new_thread = threading.Thread(target = main_function, args = args)
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

#Change image to binary matrix
def img_2_mat(img_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    ret,th = cv2.threshold(img,127,255,cv2.THRESH_BINARY)
    return th

#Run the task        
def runner(window: classes.WindowController, 
           device: classes.Device,
           button,
           lock,
           stop_event, 
           resume_event
    ):
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

    #Calculate Total Task
    total_task = int((dia)/y_increment)
    if total_task > constants.MAX_X_VEL:
        print("ERROR - CANNOT DO TASKS WITH VELOCITIES:")
        while total_task > constants.MAX_X_VEL:
            max_velocity = initial_vel*(total_task)
            total_task -= 1            
            print(max_velocity, end = ", ")
    if total_task %2 == 0:
        max_velocity = initial_vel*(total_task)
        print(max_velocity)
        total_task -= 1

    #Calculate Max Velocity
    max_velocity = initial_vel*total_task
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
            window.bar['value'] = (count/total_task)*100
            window.config_progress_text(count,total_task)

            #Set Position and Velocities
            x_velocity = max_velocity - initial_vel*(count-passed) #Fast to Slow
            #x_velocity = initial_vel*(count-passed) #Slow to Fast
            x_position = x_length*(-1)**(count+1+passed)
            y_position = y_increment
            y_velocity = 0
            avg_x_velocity = "EMPTY"
            
            #Check Ranges
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
            
            #Start Movement
            if count != int(total_task/2)+1:
                    start = time.time()

                    try:
                        device.axisx.move_relative(position=x_position,
                                        unit = Units.LENGTH_MILLIMETRES,
                                        velocity=x_velocity,
                                        velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND)
                    
                        end = time.time()
                        avg_x_velocity = x_length/(end-start)
                    except MotionLibException as err:
                        print(err)
                        avg_x_velocity = "ERROR"                

            #Pass The Middle Movement
            else:
                    avg_x_velocity = "PASSED"
                    passed += 1

            try:
                device.axisy.move_relative(position=y_position, unit = Units.LENGTH_MILLIMETRES, 
                    velocity=y_velocity, velocity_unit = Units.VELOCITY_MILLIMETRES_PER_SECOND)
            except MotionLibException as err:
                print(err)
                avg_x_velocity = "ERROR"
            
            #Log the Task
            log_tail = functions.logger(log_tail, count, energy, x_position, x_velocity, y_position, y_velocity, avg_x_velocity,
                                        initial_x, initial_y, initial_z, initial_rot)
            print("Task: {}/{}, {}".format(count, total_task, avg_x_velocity))
    
    writer(constants.log_head, log_tail)
    lock.release()
    return

#Check Device Health
def check_device(device: classes.Device,
                 window: classes.WindowController
    ):
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

#Find Z-Axis Focus
def z_test(window: classes.WindowController,
           device: classes.Device,
           button,
           lock,
           stop_event, 
           resume_event
    ):
    initial_z = window.get_values()[2]
    lock.acquire()

    device.axisz.move_absolute(position=initial_z, 
                        unit = Units.LENGTH_MILLIMETRES)

    total_step = int((1 + initial_z - constants.Z_MIN)/constants.Z_TEST_STEP)

    if total_step <= 0:
        window.print_msg("SET HIGHER Z VALUE")
        return

    count = 0
    while not stop_event.is_set():
        while not resume_event.is_set():
            time.sleep(1)
        count += 1
        window.bar['value'] = ((count)/(total_step)*100)
        window.config_progress_text(count,total_step)
        window.set_initial_z.delete('0', 'end')
        window.set_initial_z.insert(0, str(device.axisz.get_position(unit=Units.LENGTH_MILLIMETRES)))
        new_pos = initial_z - count*constants.Z_TEST_STEP
        if new_pos <= constants.Z_MIN:
            device.axisz.move_absolute(position= constants.Z_MIN, 
                                unit = Units.LENGTH_MILLIMETRES)
            button.invoke()
            window.print_msg("REACHED MINIMUM Z AXIS", "red")
            lock.release()
            return
        else:
            device.axisz.move_absolute(position= new_pos, 
                                unit = Units.LENGTH_MILLIMETRES)
    final_z = device.axisz.get_position(unit=Units.LENGTH_MILLIMETRES)
    window.set_initial_z.delete('0', 'end')
    window.set_initial_z.insert(0, str(final_z))
    window.position_msg(window.get_values()),
    lock.release()

#Print Matrix
def mat_print(device: classes.Device,
              window: classes.WindowController,
              button,
              mat, 
              lock,
              stop_event, 
              resume_event
    ):
    threshold = 255
    initial_values = window.get_values()
    initial_z = initial_values[2]
    rows = len(mat)
    cols = len(mat[0])
    print("Matrix Dimension: ", rows, cols)

    y_step = constants.Y_MAX/rows
    x_step = constants.X_MAX/cols
    window.config_progress_text(0,rows*(cols-1))

    lock.acquire()

    #unfocus
    device.axisz.move_absolute(position=constants.Z_MAX,
                         unit=Units.LENGTH_MILLIMETRES)
    count = 0
    window.bar['value'] = 0
    for row in range(rows):
        x_pos = y_step*row
        #move to x position
        device.axisx.move_absolute(position=x_pos,
                         unit=Units.LENGTH_MILLIMETRES)
        for col in range(cols-1):
            window.bar['value'] = ((count+1)/(rows*(cols-1)))*100
            window.config_progress_text(count+1,rows*(cols-1))
            count += 1

            while not resume_event.is_set():         
                time.sleep(1)
            
            #Return if Stop Button is Pressed
            if stop_event.is_set():
                device.axisz.move_absolute(position=constants.Z_MAX,
                                unit=Units.LENGTH_MILLIMETRES)
                lock.release()
                return               

            y_pos = x_step*col
            #move to y position
            device.axisy.move_absolute(position=y_pos,
                         unit=Units.LENGTH_MILLIMETRES)
            if mat[row][col] == threshold:
                #focus
                device.axisz.move_absolute(position=initial_z,
                         unit=Units.LENGTH_MILLIMETRES)
                if mat[row][col+1] == threshold:
                    next_y_pos = x_step*(col+1)
                    #move to next y position
                    device.axisy.move_absolute(position=next_y_pos,
                         unit=Units.LENGTH_MILLIMETRES)
            
            else:
                #unfocus
                device.axisz.move_absolute(position=constants.Z_MAX,
                         unit=Units.LENGTH_MILLIMETRES)
        #unfocus
        device.axisz.move_absolute(position=constants.Z_MAX,
                         unit=Units.LENGTH_MILLIMETRES)
    lock.release()
    button.invoke()
    return

#Main Program
def stage_controller(device_list):
    print("Found {} devices".format(len(device_list)))
    devicex = device_list[0]
    devicey = device_list[1]
    devicez = device_list[2]
    devicerot = device_list[3]
    axisx = devicex.get_axis(1)
    axisy = devicey.get_axis(1)
    axisz = devicez.get_axis(1)
    axisrot = devicerot.get_axis(1)
    device = classes.Device(axisx, axisy, axisz, axisrot)

    #Initialize Thread Events
    start_event = threading.Event()
    start_event.set()

    pause_event = threading.Event()

    lock = threading.Lock()

    #Configure Main Window
    window = Tk()
    window_controller = classes.WindowController(device, window)
    
    #Check Device Health
    check_device_thread = threading.Thread(target = functions.check_device(device,window_controller))
    check_device_thread.daemon = True
    check_device_thread.start()        

    #Z-Test Button
    z_test_initial_functions = [lambda: extract_btn.config(state=DISABLED),
                                lambda: window_controller.set_btn.config(state=DISABLED),
                                lambda: run_btn.config(state=DISABLED),
                                lambda: mat_print_btn.config(state=DISABLED),
                                lambda: pause_event.set(),
                                lambda: window_controller.print_msg("STARTED Z TEST", "green"),
                                lambda: z_test_btn.config(text="Stop Z-Test")]
    
    z_test_final_functions = [lambda: extract_btn.config(state=NORMAL),
                                lambda: window_controller.set_btn.config(state=NORMAL),
                                lambda: run_btn.config(state=NORMAL),
                                lambda: mat_print_btn.config(state=NORMAL),
                                lambda: window_controller.print_msg("FINISHED Z TEST", "green"),
                                lambda: z_test_btn.config(text="Start Z-Test")]
    
    z_test_command = lambda: functions.thread_switch(functions.z_test, 
                                                    start_event,
                                                    (window_controller, device, z_test_btn, lock, start_event, pause_event),
                                                    z_test_initial_functions,
                                                    z_test_final_functions)
    
    z_test_btn = Button(window, text="Start Z-Test", command = z_test_command)
    
    z_test_btn.grid(column=4, row=3)            
    
    #Run Button
    runner_initial_functions = [lambda: extract_btn.config(state=DISABLED),
                                lambda: window_controller.set_btn.config(state=DISABLED),
                                lambda: z_test_btn.config(state=DISABLED),
                                lambda: mat_print_btn.config(state=DISABLED),
                                lambda: pause_event.set(),
                                lambda: window_controller.setter(device),
                                lambda: window_controller.print_msg("RUNNING THE TASK","green"),
                                lambda: window_controller.progress_text.config(fg = "green"),
                                lambda: run_btn.config(text = "STOP")]

    runner_final_functions = [lambda: device.extract_axes(),                                  
                                lambda: extract_btn.config(state=NORMAL),
                                lambda: window_controller.set_btn.config(state=NORMAL),
                                lambda: z_test_btn.config(state=NORMAL),
                                lambda: mat_print_btn.config(state=NORMAL),
                                lambda: pause_event.clear(),
                                lambda: pause_btn.config(text="PAUSE"),
                                lambda: window_controller.print_msg("STOPPED THE TASK", "red"),
                                lambda: window_controller.progress_text.config(fg = "red"),
                                lambda: run_btn.config(text = "RUN")]
    
    runner_command = lambda: functions.thread_switch(functions.runner, 
                                            start_event,
                                            (window_controller, device, run_btn, lock, start_event, pause_event),
                                            runner_initial_functions,
                                            runner_final_functions)

    run_btn = Button(window, text="RUN", command = runner_command)
    run_btn.grid(column=1, row=10)

    #Pause Button
    pause_initial_functions = [lambda: window_controller.print_msg("PAUSED THE TASK", "red"),
                                lambda: pause_btn.config(text= "RESUME")]
    
    pause_final_functions = [lambda: window_controller.print_msg("RESUMED THE TASK", "green"),
                                lambda: pause_btn.config(text= "PAUSE")]
    
    pause_command = lambda: functions.thread_switch(None, pause_event, None, pause_initial_functions, pause_final_functions)
    pause_btn = Button(window, text="PAUSE", command = pause_command) #Requested by Sena
    pause_btn.grid(column=0, row=10)

    #Matrix Print Button
    mat = functions.img_2_mat(constants.IMAGE_PATH)
    mat_print_initial_functions =[lambda: extract_btn.config(state=DISABLED),
                                    lambda: window_controller.set_btn.config(state=DISABLED),
                                    lambda: z_test_btn.config(state=DISABLED),
                                    lambda: run_btn.config(state=DISABLED),
                                    lambda: window_controller.setter(device),
                                    lambda: pause_event.set(),
                                    lambda: window_controller.print_msg("PRINTING MATRIX", "green"),
                                    lambda: mat_print_btn.config(text= "Stop Matrix Print")]
    
    mat_print_final_functions = [lambda: device.extract_axes(),
                                    lambda: extract_btn.config(state=NORMAL),
                                    lambda: window_controller.set_btn.config(state=NORMAL),
                                    lambda: z_test_btn.config(state=NORMAL),
                                    lambda: run_btn.config(state=NORMAL),
                                    lambda: pause_event.clear(),
                                    lambda: pause_btn.config(text="PAUSE"),
                                    lambda: window_controller.print_msg("STOPPED MATRIX", "red"),
                                    lambda: mat_print_btn.config(text = "Start Matrix Print")]
    
    mat_print_command = lambda: functions.thread_switch(functions.mat_print, 
                                                        start_event, 
                                                        (device, window_controller, mat_print_btn, mat, lock, start_event, pause_event),
                                                        mat_print_initial_functions,
                                                        mat_print_final_functions)
    
    mat_print_btn = Button(window, text="Start Matrix Print (IN DEVELOPMENT)", command = mat_print_command)
    mat_print_btn.grid(column = 4, row = 10)
    
    #Extract Button
    extract_btn = Button(window, text="EXTRACT", command = lambda: device.extract_axes())  
    extract_btn.grid(column = 5, row = 10)
    window.mainloop()