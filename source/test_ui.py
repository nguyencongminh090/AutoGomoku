from ui import *


def main():
    model     = Model()
    viewmodel = ViewModel(model)
    ui        = View(viewmodel)
    ui.mainloop()


if __name__ == '__main__':
    main()