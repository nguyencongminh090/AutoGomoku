<div align="center">
  <h1>AutoGomoku</h1>
  <p><em>Automated Gomoku Bot with UI</em></p>
</div>

---

## Overview

AutoGomoku is an advanced Gomoku (Five-in-a-Row) bot featuring a modern Python-based UI, game engine, and automation utilities. It is designed for both playing and analyzing Gomoku games, with a focus on usability and extensibility.

---

## Features

- **Intuitive UI**: Easy-to-use interface for playing and observing games
- **Engine Integration**: Compatible with Gomocup protocol engines
- **Screen Capture & Detection**: Automatic board recognition and move detection
- **Flexible Time Control**: Configurable match time and increment settings
- **Dual Control Modes**: 
  - Auto mode for continuous play
  - Manual mode with move confirmation
- **Real-time Analysis**: Live display of search depth, winrate, and PV

---

## Requirements

Just run:
```powershell
pip install -r requirements.txt
```

---

## Installation

1. **Clone the repository**
   ```powershell
   git clone https://github.com/nguyencongminh090/AutoGomoku
   cd AutoGomoku/source
   ```
2. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```
   > **Note:** Some dependencies might require additional system packages. Check the error messages if any installation issues occur.

---

## 🎮 Controls

### Hotkeys
- `Ctrl + Shift + X`: Start game thread
- `Alt + S`: Stop game
- `Alt + R`: Clear log text
- `Alt + D`: Display search info
- `Alt + Q`: Stop engine search
- `Alt + M`: Continue move (in manual mode)
- `ESC`: Turn off

---

## 💻 Usage

1. **Initial Setup**
   - Choose engine (*) 
   - Set time management settings

2. **Board Detection**
   - Detect game board (*)

3. **Activation**
   - Turn on the system

4. **Operation**
   - Use hotkeys to control the game

(*) Required steps

---

## Project Structure

```
source/
│
├── pygomo/         # Gomoku engine, protocol, and core logic
│   ├── engine.py       # Main Gomoku logic and move generation
│   ├── gomocup.py      # Gomocup protocol support
│   ├── protocol.py     # Protocol definitions
│   └── ...
├── ui/             # User Interface (MVC pattern)
│   ├── model.py        # Data model for UI
│   ├── view_model.py   # ViewModel for UI logic
│   ├── view.py         # Main Tkinter window and widgets
│   └── ...
├── utils/          # Utilities for board, detection, helpers
│   ├── board.py        # Board representation and helpers
│   ├── detect.py       # Board/screen detection logic
│   ├── screen_capture.py # Screen capture utilities
│   └── ...
├── test_ui.py      # Entry point: launches the UI (main app)
├── main_test.py    # Script for engine/utilities testing
├── test_detect_open.py # Script for board/screen detection test
├── color.cfg       # Color configuration for UI
└── ReadMe.md       # Project documentation
```

### Component Details

- **pygomo/**: Engine communication and protocol handling
  - Manages interaction with Gomocup-compatible engines
  - Implements move generation and protocol parsing

- **ui/**: User interface implementation
  - Follows MVC pattern for clean separation of concerns
  - Handles user input and visual feedback
  - Manages game state and engine communication

- **utils/**: Core functionality
  - Board detection and screen capture
  - Move validation and pattern recognition
  - Helper utilities for game automation

---

## Customization & Extending

- **UI Modifications**: Edit files in `ui/` to customize the interface
- **Engine Integration**: Update `pygomo/` for different engine protocols
- **Detection Logic**: Modify `utils/` for custom board detection

---

## License

This project is licensed under the MIT License. See `LICENSE` file for details.

---

<div align="center">
  <sub>Built with ❤️ by Nguyen Cong Minh</sub>
</div>
