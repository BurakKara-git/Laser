from tkinter import Entry, Label, Tk, Button
from tkinter.ttk import Progressbar, Combobox
from zaber_motion import Units
from zaber_motion.ascii import Axis
import constants

#Entry With PlaceHolder Class
#https://stackoverflow.com/questions/27820178/how-to-add-placeholder-to-an-entry-in-tkinter
class EntryWithPlaceholder(Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", axis= "PLACEHOLDER" , row=0, col=0, color='grey'):
        super().__init__(master)
        
        initial_text = Label(master, text= axis, font=("Arial Bold", 20))
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

class Device:
    def __init__(
            self, 
            axisx: Axis,
            axisy: Axis, 
            axisz: Axis, 
            axisrot: Axis
    ):
        self.axisx = axisx
        self.axisy = axisy
        self.axisz = axisz
        self.axisrot = axisrot
        self.axes = [self.axisx, self.axisy, self.axisz, self.axisrot]
    
    def get_current_positions(self):
        x_pos = self.axisx.get_position(Units.LENGTH_MILLIMETRES)
        y_pos = self.axisy.get_position(Units.LENGTH_MILLIMETRES)
        z_pos = self.axisz.get_position(Units.LENGTH_MILLIMETRES)
        rot_pos = self.axisrot.get_position(Units.NATIVE)
        return [x_pos, y_pos, z_pos, rot_pos]
    
    def extract_axes(self):
        self.axisz.move_absolute(constants.Z_MAX, Units.LENGTH_MILLIMETRES)
        self.axisy.move_absolute(constants.Y_MAX, Units.LENGTH_MILLIMETRES) 
        self.axisx.move_absolute(constants.X_MAX, Units.LENGTH_MILLIMETRES)
    
    def set_axes(self, x_pos, y_pos, z_pos, rot_pos):
        self.axisx.move_absolute(x_pos, Units.LENGTH_MILLIMETRES)
        self.axisy.move_absolute(y_pos, Units.LENGTH_MILLIMETRES)
        self.axisz.move_absolute(z_pos, Units.LENGTH_MILLIMETRES)
        self.axisrot.move_absolute(rot_pos,Units.NATIVE)

    def stop_axes(self):
        self.axisx.stop()
        self.axisy.stop()
        self.axisz.stop()
        self.axisrot.stop()

class WindowController:
    def __init__(self,
                 device: Device,                 
                 window: Tk
    ):
        self.window = window
        window.title("Stage Controller")
        window.geometry('1280x720')

        self.lbl = Label(window, text="Stage Controller Is Ready", font=("Arial Bold", 20), fg= "green")
        self.lbl.grid(column=0, row=0)

        self.set_btn = Button(window, text="Set", command = lambda: self.setter(device))
        self.set_btn.grid(column=1, row=0)

        self.exit_btn = Button(self.window, text="EXIT", command = lambda: self.exit_button(device))  
        self.exit_btn.grid(column = 3, row = 0)

        self.set_initial_x = EntryWithPlaceholder(self.window, constants.INITIAL_X, "X", 1, 0)
        self.set_initial_y = EntryWithPlaceholder(self.window, constants.INITIAL_Y, "Y", 2, 0)
        self.set_initial_z = EntryWithPlaceholder(self.window, constants.INITIAL_Z, "Z", 3, 0)
        self.set_initial_rot = EntryWithPlaceholder(self.window, constants.INITIAL_ROT, "Rotation", 4, 0)
        self.set_y_increment = EntryWithPlaceholder(self.window, constants.INITIAL_INCREMENT, "Y increment", 5, 0)
        self.set_dia = EntryWithPlaceholder(self.window, constants.INITIAL_DIAMETER, "Diameter", 6, 0)
        self.set_x_length = EntryWithPlaceholder(self.window, constants.X_MAX, "X Length", 7, 0)
        self.set_initial_vel = EntryWithPlaceholder(self.window, constants.INITIAL_VELOCITY, "Initial Velocity", 8, 0)

        self.set_degree = Combobox(self.window)
        self.set_degree['values']= constants.DEGREES
        self.set_degree.current(0)
        self.set_degree.grid(column=1, row=9)

        self.set_degree_text = Label(self.window, text="Degree", font=("Arial Bold", 20))
        self.set_degree_text.grid(column=0, row=9)

        self.set_list = [self.set_initial_x, self.set_initial_y, self.set_initial_z, 
                    self.set_initial_rot, self.set_y_increment, self.set_dia, 
                    self.set_x_length, self.set_initial_vel, self.set_degree]

        #Initialize Progress Bar
        self.bar = Progressbar(self.window, length=constants.PROGRESS_BAR_LENGTH,
                           style='black.Horizontal.TProgressbar')
        self.bar['value'] = 0
        self.bar.grid(column=0, row=11)

        self.progress_text = Label(self.window, text= "", font=("Arial Bold", 10), fg="green")
        self.progress_text.grid(column=1, row=11)

    def destroy(self):
        self.window.destroy()

    def exit_button(self,
                    device: Device
        ):
        device.extract_axes()
        self.window.destroy()

    def get_values(self):
        """
        0: X (float)
        1: Y (float)
        2: Z (float)
        3: Rotation (float)
        4: Increment (float)
        5: Diameter (float)
        6: X Length (float)
        7: Initial Velocity (float)
        8: Degree (float)
        9: Energy (float)
        """
        values = []
        for i in range (len(self.set_list)):
            values.append(float(self.set_list[i].get()))
        deg = values[8]
        energy = constants.ENERGIES[deg]
        values.append(energy)
        
        return values

    def config_progress_text(self,value, total):
        self.progress_text.config(text = "Task: {}/{}".format(value,total), fg = "green")

    def print_msg(self,MSG,color):
        self.lbl.configure(text= MSG, fg=color)
    
    def position_msg(self, values):
        #Destroy the previous Messages at column 2
        for widget in self.window.grid_slaves(column=2):
            if (widget in  self.window.grid_slaves(row=0)):
                pass
            else:
                widget.destroy()
        
        #Destroy the previous Messages at column 3
        for widget in self.window.grid_slaves(column=3):
            if (widget in  self.window.grid_slaves(row=0)):
                pass
            else:
                widget.destroy()

        #Print Set Messages
        for i in range (len(values)):
            text = Label(self.window, font=("Arial Bold", 20), fg="green")
            text.configure(text = values[i])
            text.grid(column = 2, row = i+1)
        
        text_energy = Label(self.window, text= "({} mJ)".format(values[9]), font=("Arial Bold", 20), fg="green")
        text_energy.grid(column = 3, row=9)


    def setter(self,
            device: Device
        ):
        
        #Stop Axes
        device.stop_axes()

        #Get Initial Position Values
        values = self.get_values()
        
        #Configure Messages
        self.position_msg(values)

        #Move Axes
        initial_x = values[0]
        initial_y = values[1] 
        initial_z = values[2] 
        initial_rot = values[3]
        device.set_axes(initial_x, initial_y, initial_z, initial_rot)

        #Print Msg
        self.print_msg("INITIAL VALUES ARE SET", "green")

class Device:
    def __init__(
            self, 
            axisx: Axis,
            axisy: Axis, 
            axisz: Axis, 
            axisrot: Axis
    ):
        self.axisx = axisx
        self.axisy = axisy
        self.axisz = axisz
        self.axisrot = axisrot
        self.axes = [self.axisx, self.axisy, self.axisz, self.axisrot]
    
    def get_current_positions(self):
        """
        0: X(mm - float)
        1: Y(mm - float)
        2: Z(mm - float)
        3: Rotation(Native - float)
        """
        x_pos = self.axisx.get_position(Units.LENGTH_MILLIMETRES)
        y_pos = self.axisy.get_position(Units.LENGTH_MILLIMETRES)
        z_pos = self.axisz.get_position(Units.LENGTH_MILLIMETRES)
        rot_pos = self.axisrot.get_position(Units.NATIVE)
        return [x_pos, y_pos, z_pos, rot_pos]
    
    def extract_axes(self):
        self.axisz.move_absolute(constants.Z_MAX, Units.LENGTH_MILLIMETRES)
        self.axisy.move_absolute(constants.Y_MAX, Units.LENGTH_MILLIMETRES) 
        self.axisx.move_absolute(constants.X_MAX, Units.LENGTH_MILLIMETRES)
    
    def set_axes(self, x_pos, y_pos, z_pos, rot_pos):
        self.axisx.move_absolute(x_pos, Units.LENGTH_MILLIMETRES)
        self.axisy.move_absolute(y_pos, Units.LENGTH_MILLIMETRES)
        self.axisz.move_absolute(z_pos, Units.LENGTH_MILLIMETRES)
        self.axisrot.move_absolute(rot_pos,Units.NATIVE)

    def stop_axes(self):
        self.axisx.stop()
        self.axisy.stop()
        self.axisz.stop()
        self.axisrot.stop()
