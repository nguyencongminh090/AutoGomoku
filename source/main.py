"""
This script initializes and runs the main graphical user interface (GUI) of the
AutoGomoku application. It follows the Model-View-ViewModel (MVVM) design
pattern to structure the application's components:

-   **Model**    : Represents the application's data and business logic.
-   **ViewModel**: Acts as an intermediary, handling the presentation logic
    and managing the state of the View.
-   **View**     : The user interface, which displays data from the ViewModel and
    sends user commands back to it.
"""
from ui import View, ViewModel, Model


def main():
    """
    Initializes the MVVM components and starts the application's main loop.
    """
    model      = Model()
    view_model = ViewModel(model)
    ui         = View(view_model)
    ui.mainloop()


if __name__ == "__main__":
    main()
