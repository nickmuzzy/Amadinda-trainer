# Amadinda Trainer

An educational software tool for learning traditional Ugandan amadinda xylophone patterns, developed as part of a Master's thesis exploring AI-assisted educational technology creation.

**Author**: Nicholas Muzyczka  
**License**: GNU General Public License v3.0 (GPL v3)

## Overview

The Amadinda Trainer provides an interactive platform for learning amadinda music through TUBS (Time Unit Box System) notation. Students can compose patterns for two interlocking players (Omunazi and Omwawuzi), experiencing the fundamental principle of African polyrhythmic music where individual parts combine to create emergent melodic patterns.

## Features

- **Interactive TUBS Notation Grid** - Visual representation of amadinda patterns
- **Traditional Pattern Library** - Authentic pieces from Kiganda repertoire
- **Pattern Validation System** - Automatic detection of non-traditional patterns
- **Interlocking Playback** - Demonstrates polyrhythmic structures
- **Cultural Context Integration** - Traditional patterns with cultural descriptions
- **Educational Scaffolding** - Visual indicators, metronome, keyboard shortcuts
- **Advanced Audio Controls** - Master volume, main notes, upper octave, omukoonezi, and metronome volume
- **Octave Plus Mode** - Plays upper octave notes (C3-A3) alongside main notes
- **Omukoonezi Mode** - Plays high octave notes (C4-D4) for traditional patterns
- **Pattern Size Toggle** - Switch between 6 and 12 note patterns
- **Note Name Display** - Toggle between numbered and note name labels
- **Strict Rules Mode** - Enforce traditional composition rules
- **Volume Mixer Dialog** - Comprehensive audio mixing interface

## Installation

### Prerequisites
- Python 3.8 or higher
- Linux (tested on Ubuntu)

### From Source
1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python3 amadinda_trainer.py
   ```

### Using the Run Script
```bash
chmod +x run_amadinda.sh
./run_amadinda.sh
```

### Using the AppImage (Recommended)
Download the latest AppImage from releases and run:
```bash
chmod +x AmadindaTrainer-x86_64.AppImage
./AmadindaTrainer-x86_64.AppImage
```

The AppImage is self-contained and includes all dependencies - no installation required!

## Building a Standalone Executable

1. Create a virtual environment:
   ```bash
   python3 -m venv amadinda_env
   source amadinda_env/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install pygame PyQt5 numpy pyinstaller
   ```

3. Build the executable:
   ```bash
   pyinstaller --onefile --windowed --add-data "samples:samples" --add-data "config.py:." amadinda_trainer.py
   ```

4. The executable will be created in `dist/amadinda_trainer`

## Usage

### Basic Controls
- **Number keys 1-5**: Insert notes (C, D, E, G, A)
- **Arrow keys**: Navigate between cells
- **Delete/Backspace**: Clear current cell
- **Space**: Play/Stop playback
- **M**: Toggle metronome
- **C**: Toggle count-off
- **Left/Right arrows**: Step through playback position (when not playing)

### Pattern Composition
1. Click on cells to add notes
2. Use the number keys 1-5 for quick entry
3. Navigate with arrow keys
4. Play your pattern to hear the interlocking result

### Traditional Patterns
- Load authentic amadinda pieces from the "Load Traditional Pattern" button
- Study cultural context and composition principles
- Learn traditional Kiganda music rules

## Educational Value

This software specifically addresses groove and rhythmic understanding through:
- **Interlocking patterns** that demonstrate polyrhythmic structures
- **Traditional composition rules** that develop intuitive rhythmic sense
- **Experiential learning** through active composition and performance
- **Cultural context** connecting musical practice to social meaning

## Technical Details

- **Language**: Python 3
- **GUI Framework**: PyQt5
- **Audio**: Pygame
- **Packaging**: PyInstaller
- **Architecture**: Object-oriented with signal/slot pattern

## Development

This software was developed using AI assistance to demonstrate how artificial intelligence can democratize educational technology creation, enabling music educators to develop specialized tools without extensive programming expertise.

## License

This project is licensed under the GNU General Public License v3.0 (GPL v3). See the [LICENSE](LICENSE) file for the full license text.

### License Summary
- **Free to use**: You can use, modify, and distribute this software
- **No commercial use**: Any derivative works must also be open source under GPL v3
- **Source code required**: If you distribute the software, you must provide the source code
- **Educational use**: Perfect for educational and research purposes

This software was developed as part of a Master's thesis exploring AI-assisted educational technology creation.

## Contact

For questions about this software or the research behind it, please refer to the associated thesis documentation.
