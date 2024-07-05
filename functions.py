import threading, os, datetime, constants, csv

#Convert Degree to Energy
energies = {20:1.500, 25:1.465, 30:1.395, 35: 1.200, 40:0.995, 45:0.715, 50:0.475, 60: 0.105}
def Deg_2_Energy(deg):
    energy = energies[deg]
    return energy

#Logger
log_head = ["N","Energy(mJ)","X_Position(mm-Rel)", "X_Velocity(mm/s)", "Y_Position(mm-Rel)", "Y_Velocity(mm/s)",
            "Avg_X_Velocity(mm/s)", "Initial_X(mm)", "Initial_Y(mm)", "Initial_Z(mm)", "Initial_Rot(native)" ]
log_tail = []
def logger(n,energy,x_position,x_velocity,y_position,y_velocity, avg_x_velocity):
    log = [n,energy,x_position,x_velocity,y_position,y_velocity,
          avg_x_velocity,constants.INITIAL_X,constants.INITIAL_Y,constants.INITIAL_Z,constants.INITIAL_ROT]
    log_tail.append(log)

#Write the File
def writer():
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