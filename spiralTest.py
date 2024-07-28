import math

def generate_spiral_gcode(radius, height, turns, start_x, start_y, start_z, velocity):
    gcode = []
    total_steps = int(100 * turns)  
    y_step = height / total_steps  
    theta_step = (2 * math.pi * turns) / total_steps  

    for step in range(total_steps):
        theta = step * theta_step  
        y = start_y + step * y_step  
        x = start_x + radius * math.cos(theta) 
        z = start_z  
        gcode.append(f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f} F{velocity}") 

    return "\n".join(gcode)

print(generate_spiral_gcode(3, 3, 3, 21.08, 13.14, 20.4, 1500))
# GCode(gcode, device, window_controller, button, lock, stop_event, resume_event)
