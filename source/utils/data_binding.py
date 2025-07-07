from ttkbootstrap import Variable
from tkinter      import TclError


class DataBinding:
    def __init__(self, initial_value=None):
        self.__value              = initial_value
        self.__variable: Variable = None

    def subscribe(self, variable: Variable):
        self.__variable = variable
        self.__variable.trace_add('write', self.__on_change)
        if not self.__variable.get():
            self.update()

    def __on_change(self, *_):
        try:
            if self.__variable and (value := self.__variable.get()) != self.__value and value != '':
                self.__value = value
        except (TclError, ValueError):
            return

    def update(self):
        self.__variable.set(self.__value)

    def set(self, value):
        if value != self.__value:
            self.__value = value
            self.update()

    def get(self):
        return self.__value