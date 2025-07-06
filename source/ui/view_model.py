from typing       import Tuple, Callable
from ui           import Model
from ttkbootstrap import IntVar


class ViewModel:
    def __init__(self, model: Model):
        self.__model    = model
        self.time_entry = IntVar(value=60)

    def bind(self, **args):
        ...