from tkinter.filedialog import askopenfilename
from utils              import DataBinding
from .model             import Model

class ViewModel:
    def __init__(self, model: Model):
        self.__model       = model
        self.time_entry    = DataBinding(60,          lambda x: setattr(self.__model, 'time_match', x))
        self.timeP_entry   = DataBinding(0,           lambda x: setattr(self.__model, 'time_plus', x))
        self.engine_entry  = DataBinding('No Engine', lambda x: setattr(self.__model, 'engine', x))
        self.switch_button = DataBinding(True,        lambda x: setattr(self.__model, 'mode', x))

    def safe_kill_engine(self):
        self.__model.terminate_engine()

    def detect_board(self, master):
        self.__model.detect_board(master)

    def select_engine(self):
        fn = askopenfilename(filetypes=[("Executable Files", "*.exe")], title="Select Engine")
        if fn != '':
            self.engine_entry.set(fn)