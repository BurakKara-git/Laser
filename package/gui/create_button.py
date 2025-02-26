from tkinter import Button

def create_button(window, text, command, row, column):
    """
    Creates a Tkinter Button and places it in a grid layout.

    Args:
        window (Tk or Toplevel): The parent Tkinter window where the button will be placed.
        text (str): The label displayed on the button.
        command (function): The function to be executed when the button is clicked.
        row (int): The row index in the grid layout where the button will be placed.
        column (int): The column index in the grid layout where the button will be placed.

    Returns:
        Button: The created Button widget.

    Example:
        create_button(root, "Click Me", some_function, 1, 0)
    """
    btn = Button(window, text=text, command=command)
    btn.grid(column=column, row=row)  # Position the button in the grid layout
    return btn