from tkinter.filedialog import askopenfilename
from .model             import Model

class ViewModel:
    """ViewModel layer for the Gomoku game automation application.
    
    Acts as an intermediary between the UI (View) and the business logic (Model),
    following the MVVM (Model-View-ViewModel) pattern. Exposes data bindings and
    commands that the UI can interact with while keeping the view decoupled from
    the model implementation.
    """

    def __init__(self, model: Model):
        """Initialize the ViewModel with a reference to the Model.
        
        Sets up data bindings that connect UI elements to model properties,
        allowing for automatic synchronization between the view and model state.
        
        Args:
            model (Model): The backend model instance containing game logic
                           and state management.
        """

        self.__model       = model
        self.time_entry    = self.__model.time_match
        self.timeP_entry   = self.__model.time_plus
        self.engine_entry  = self.__model.engine
        self.switch_button = self.__model.mode
        self.log_text      = self.__model.text_box

    def safe_kill_engine(self):
        """Force terminate the engine process if it's still running.
        
        Delegates to the model's safe_kill_engine method to forcefully stop
        the engine process. This is typically used as a fallback when normal
        termination fails.
        """

        self.__model.safe_kill_engine()

    def detect_board(self, master):
        """Detect and locate the game board on the screen.
        
        Initiates board detection process through the model. If successful,
        the board position will be stored and used for automated gameplay.
        
        Args:
            master: The master window/widget reference needed for screen capture.
                    Typically the main application window.
        
        Side Effects:
            Updates the log text with detection results and may display
            debug information if configured.
        """

        self.__model.detect_board(master)

    def select_engine(self):
        """Open a file dialog to select the Gomoku engine executable.
        
        Displays a file selection dialog filtered for executable files (.exe).
        If a file is selected, updates the engine path in the model's data binding,
        which will automatically reflect in any bound UI elements.
        
        Side Effects:
            Updates the engine_entry data binding with the selected file path.
            Does nothing if the user cancels the dialog.
        """

        fn = askopenfilename(filetypes=[("Executable Files", "*.exe")], title="Select Engine")
        if fn != '':
            self.engine_entry.set(fn)

    def turn_on(self):
        """Turn on the game automation system.
        
        Validates prerequisites (board detection, engine configuration) and
        initializes the engine for gameplay. Must be called before starting
        any games.
        
        Raises:
            AssertionError: If board position not detected, engine path not set,
                            or engine already running.
        """

        self.__model.turn_on()

    def turn_off(self):
        """Turn off the game automation system.
        
        Stops any running games and terminates the engine. This performs
        a clean shutdown of the automation system and releases resources.
        
        Side Effects:
            Stops current game if running and terminates the engine process.
            Updates log text with shutdown status.
        """

        self.__model.turn_off()
