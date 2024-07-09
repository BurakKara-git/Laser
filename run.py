#Import Libraries
from tkinter import *
from tkinter.ttk import Progressbar, Combobox
from zaber_motion import Units, MotionLibException
from zaber_motion.ascii import Connection, WarningFlags
import time, threading, constants, classes, functions

# Configure Top Message
def print_msg(MSG,color):
    lbl.configure(text= MSG, fg=color)

#Check Device Health
def check_device(axes):
    for axis in axes:            
        warning_flags = axis.warnings.get_flags()
        if WarningFlags.CRITICAL_SYSTEM_ERROR in warning_flags:
            while True:
                print_msg("WARNING: CRITICAL SYSTEM ERROR!", "red")
                time.sleep(0.1)        
        if WarningFlags.HARDWARE_EMERGENCY_STOP in warning_flags:
            while True:
                print_msg("WARNING: HARDWARE EMERGENCY STOP!", "red")
                time.sleep(0.1)
    time.sleep(10)

#Extract the Sample
def extractor():
    axisz.move_absolute(constants.Z_MAX, Units.LENGTH_MILLIMETRES)
    axisy.move_absolute(constants.Y_MAX, Units.LENGTH_MILLIMETRES) 
    axisx.move_absolute(constants.X_MAX, Units.LENGTH_MILLIMETRES) 
    wait_axes([axisx, axisy, axisz, axisrot])
    print_msg("SAMPLE IS EXTRACTED", "green")

#Set Initial Positions
def setter(master):
    stop_axes([axisrot,axisx, axisy, axisz])
    deg = set_degree.get()
    energy = functions.Deg_2_Energy(int(deg))

    set_list = [set_initial_x, set_initial_y, set_initial_z, set_initial_rot, set_y_increment,
                set_dia, set_x_length, set_initial_vel, set_degree]

    #Destroy the previous Messages at column 2
    for widget in master.grid_slaves(column=2):
       if (widget in  master.grid_slaves(row=0)):
           pass
       else:
           widget.destroy()
    
    #Destroy the previous Messages at column 3
    for widget in master.grid_slaves(column=3):
       if (widget in  master.grid_slaves(row=0)):
           pass
       else:
           widget.destroy()

    #Print Set Messages
    for i in range (len(set_list)):
        text = Label(master, font=("Arial Bold", 20), fg="green")
        text.configure(text = set_list[i].get())
        text.grid(column = 2, row = i+1)
    
    text_energy = Label(master, text= "({} mJ)".format(energy), font=("Arial Bold", 20), fg="green")
    text_energy.grid(column = 3, row=9)

    #Get Initial Position Values
    global initial_x, initial_y, initial_z, initial_rot
    initial_x = set_initial_x.get()
    initial_y = set_initial_y.get() 
    initial_z = set_initial_z.get() 
    initial_rot = set_initial_rot.get()
    
    #Initial Positions
    axisx.move_absolute(float(initial_x), Units.LENGTH_MILLIMETRES)
    axisy.move_absolute(float(initial_y), Units.LENGTH_MILLIMETRES)
    axisz.move_absolute(float(initial_z), Units.LENGTH_MILLIMETRES)
    axisrot.move_absolute(float(initial_rot),Units.NATIVE)
    wait_axes([axisx, axisy, axisz, axisrot])
    print_msg("INITIAL VALUES ARE SET", "green")

#Exit Button
def exit_button():
    extractor()
    window.destroy()

#Wait all Axes
def wait_axes(axes):
    for axis in axes:            
        while axis.is_busy():
            time.sleep(0.1)

#Stop all Axes
def stop_axes(axes):
    for axis in axes:
        axis.stop()

#Find Z-Axis Focus
def z_test(stop_event, resume_event):
    initial_z = float(set_initial_z.get())
    lock.acquire()
    axisz.move_absolute(position=initial_z, 
                            unit = Units.LENGTH_MILLIMETRES)
    wait_axes([axisz])

    total_step = int((1 + initial_z - constants.Z_MIN)/constants.Z_TEST_STEP)

    if total_step <= 0:
        print_msg("SET HIGHER Z VALUE")
        return

    count = 0
    while not stop_event.is_set():
        while not pause_event.is_set():
            time.sleep(1)
        count += 1
        bar['value'] = (count)/(total_step)*100
        progress_text.config(text = "Task: {}/{}".format(count,total_step), fg = "green")
        set_initial_z.delete('0', 'end')
        set_initial_z.insert(0, str(axisz.get_position(unit=Units.LENGTH_MILLIMETRES)))
        new_pos = initial_z - count*constants.Z_TEST_STEP
        if new_pos <= constants.Z_MIN:
            axisz.move_absolute(position= constants.Z_MIN, 
                                unit = Units.LENGTH_MILLIMETRES)
            z_test_btn.invoke()
            print_msg("REACHED MINIMUM Z AXIS", "red")
            lock.release()
            return
        else:
            axisz.move_absolute(position= new_pos, 
                                unit = Units.LENGTH_MILLIMETRES)
    
    lock.release()

#Run the task        
def runner(stop_event, resume_event):
    global log_tail
    log_tail = []
    dia = float(set_dia.get())
    x_length = float(set_x_length.get())
    y_increment = float(set_y_increment .get())
    deg = float(set_degree.get())
    energy = float(functions.Deg_2_Energy(int(deg)))
    initial_vel = float(set_initial_vel.get())

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

        #Wait axes to finish task
        wait_axes([axisx, axisy, axisz, axisrot])

        if count == total_task:
            functions.writer(constants.log_head, log_tail)
            lock.release()
            run_btn.invoke()
            return
        
        else:
            count += 1
            bar['value'] = (count/total_task)*100
            progress_text.config(text = "Task: {}/{}".format(count,total_task), fg = "green")

            #Set Position and Velocities
            x_velocity = max_velocity - initial_vel*(count-passed) #Fast to Slow
            #x_velocity = initial_vel*(count-passed) #Slow to Fast
            x_position = x_length*(-1)**(count+1+passed)
            y_position = y_increment
            y_velocity = 0
            avg_x_velocity = "EMPTY"
            
            #Check Ranges
            if axisx.get_position(Units.LENGTH_MILLIMETRES) + x_position > constants.X_MAX:
                functions.writer(constants.log_head, log_tail)
                print_msg("Reached Max X Range", "red")
                lock.release()
                return
            
            if axisx.get_position(Units.LENGTH_MILLIMETRES) + x_position < constants.X_MIN:
                functions.writer(constants.log_head, log_tail)
                print_msg("Reached Min X Range", "red")
                lock.release()
                return
            
            if axisy.get_position(Units.LENGTH_MILLIMETRES) + y_position > constants.Y_MAX:
                functions.writer(constants.log_head, log_tail)
                print_msg("Reached Max Y Range", "red")
                lock.release()
                return
            
            if axisy.get_position(Units.LENGTH_MILLIMETRES) + y_position < constants.Y_MIN:
                functions.writer(constants.log_head, log_tail)
                print_msg("Reached Min Y Range", "red")
                lock.release()
                return
            
            #Start Movement
            if count != int(total_task/2)+1:
                    start = time.time()

                    try:
                        axisx.move_relative(position=x_position,
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
                axisy.move_relative(position=y_position, unit = Units.LENGTH_MILLIMETRES, 
                    velocity=y_velocity, velocity_unit = Units.VELOCITY_MILLIMETRES_PER_SECOND)
            except MotionLibException as err:
                print(err)
            
            #Log the Task
            log_tail = functions.logger(log_tail, count, energy, x_position, x_velocity, y_position, y_velocity, avg_x_velocity)
            print("Task: {}/{}, {}".format(count, total_task, avg_x_velocity))
    
    functions.writer(constants.log_head, log_tail)
    lock.release()
    return

if __name__ == "__main__":
    with Connection.open_serial_port("COM3") as connection: #Connect the Device
        delete_list = []

        #Configure Main Window
        window = Tk()
        window.title("Stage Controller")
        window.geometry('1280x720')

        #Initialize Thread Events
        start_event = threading.Event()
        start_event.set()

        pause_event = threading.Event()

        lock = threading.Lock()     

        #Initialize Texts
        lbl = Label(window, text="Stage Controller Is Ready", font=("Arial Bold", 20), fg= "green")
        lbl.grid(column=0, row=0)

        set_btn = Button(window, text="Set", command= lambda: setter(window))
        set_btn.grid(column=1, row=0)

        exit_btn = Button(window, text="EXIT", command= exit_button)  
        exit_btn.grid(column = 3, row = 0)

        set_initial_x = classes.EntryWithPlaceholder(window, constants.INITIAL_X, "X", 1, 0)
        set_initial_y = classes.EntryWithPlaceholder(window, constants.INITIAL_Y, "Y", 2, 0)
        set_initial_z = classes.EntryWithPlaceholder(window, constants.INITIAL_Z, "Z", 3, 0)
        set_initial_rot = classes.EntryWithPlaceholder(window, constants.INITIAL_ROT, "Rotation", 4, 0)
        set_y_increment = classes.EntryWithPlaceholder(window, constants.INITIAL_INCREMENT, "Y increment", 5, 0)
        set_dia = classes.EntryWithPlaceholder(window, constants.INITIAL_DIAMETER, "Diameter", 6, 0)
        set_x_length = classes.EntryWithPlaceholder(window, constants.X_MAX, "X Length", 7, 0)
        set_initial_vel = classes.EntryWithPlaceholder(window, constants.INITIAL_VELOCITY, "Initial Velocity", 8, 0)

        set_degree = Combobox(window)
        set_degree['values']= constants.DEGREES
        set_degree.current(0)
        set_degree.grid(column=1, row=9)

        set_degree_text = Label(window, text="Degree", font=("Arial Bold", 20))
        set_degree_text.grid(column=0, row=9)

        #Initialize Progress Bar
        bar = Progressbar(window, length=constants.PROGRESS_BAR_LENGTH,
                           style='black.Horizontal.TProgressbar')
        bar['value'] = 0
        bar.grid(column=0, row=11)

        progress_text = Label(window, text= "", font=("Arial Bold", 10), fg="green")
        progress_text.grid(column=1, row=11)
        
        #Establish Connections
        connection.enable_alerts()

        device_list = connection.detect_devices()
        print("Found {} devices".format(len(device_list)))
        
        #Assigning Devices
        devicex = device_list[0]
        devicey = device_list[1]
        devicez = device_list[2]
        devicerot = device_list[3]

        axisx = devicex.get_axis(1)
        axisy = devicey.get_axis(1)
        axisz = devicez.get_axis(1)
        axisrot = devicerot.get_axis(1)  

        #Check Device Health
        check_device_thread = threading.Thread(target = check_device, args = ([axisx, axisy, axisz, axisrot],))
        check_device_thread.daemon = True
        check_device_thread.start()

        #Z-Test Button
        z_test_initial_functions = [lambda: pause_event.set(),
                                    lambda: print_msg("STARTED Z TEST", "green"),
                                    lambda: z_test_btn.config(text="Stop Z-Test")]
        
        z_test_final_functions = [lambda: print_msg("Z Test Result: " + str(axisz.get_position(unit=Units.LENGTH_MILLIMETRES)), "green"),
                                  lambda: z_test_btn.config(text="Start Z-Test")]
        
        z_test_command = lambda: functions.thread_switch(z_test, 
                                               start_event,
                                               (start_event, pause_event),
                                               z_test_initial_functions,
                                               z_test_final_functions)
        
        z_test_btn = Button(window, text="Start Z-Test", command = z_test_command)
        
        z_test_btn.grid(column=4, row=3)            
        
        #Run Button
        runner_initial_functions = [lambda: extract_btn.config(state=DISABLED),
                                    lambda: set_btn.config(state=DISABLED),
                                    lambda: z_test_btn.config(state=DISABLED),
                                    lambda: pause_event.set(),
                                    lambda: setter(window),
                                    lambda: print_msg("RUNNING THE TASK","green"),
                                    lambda: progress_text.config(fg = "green"),
                                    lambda: run_btn.config(text = "STOP")]

        runner_final_functions = [lambda: extractor(),                                  
                                  lambda: extract_btn.config(state=NORMAL),
                                  lambda: set_btn.config(state=NORMAL),
                                  lambda: z_test_btn.config(state=NORMAL),
                                  lambda: pause_event.clear(),
                                  lambda: pause_btn.config(text="PAUSE"),
                                  lambda: print_msg("STOPPED THE TASK", "red"),
                                  lambda: progress_text.config(fg = "red"),
                                  lambda: run_btn.config(text = "RUN")]
        
        runner_command = lambda: functions.thread_switch(runner, 
                                               start_event,
                                               (start_event, pause_event),
                                               runner_initial_functions,
                                               runner_final_functions)

        run_btn = Button(window, text="RUN", command = runner_command)
        run_btn.grid(column=1, row=10)

        #Pause Button
        pause_initial_functions = [lambda: print_msg("PAUSED THE TASK", "red"),
                                   lambda: pause_btn.config(text= "RESUME")]
        
        pause_final_functions = [lambda: print_msg("RESUMED THE TASK", "green"),
                                 lambda: pause_btn.config(text= "PAUSE")]
        
        pause_command = lambda: functions.thread_switch(None, pause_event, None, pause_initial_functions, pause_final_functions)
        pause_btn = Button(window, text="PAUSE", command = pause_command) #Requested by Sena
        pause_btn.grid(column=0, row=10)
        
        #Extract Button
        extract_btn = Button(window, text="EXTRACT", command = lambda: extractor())  
        extract_btn.grid(column = 5, row = 10)
        window.mainloop()