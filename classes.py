from tkinter import Entry, Label

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
