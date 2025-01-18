from tkinter import Button

def create_button(window, text, command, row, column):
        btn = Button(window, text=text, command=command)
        btn.grid(column=column, row=row)
        return btn