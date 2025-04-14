import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled  import ScrolledText


class View(ttk.Window):
    def __init__(self):
        super().__init__()
        self.geometry()
        self.resizable(False, False)
        self.wm_attributes("-topmost", 1)
        self.protocol("WM_DELETE_WINDOW", self.__safe_exit)

        # Label
        self.__label_1 = ttk.Label(self, text="Time:")
        self.__label_2 = ttk.Label(self, text="Time plus:")
        self.__label_3 = ttk.Label(self, text="Engine:")

        self.__label_1.grid(column=0, row=0, padx=5, pady=5, sticky=W)
        self.__label_2.grid(column=0, row=1, padx=5, pady=5, sticky=W)
        self.__label_3.grid(column=0, row=2, padx=5, pady=5, sticky=W)

        # Entry
        self.__time_entry      = ttk.Entry(self)
        self.__time_plus_entry = ttk.Entry()
        self.__engine_entry    = ttk.Entry()

        self.__time_entry.grid(column=1, row=0, padx=5, pady=5, sticky='we')
        self.__time_plus_entry.grid(column=1, row=1, padx=5, pady=5, sticky='we')
        self.__engine_entry.grid(column=1, row=2, padx=5, pady=5, sticky='we')

        # TextBox
        self.__log_textbox = ScrolledText(self, height=5, autohide=True)
        self.__log_textbox.grid(column=0, columnspan=2, row=3, padx=5, pady=5, sticky='news')

        # Button
        self.__setting_button = ttk.Button(self, text='Setting', bootstyle='success outline')
        self.__setting_button.grid(column=0, columnspan=2, row=4, padx=5, pady=5, sticky='we')

        # Setting TopLevel
        self.__setting_frame = ttk.Toplevel(title='Settings')

    def __safe_exit(self):
        ...