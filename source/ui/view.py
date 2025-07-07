import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled  import ScrolledText
from .view_model            import ViewModel


class View(ttk.Window):
    def __init__(self, view_model: ViewModel):
        super().__init__()
        self.geometry()
        self.resizable(True, False)
        self.wm_attributes("-topmost", 1)
        self.protocol("WM_DELETE_WINDOW", self.__safe_exit)
        self.title('AutoGomoku v5.0 NguyenMinh')
        self.columnconfigure(1, weight=1)

        # Setting TopLevel
        self.__setting_frame = ttk.Toplevel(title='Settings')        
        self.__setting_frame.wm_attributes("-topmost", 1)
        self.__setting_frame.geometry()
        self.__setting_frame.resizable(0, 0)
        self.__setting_frame.withdraw()

        # Variable
        self.__time_var   = ttk.IntVar(self)
        self.__timeP_var  = ttk.IntVar(self)
        self.__engine_var = ttk.StringVar(self)
        self.__switch_var = ttk.BooleanVar(self.__setting_frame)

        # Register handler
        self.__view_model = view_model
        self.__view_model.time_entry.subscribe(self.__time_var)        
        self.__view_model.timeP_entry.subscribe(self.__timeP_var)
        self.__view_model.engine_entry.subscribe(self.__engine_var)
        self.__view_model.switch_button.subscribe(self.__switch_var)

        # Label
        self.__label_1 = ttk.Label(self, text="Time (s):")
        self.__label_2 = ttk.Label(self, text="Time plus (s):")
        self.__label_3 = ttk.Label(self, text="Engine:")

        self.__label_1.grid(column=0, row=0, padx=5, pady=(5, 2.5), sticky=W)
        self.__label_2.grid(column=0, row=1, padx=5, pady=(2.5, 2.5), sticky=W)
        self.__label_3.grid(column=0, row=2, padx=5, pady=(2.5, 2.5), sticky=W)

        # Entry
        self.__time_entry      = ttk.Entry(self, textvariable=self.__time_var)
        self.__time_plus_entry = ttk.Entry(self, textvariable=self.__timeP_var)
        self.__engine_entry    = ttk.Entry(self, textvariable=self.__engine_var)

        self.__time_entry.grid(column=1, row=0, padx=5, pady=(2.5, 2.5), sticky='we')
        self.__time_plus_entry.grid(column=1, row=1, padx=5, pady=(2.5, 2.5), sticky='we')
        self.__engine_entry.grid(column=1, row=2, padx=5, pady=(2.5, 2.5), sticky='we')

        # TextBox
        self.__log_textbox = ScrolledText(self, height=5, width=30, autohide=True)
        self.__log_textbox.grid(column=0, columnspan=2, row=3, padx=5, pady=(2.5, 2.5), sticky='news')          

        # Button
        self.__setting_button    = ttk.Button(self, text='Setting', bootstyle='success outline')
        self.__set_engine_button = ttk.Button(self.__setting_frame, text='Select Engine')
        self.__detect_board      = ttk.Button(self.__setting_frame, text='Detect Board')

        self.__setting_button.grid(column=0, columnspan=2, row=4, padx=5, pady=(2.5, 5), sticky='we')
        self.__set_engine_button.grid(column=1, row=0, padx=(5, 2.5), pady=5, sticky='we')
        self.__detect_board.grid(column=2, row=0, padx=(2.5, 5), pady=5, sticky='we')

        # CheckButton        
        self.__switch = ttk.Checkbutton(self.__setting_frame, bootstyle='round-toggle', text='Auto', variable=self.__switch_var)
        self.__switch.grid(column=0, row=0, padx=(5, 2.5), pady=5, sticky='we')

        # Configure
        self.__setting_button.configure(command=self.__setting_frame.deiconify)
        self.__detect_board.configure(command=lambda: self.__view_model.detect_board(self))
        self.__set_engine_button.configure(command=self.__view_model.select_engine)

    def __safe_exit(self):
        # Find and terminate engine if exist
        self.destroy()
        self.__view_model.safe_kill_engine()