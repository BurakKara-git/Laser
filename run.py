#Import Libraries
from tkinter import *
from tkinter.ttk import Progressbar
from tkinter.ttk import Combobox
import time
from time import sleep
import csv
import os
import datetime
import threading
from zaber_motion import Units
from zaber_motion.ascii import Connection
from pynput.keyboard import Key
from pynput import keyboard

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
          avg_x_velocity,initial_x,initial_y,initial_z,initial_rot]
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

# Configure Top Message
def print_msg(MSG,color):
    lbl.configure(text= MSG, fg=color)

def done(MSG,color):
    print_msg(MSG,color)
    extract_btn.config(state=NORMAL)
    set_btn.config(state=NORMAL)
    bar.destroy()
    progress_text.config(fg = color) 
        
def runner(dia,x_length,y_increament,energy,initial_vel,stop):
    print_msg("RUNNING THE TASK","green")
    
    global log_tail
    log_tail = []

    global bar
    global progress_text
    bar = Progressbar(window, length=200, style='black.Horizontal.TProgressbar')
    bar['value'] = 0
    bar.grid(column=0, row=11)
    
    extract_btn.config(state=DISABLED)
    set_btn.config(state=DISABLED)
    
    forN = int((dia+5)/y_increament)
    if forN %2 == 0:
        forN += 1
    max_velocity = initial_vel*(forN)    
    passed = 0

    progress_text = Label(window, text= "0/{}".format(forN), font=("Arial Bold", 10), fg="green")
    progress_text.grid(column=1, row=11)

    for n in range(1,forN+1):

        if start_event.is_set():
            break

        else:
            bar['value'] = (n/forN)*100
            progress_text.config(text = str(n) + "/{}".format(forN))

            #Set Position and Velocities
            x_velocity = max_velocity - initial_vel*(n-passed)
            x_position = x_length*(-1)**(n+1+passed)
            y_position = y_increament
            y_velocity = 0        

            if n != int(forN/2)+1:
                start = time.time()
                """
                axisx.move_relative(position=x_position, unit = Units.LENGTH_MILLIMETRES, 
                        velocity=x_velocity, velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND
                        )
                end = time.time()
                avg_x_velocity = x_length/(end-start)
                """
                avg_x_velocity = "DONE"

            #Pass The Middle Movement
            else:
                avg_x_velocity = "PASSED"
                passed += 1        
            """
            axisy.move_relative(position=y_position, unit = Units.LENGTH_MILLIMETRES, 
                        velocity=y_velocity, velocity_unit = Units.VELOCITY_MILLIMETRES_PER_SECOND
                        )
            """
            logger(n,energy,x_position,x_velocity,y_position,y_velocity, avg_x_velocity)
            sleep(0.02)
            print(avg_x_velocity)

    #Write the Data
    if not start_event.is_set():
        MSG = "COMPLETED THE TASK"
        done(MSG, "green")
        writer()

def extractor():
    """
    axisx.move_absolute(40, Units.LENGTH_MILLIMETRES)
    axisy.move_absolute(60, Units.LENGTH_MILLIMETRES)
    axisz.move_absolute(24, Units.LENGTH_MILLIMETRES)    
    """
    
    print_msg("SAMPLE IS EXTRACTED", "green")

def setter():
    deg = set_degree.get()
    energy = Deg_2_Energy(int(deg))

    set_list = [set_initial_x, set_initial_y, set_initial_z, set_initial_rot, set_y_increament,
                set_dia, set_x_length, set_initial_vel, set_degree]

    for widget in window.grid_slaves(column=2):
       if (widget in  window.grid_slaves(row=0)):
           pass
       else:
           widget.destroy()
    
    for widget in window.grid_slaves(column=3):
       if (widget in  window.grid_slaves(row=0)):
           pass
       else:
           widget.destroy()

    for i in range (len(set_list)):
        text = Label(window, font=("Arial Bold", 20), fg="green")
        text.configure(text = set_list[i].get())
        text.grid(column = 2, row = i+1)
    
    text_energy = Label(window, text= "({} mJ)".format(energy), font=("Arial Bold", 20), fg="green")
    text_energy.grid(column = 3, row=9)

    global initial_x, initial_y, initial_z, initial_rot
    initial_x = set_initial_x.get()
    initial_y = set_initial_y.get() 
    initial_z = set_initial_z.get() 
    initial_rot = set_initial_rot.get() 
    
    """
    #Initial Positions
    axisx.move_absolute(float(initial_x), Units.LENGTH_MILLIMETRES)
    axisy.move_absolute(float(initial_y), Units.LENGTH_MILLIMETRES)
    axisz.move_absolute(float(initial_z), Units.LENGTH_MILLIMETRES)
    axisrot.move_absolute(float(initial_rot),Units.NATIVE)    
    """

    print_msg("INITIAL VALUES ARE SET", "green")

class EntryWithPlaceholder(Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", axis= "PLACEHOLDER" , row=0, col=0, color='grey'):
        super().__init__(master)
        
        initial_text = Label(window, text= axis, font=("Arial Bold", 20))
        initial_text.grid(column=col, row=row)
        self.grid(column=col+1, row=row)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()

def switch_runner():
    setter()
    dia = float(set_dia.get())
    x_length = float(set_x_length.get())
    y_increament = float(set_y_increament .get())
    deg = float(set_degree.get())
    energy = float(Deg_2_Energy(int(deg)))
    initial_vel = float(set_initial_vel.get())

    if start_event.is_set():
        thread_runner = threading.Thread(target = runner, args = (dia,x_length,y_increament,energy,initial_vel, start_event))
        thread_runner.daemon = True
        run_btn.config(text= "STOP")
        start_event.clear()
        thread_runner.start()
    else:
        run_btn.config(text = "RUN")
        start_event.set()
        MSG = "STOPPED THE TASK"
        done(MSG, "red")
        thread_runner = None

if __name__ == "__main__":
    #with Connection.open_serial_port("COM3") as connection:
        delete_list = []
        window = Tk()
        window.title("Stage Controller")
        window.geometry('1280x720')
        

        lbl = Label(window, text="Set Parameters", font=("Arial Bold", 20))
        lbl.grid(column=0, row=0)

        set_btn = Button(window, text="Set", command=setter)
        set_btn.grid(column=1, row=0)

        exit_btn = Button(window, text="EXIT", command= lambda: window.destroy())  
        exit_btn.grid(column = 3, row = 0)

        set_initial_x = EntryWithPlaceholder(window, 0.0, "X", 1, 0)
        set_initial_y = EntryWithPlaceholder(window, 3.0, "Y", 2, 0)
        set_initial_z = EntryWithPlaceholder(window, 20.4, "Z", 3, 0)
        set_initial_rot = EntryWithPlaceholder(window, 29333, "Rotation", 4, 0)
        set_y_increament = EntryWithPlaceholder(window, 0.05, "Y Increament", 5, 0)
        set_dia = EntryWithPlaceholder(window, 15, "Diameter", 6, 0)
        set_x_length = EntryWithPlaceholder(window, 40, "X Length", 7, 0)
        set_initial_vel = EntryWithPlaceholder(window, 1, "Initial Velocity", 8, 0)
        
        set_degree = Combobox(window)
        set_degree['values']= (20, 25, 30, 35, 40, 45, 50, 55, 60)
        set_degree.current(0)
        set_degree.grid(column=1, row=9)

        set_degree_text = Label(window, text="Degree", font=("Arial Bold", 20))
        set_degree_text.grid(column=0, row=9)
        
        """
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
        """

        start_event = threading.Event()
        start_event.set()
        
        run_btn = Button(window, text="RUN", command = lambda: switch_runner())
        run_btn.grid(column=0, row=10)
        
        extract_btn = Button(window, text="EXTRACT", command=extractor)  
        extract_btn.grid(column = 0, row = 12)

        
        
        window.mainloop()