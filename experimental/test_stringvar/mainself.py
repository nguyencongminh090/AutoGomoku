from ttkbootstrap import *
import ttkbootstrap


class Model:
    def __init__(self):
        self.num_data: int = 0
        self.str_data: str = '<hello world>'

    def inc(self):
        self.num_data += 1

class ViewModel:
    def __init__(self, model: Model):
        self.__model = model

        self.default_int = self.__model.num_data
        self.num_var     = None
        self.str_var     = NotImplemented

    def set_num_var(self, int_var: ttkbootstrap.IntVar):
        self.num_var = int_var
        self.num_var.set(self.default_int)
        self.num_var.trace_add('write', self.__on_handle_num_data)

    def __on_handle_num_data(self, *args):
        if self.num_var:
            try:
                value = self.num_var.get()
                if value:
                    self.__model.num_data = self.num_var.get()
                    print('Data:', self.__model.num_data)
            except ValueError:
                return 0
            finally:
                self.update_view()
    
    def update_view(self):
        self.num_var.set(self.__model.num_data)

    def get_num_var(self):
        print(self.num_var.get(), self.__model.num_data)

    def inc(self):
        self.__model.inc()
        self.update_view()


class UI(ttkbootstrap.Window):
    def __init__(self, model: ViewModel):
        super().__init__()

        self.__view_model = model
        # StringVar
        self.__int_var = IntVar(self)
        self.__int_var.set(self.__view_model.num_var)
        self.__view_model.set_num_var(self.__int_var)
        
        # Label
        self.__label_1 = Label(self, text='', textvariable=self.__int_var)
        self.__label_1.pack(anchor='center', side='top', fill='both', padx=5, pady=5)

        # Entry
        self.__intentry_0 = Entry(self, textvariable=self.__int_var)
        self.__intentry_0.pack(anchor='center', fill='both', side='top', padx=5, pady=5)

        # Button
        self.__button = Button(self, text='GET', command=self.__view_model.get_num_var)
        self.__button.pack(anchor='center', fill='both', side='top', padx=5, pady=5)

        self.__button_1 = Button(self, text='INC', command=self.__view_model.inc)
        self.__button_1.pack(anchor='center', fill='both', side='top', padx=5, pady=5)

# -----------------------------------
def main():
    model     = Model()
    viewmodel = ViewModel(model)
    window    = UI(viewmodel)
    window.mainloop()


if __name__ == '__main__':
    main()