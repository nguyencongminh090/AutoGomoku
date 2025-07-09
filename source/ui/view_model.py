from tkinter.filedialog import askopenfilename
from utils              import DataBinding
from .model             import Model

class ViewModel:
    def __init__(self, model: Model):
        self.__model       = model
        self.time_entry    = self.__model.time_match
        self.timeP_entry   = self.__model.time_plus
        self.engine_entry  = self.__model.engine
        self.switch_button = self.__model.mode

    def safe_kill_engine(self):
        self.__model.safe_kill_engine()

    def detect_board(self, master):
        self.__model.detect_board(master)

    def select_engine(self):
        fn = askopenfilename(filetypes=[("Executable Files", "*.exe")], title="Select Engine")
        if fn != '':
            self.engine_entry.set(fn)

    def turn_on(self):
        self.__model.turn_on()

    def turn_off(self):
        self.__model.turn_off()