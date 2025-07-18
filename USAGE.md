# AutoGomoku Usage Guide

## 1. Overview

AutoGomoku is a sophisticated bot designed to automate gameplay and analysis of the game Gomoku (Five-in-a-Row). It features a graphical user interface (GUI), a robust backend that interfaces with standard Gomoku engines, and advanced screen-analysis capabilities to detect the game board and moves in real-time.

The application is built on a Model-View-ViewModel (MVVM) architecture, ensuring a responsive user experience by handling long-running tasks like game analysis and hotkey listening in separate background threads.

## 2. Key Features

- **Graphical User Interface:** A simple control panel for configuring the bot and viewing logs.
- **Gomocup Engine Compatibility:** Can use any Gomoku engine that adheres to the standard Gomocup communication protocol.
- **Automatic Board Detection:** A screen capture tool allows you to select the game board on your screen, which the bot will then use to track the game state.
- **Real-time Move Detection:** The bot continuously watches the selected board area to detect new moves made by an opponent.
- **Configurable Time Controls:** Set the match time and increment per move.
- **Dual Control Modes:**
  - **Auto Mode:** The bot plays its moves automatically.
  - **Manual Mode:** The bot suggests a move but waits for a hotkey press (`Alt+M`) before executing the mouse click.
- **Live Engine Analysis:** Use a hotkey (`Alt+D`) to display the engine's current search depth, win rate, and principal variation (PV) in the log.

## 3. Installation and Setup

Follow these steps to get the application running.

### Step 1: Prerequisites
Ensure you have Python 3.10 or newer installed on your system.

### Step 2: Clone the Repository
Open a terminal or command prompt and clone the project:
```bash
git clone https://github.com/nguyencongminh090/AutoGomoku
cd AutoGomoku/source
```

### Step 3: Create a Virtual Environment (Recommended)
Using a virtual environment is highly recommended to avoid conflicts with other Python projects.
```bash
# Create the virtual environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Step 4: Install Dependencies
Install the required Python packages using the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

## 4. Configuration (`tool_config.toml`)

You can adjust the bot's behavior by editing the `tool_config.toml` file before launching the application.

- `show_window = true`: Set to `false` to hide the console window on startup.
- `show_log = false`: Set to `true` to print all raw communication from the Gomoku engine to the console. This is useful for debugging engine issues.
- `debug_board = false`: Set to `true` to have the application display the detected board region in a separate window for 5 seconds after detection.

## 5. How to Use: Step-by-Step Workflow

1.  **Launch the Application:**
    Run `main.py` from the `source` directory.
    ```bash
    python main.py
    ```
    The main control panel will appear on your screen.

2.  **Select Your Engine:**
    - Click the **"Setting"** button to open the settings panel.
    - Click **"Select Engine"** and navigate to the executable file (`.exe`) of your chosen Gomocup-compatible engine.

3.  **Detect the Game Board:**
    - Arrange your screen so that the Gomoku game board you want to play on is visible.
    - Click the **"Detect Board"** button. The screen will darken.
    - Click and drag a rectangle precisely around the game board area. When you release the mouse, the coordinates will be captured.
    - A "Found board" message will appear in the log if successful.

4.  **Turn the System On:**
    - Click the **"Turn On"** button. This loads the engine into memory and prepares the system for automation. A "Turned on" message will appear.

5.  **Start the Game:**
    - Press the hotkey `Ctrl+Shift+X`.
    - The bot will now start its main game loop, detect any opening moves, and begin playing.

## 6. Hotkey Reference

| Hotkey | Action | Description |
| :--- | :--- | :--- |
| `Ctrl+Shift+X` | **Start Game** | Initiates the main game loop after the system is turned on. |
| `Alt+S` | **Stop Game** | Stops the current game, but leaves the engine running and system on. |
| `Alt+R` | **Clear Log** | Clears all text from the log window. |
| `Alt+D` | **Display Info** | Shows the engine's current search analysis in the log. |
| `Alt+Q` | **Stop Search** | Manually tells the engine to stop its current thinking process. |
| `Alt+M` | **Confirm Move** | In Manual mode, this confirms the suggested move and executes the click. |
| `ESC` | **Turn Off** | Stops the game, terminates the engine, and stops the hotkey listener. |
| `Alt+=` | **Inc Time** | Increases the match time by 1 second. |
| `Alt+-` | **Dec Time** | Decreases the match time by 1 second. |
| `Alt+Enter` | **Set Current Time** | Sets the internal timer to the value in the "Time (s)" box. |
| `Alt+Shift+Enter`| **Sync Time from Bot**| Updates the "Time (s)" box with the bot's internal remaining time. |

## 7. Troubleshooting

- **Problem: The hotkeys become unresponsive during a long game.**
  - **Symptom:** After running for a while, especially after using `Alt+D`, the bot stops responding to hotkeys like `Alt+S`. The game continues, but you can't control it.
  - **Cause:** This was due to a blocking call in the search info display, which froze the single hotkey worker thread.
  - **Solution:** This issue has been fixed in the latest version by running the engine communication in a separate, non-blocking thread.

- **Problem: The bot fails with a "No board found" error.**
  - **Cause:** The screen detection logic could not identify a valid board in the region you selected.
  - **Solution:** Try again, ensuring your selection is precise. Make sure the game board is not obscured by other windows and has good contrast and lighting.

- **Problem: The engine fails to start or crashes.**
  - **Cause:** The path to the engine executable is incorrect, or the engine itself has a bug.
  - **Solution:**
    1. Double-check that the engine path in the UI is correct.
    2. Set `show_log = true` in `tool_config.toml` and restart. Observe the console output for any error messages from the engine itself.
