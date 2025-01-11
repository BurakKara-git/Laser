from tkinter import Entry, Label

class EntryWithPlaceholder(Entry):
    """
    Entry With PlaceHolder Class
    https://stackoverflow.com/questions/27820178/how-to-add-placeholder-to-an-entry-in-tkinter
    """

    def __init__(
        self,
        master=None,
        placeholder="PLACEHOLDER",
        axis="PLACEHOLDER",
        row=0,
        col=0,
        color="grey",
    ):
        """Initializes the widget with a placeholder and axis label.

        Args:
            master (Widget): The parent widget.
            placeholder (str): The placeholder text.
            axis (str): The axis label text.
            row (int): The row position in the grid. Defaults to 0.
            col (int): The column position in the grid. Defaults to 0.
            color (str): The placeholder text color. Defaults to 'grey'.

        Returns:
            None
        """
        super().__init__(master)

        initial_text = Label(master, text=axis, font=("Arial Bold", 20))
        initial_text.grid(column=col, row=row)
        self.grid(column=col + 1, row=row)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["fg"]

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        """Inserts placeholder text and sets its color.

        Inserts the placeholder text at the start and sets its color.

        Returns:
            None
        """
        self.insert(0, self.placeholder)
        self["fg"] = self.placeholder_color

    def foc_in(self, *args):
        """Removes placeholder text on focus.

        Deletes the placeholder text and resets the text color when the widget gains focus.

        Args:
            *args: Variable length argument list.

        Returns:
            None
        """
        if self["fg"] == self.placeholder_color:
            self.delete("0", "end")
            self["fg"] = self.default_fg_color

    def foc_out(self, *args):
        """Adds placeholder text on losing focus.

        Inserts the placeholder text if the widget is empty when it loses focus.

        Args:
            *args: Variable length argument list.

        Returns:
            None
        """

        if not self.get():
            self.put_placeholder()
