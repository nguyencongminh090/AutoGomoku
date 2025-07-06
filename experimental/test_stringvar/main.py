import ttkbootstrap as tkb
from tkinter import StringVar

# --- Model ---
class CounterModel:
    """
    The Model holds the application's data and core business logic.
    It's completely independent of the UI.
    """
    def __init__(self, initial_value=0):
        self._count = initial_value
        self._subscribers = [] # Used to notify the ViewModel of changes

    def increment(self):
        """Increments the counter."""
        self._count += 1
        self._notify_subscribers()

    def decrement(self):
        """Decrements the counter."""
        self._count -= 1
        self._notify_subscribers()

    def reset(self):
        """Resets the counter to its initial value."""
        self._count = 0
        self._notify_subscribers()

    def get_count(self):
        """Returns the current counter value."""
        return self._count

    def subscribe(self, callback):
        """Allows a callback (typically from the ViewModel) to listen for changes."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback):
        """Removes a subscribed callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify_subscribers(self):
        """Notifies all subscribed callbacks that the Model's state has changed."""
        for callback in self._subscribers:
            callback()

# --- ViewModel ---
class CounterViewModel:
    """
    The ViewModel acts as an intermediary between the Model and the View.
    It exposes data from the Model in a View-friendly format and handles
    commands from the View, translating them into Model operations.
    """
    def __init__(self, model: CounterModel):
        self._model = model
        self._update_listeners = [] # Callbacks for the View to update itself

        # Subscribe to the Model's changes so the ViewModel can react
        self._model.subscribe(self._on_model_changed)

    def get_counter_value(self):
        """Returns the current counter value from the Model."""
        return self._model.get_count()

    def increment_command(self):
        """
        Command exposed to the View for incrementing.
        Calls the corresponding method on the Model.
        """
        self._model.increment()

    def decrement_command(self):
        """
        Command exposed to the View for decrementing.
        Calls the corresponding method on the Model.
        """
        self._model.decrement()

    def reset_command(self):
        """
        Command exposed to the View for resetting.
        Calls the corresponding method on the Model.
        """
        self._model.reset()

    def _on_model_changed(self):
        """
        This method is called by the Model when its state changes.
        It then notifies all subscribed Views to update their display.
        """
        self._notify_update_listeners()

    def add_update_listener(self, callback):
        """Allows the View to subscribe to ViewModel updates."""
        if callback not in self._update_listeners:
            self._update_listeners.append(callback)

    def remove_update_listener(self, callback):
        """Removes a View's update listener."""
        if callback in self._update_listeners:
            self._update_listeners.remove(callback)

    def _notify_update_listeners(self):
        """Notifies all subscribed Views about a change in the ViewModel's state."""
        for callback in self._update_listeners:
            callback()

# --- View ---
class CounterView(tkb.Frame):
    """
    The View is responsible for the user interface.
    It displays data from the ViewModel and sends user actions (commands)
    to the ViewModel. It has no direct knowledge of the Model.
    """
    def __init__(self, master, viewmodel):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.viewmodel = viewmodel
        self.create_widgets()
        self.bind_viewmodel()

    def create_widgets(self):
        """Creates and lays out the UI elements."""
        # Create a StringVar to hold the counter text. This variable will be
        # directly updated by the ViewModel and automatically reflected in the Label.
        self.counter_text_var = StringVar()
        self.counter_label = tkb.Label(
            self,
            textvariable=self.counter_text_var, # Binds the Label to the StringVar
            font=("Helvetica", 48, "bold"),
            bootstyle="primary"
        )
        self.counter_label.pack(pady=20)

        # Buttons
        button_frame = tkb.Frame(self)
        button_frame.pack(pady=10)

        self.increment_button = tkb.Button(
            button_frame,
            text="Increment",
            command=self.viewmodel.increment_command, # Calls ViewModel method directly
            bootstyle="success"
        )
        self.increment_button.pack(side="left", padx=10)

        self.decrement_button = tkb.Button(
            button_frame,
            text="Decrement",
            command=self.viewmodel.decrement_command, # Calls ViewModel method directly
            bootstyle="warning"
        )
        self.decrement_button.pack(side="left", padx=10)

        self.reset_button = tkb.Button(
            button_frame,
            text="Reset",
            command=self.viewmodel.reset_command, # Calls ViewModel method directly
            bootstyle="danger"
        )
        self.reset_button.pack(side="left", padx=10)

    def bind_viewmodel(self):
        """
        Establishes the binding from the ViewModel to the View.
        The View subscribes to updates from the ViewModel.
        """
        # Perform an initial update to show the starting counter value
        self.update_counter_display()

        # Subscribe to the ViewModel's update notification.
        # Whenever the ViewModel notifies, update_counter_display will be called.
        self.viewmodel.add_update_listener(self.update_counter_display)

    def update_counter_display(self):
        """
        This method is called by the ViewModel when its state changes.
        It updates the StringVar, which in turn updates the Label.
        """
        self.counter_text_var.set(str(self.viewmodel.get_counter_value()))

# --- Main Application ---
def main():
    """
    The main function to set up and run the application.
    It orchestrates the creation of Model, ViewModel, and View.
    """
    root = tkb.Window(themename="superhero") # Choose your preferred ttkbootstrap theme
    root.title("MVVM Counter Demo")
    root.geometry("500x300")
    root.resizable(False, False)

    # 1. Create the Model instance
    model = CounterModel()

    # 2. Create the ViewModel instance, passing the Model to it
    viewmodel = CounterViewModel(model)

    # 3. Create the View instance, passing the ViewModel to it
    view = CounterView(root, viewmodel)

    root.mainloop()

if __name__ == "__main__":
    main()