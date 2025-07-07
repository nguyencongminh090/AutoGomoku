from utils        import DataBinding
from .model       import Model

class ViewModel:
    def __init__(self, model: Model):
        self.__model       = model
        self.time_entry    = DataBinding(60)
        self.timeP_entry   = DataBinding(0)
        self.engine_entry  = DataBinding('No Engine')
        self.switch_button = DataBinding(True)