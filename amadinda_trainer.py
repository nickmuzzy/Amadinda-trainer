#!/usr/bin/env python3

"""
Amadinda Trainer - An educational tool for learning Ugandan amadinda xylophone patterns

Copyright (C) 2024

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import time
import threading
import pygame
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
                            QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
                            QSlider, QFrame, QGridLayout, QComboBox, QGroupBox,
                            QSizePolicy, QScrollArea, QSpacerItem, QMessageBox,
                            QButtonGroup, QToolTip, QDialog, QTabWidget, QTextEdit,
                            QListWidget)
from PyQt5.QtCore import QEvent, Qt, QSize, pyqtSignal, QObject, QPoint, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QCursor, QPainter, QPixmap

# Add the current directory to the Python path to ensure config can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import PENTATONIC_NOTES, DEFAULT_TEMPO, DEFAULT_PATTERN_LENGTH, PRIMARY_OCTAVE

# Mapping between numbers and notes
NUMBER_TO_NOTE = {
    '1': 'C', '2': 'D', '3': 'E', '4': 'G', '5': 'A'
}
NOTE_TO_NUMBER = {
    'C': '1', 'D': '2', 'E': '3', 'G': '4', 'A': '5'
}

# Unicode symbols for button icons
PLAY_SYMBOL = "▶"
STOP_SYMBOL = "⏹"
RESET_SYMBOL = "⟲"

# Define prohibited patterns in Kiganda music (based on Kubik's research)
# Note: Some traditional pieces may break these rules, suggesting they are guidelines rather than strict prohibitions
PROHIBITED_PATTERNS = [
    # Most strict rules - rarely broken
    "111", "222", "333", "444", "555",  # Three identical notes
    
    # More flexible rules - sometimes broken in traditional pieces
    # "121", "232", "343", "454",  # Adjacent notes around a central note
    # "151", "212", "323", "434", "545",  # Adjacent notes around a central note (alt pattern)
    # "112", "334", # Certain rising patterns
    # "115", "332", "443", "554",  # Certain falling patterns
    # "155", "544",  # Certain patterns with repeated notes
    # "123", "234", "345", "451", "512"   # Rising scalar patterns
]

# Traditional Amadinda Repertoire
TRADITIONAL_PATTERNS = {
    "Banno bakoola ng'osiga": {
        "description": "Your friends are pruning but you are sowing",
        "okunaga": ["G", "E", "G", "C", "E", "E", "G", "D", "E", "G", "D", "C"],
        "okwawula": ["A", "E", "E", "A", "A", "E", "A", "D", "E", "A", "C", "C"]
    },
    "Ndyegulira ekkadde": {
        "description": "I will buy myself an old woman",
        "okunaga": ["D", "C", "D", "D", "D", "A", "D", "C", "C", "D", "E", "A"],
        "okwawula": ["A", "G", "D", "A", "G", "D", "A", "G", "D", "A", "G", "D"]
    },
    "Ekyuma ekya Bora": {
        "description": "The swinging machine of Bora",
        "okunaga": ["G", "E", "D", "E", "E", "D", "G", "E", "D", "E", "E", "D"],
        "okwawula": ["A", "A", "G", "C", "A", "C", "A", "A", "C", "C", "A", "C"]
    },
    "Omunyoro atunda nandere": {
        "description": "The Munyoro sells Nandere fish",
        "okunaga": ["A", "G", "E", "A", "G", "E", "A", "G", "E", "G", "G", "D"],
        "okwawula": ["D", "D", "C", "D", "D", "C", "D", "E", "C", "D", "C", "C"]
    }
}


class Signaler(QObject):
    """Helper class to emit signals from non-GUI threads"""
    update_position = pyqtSignal(int)
    playback_finished = pyqtSignal()
    pattern_check_needed = pyqtSignal()


class CustomToolTip(QLabel):
    """Custom tooltip with better styling and positioning control"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip)
        self.setStyleSheet("""
            background-color: #FFFFD3;
            color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 4px;
            padding: 6px;
            font-size: 12px;
        """)
        self.setWordWrap(True)
        self.setMaximumWidth(300)
        self.hide()

    def showAt(self, pos, text):
        self.setText(text)
        self.adjustSize()
        self.move(pos)
        self.show()


class PatternDialog(QDialog):
    """Dialog for selecting traditional patterns"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Traditional Pattern")
        self.setMinimumSize(600, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #212121;
                color: #FFFFFF;
            }
            QListWidget {
                background-color: #424242;
                color: #FFFFFF;
                border: 1px solid #616161;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #FF9800;
            }
            QPushButton {
                background-color: #424242;
                color: #FFFFFF;
                border: 1px solid #616161;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Select a Traditional Amadinda Pattern")
        title.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(title)
        
        # Description
        desc = QLabel("These are authentic patterns from traditional Kiganda music:")
        layout.addWidget(desc)
        
        # Pattern list
        self.pattern_list = QListWidget()
        for pattern_name in TRADITIONAL_PATTERNS.keys():
            pattern = TRADITIONAL_PATTERNS[pattern_name]
            item_text = f"{pattern_name}\n{pattern['description']}"
            self.pattern_list.addItem(item_text)
        
        layout.addWidget(self.pattern_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        load_button = QPushButton("Load Pattern")
        load_button.clicked.connect(self.accept)
        button_layout.addWidget(load_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Connect selection
        self.pattern_list.itemDoubleClicked.connect(self.accept)

class AboutDialog(QDialog):
    """About dialog with tabbed information about Amadinda"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Amadinda")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #212121;
                color: #FFFFFF;
            }
            QTabWidget::pane {
                border: 1px solid #616161;
                background-color: #212121;
            }
            QTabBar::tab {
                background-color: #424242;
                color: #FFFFFF;
                border: 1px solid #616161;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 5px 10px;
            }
            QTabBar::tab:selected {
                background-color: #616161;
            }
            QTextEdit {
                background-color: #212121;
                color: #FFFFFF;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Add logo at the top of the About dialog
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples", "Groove_Builders_Logo.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            # Scale logo to reasonable size (80px height for About dialog)
            logo_pixmap = logo_pixmap.scaledToHeight(80, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
            layout.addSpacing(10)  # Add some space between logo and tabs
        
        tab_widget = QTabWidget()
        
        # General Tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        general_text = QTextEdit()
        general_text.setReadOnly(True)
        general_text.setHtml("""
            <h2>AMADINDA COMPOSER</h2>
            <p>The amadinda is a xylophone used by the Baganda people of Uganda. This application
            helps you create and explore traditional amadinda music patterns.</p>
            
            <p>In traditional amadinda music, two players (sometimes with a third) create 
            interlocking patterns that combine to form complex rhythmic and melodic structures.</p>
            
            <p>This application uses a 12-pulse cycle, which is a common structure in amadinda music.
            The numbers 1-5 represent the five notes of the pentatonic scale: C, D, E, G, and A.</p>
        """)
        
        general_layout.addWidget(general_text)
        tab_widget.addTab(general_tab, "General")
        # Players Tab
        players_tab = QWidget()
        players_layout = QVBoxLayout(players_tab)
        
        players_text = QTextEdit()
        players_text.setReadOnly(True)
        players_text.setHtml("""
            <h2>AMADINDA PLAYERS AND THEIR ROLES:</h2>
            
            <h3>Player A (Omunazi):</h3>
            <ul>
                <li>Establishes the main theme (okunaga)</li>
                <li>Typically sits on the right side of the instrument</li>
                <li>Plays the foundational pattern</li>
            </ul>
            
            <h3>Player B (Omwawuzi):</h3>
            <ul>
                <li>Adds the second part (okwawula)</li>
                <li>Sits on the left side of the instrument</li>
                <li>Plays notes that interlock between Player A's notes</li>
            </ul>
            
            <p>Sometimes a third player (Omukoonezi) adds additional notes that double
            some of the existing notes at the octave, creating a richer sound.</p>
            
            <p>The interlocking between these parts creates "inherent patterns" that emerge
            from the combined texture - melodies that aren't played by any single performer
            but arise from the interaction of all parts.</p>
        """)
        
        players_layout.addWidget(players_text)
        tab_widget.addTab(players_tab, "Players")
        # Composition Tab
        composition_tab = QWidget()
        composition_layout = QVBoxLayout(composition_tab)
        
        composition_text = QTextEdit()
        composition_text.setReadOnly(True)
        composition_text.setHtml("""
            <h2>AMADINDA COMPOSITION PRINCIPLES:</h2>
            
            <p>Traditional amadinda music follows certain rules and patterns:</p>
            
            <ol>
                <li>Avoidance of three identical consecutive notes (e.g., 111, 222)</li>
                <li>Avoidance of direct ascending or descending scalar patterns
                in combined melodies (e.g., 123, 321)</li>
                <li>Preference for certain intervallic relationships that create
                pleasing inherent patterns</li>
                <li>The interlocking nature means Players A and B never play simultaneously
                but alternate to create a continuous flow of notes</li>
            </ol>
            
            <p>When "Traditional Mode" is enabled, this application helps enforce these
            rules to create authentic amadinda-style compositions.</p>
            
            <p>Based on the research of Gerhard Kubik, who extensively documented
            amadinda musical practices in Uganda.</p>
        """)
        
        composition_layout.addWidget(composition_text)
        tab_widget.addTab(composition_tab, "Composition")
        
        # Usage Tab
        usage_tab = QWidget()
        usage_layout = QVBoxLayout(usage_tab)
        
        usage_text = QTextEdit()
        usage_text.setReadOnly(True)
        usage_text.setHtml("""
            <h2>HOW TO USE THIS APPLICATION:</h2>
            
            <ol>
                <li>Enter numbers 1-5 in the cells to create patterns:
                    <ul>
                        <li>1 = C</li>
                        <li>2 = D</li>
                        <li>3 = E</li>
                        <li>4 = G</li>
                        <li>5 = A</li>
                    </ul>
                </li>
                <li>Player A (green cells) and Player B (orange cells) alternate in time.
                In performance, they would be interleaved rather than played separately.</li>
                <li>The Position indicators show how the notes from both players
                interlock to create the full piece.</li>
                <li>Use "Traditional Mode" to create compositions that follow authentic
                amadinda composition principles.</li>
                <li>You can generate random patterns and play them back.</li>
                <li>Experiment with creating your own patterns and see how the
                interlocking creates interesting musical structures!</li>
            </ol>
        """)
        
        usage_layout.addWidget(usage_text)
        tab_widget.addTab(usage_tab, "Using This App")
        
        layout.addWidget(tab_widget)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: #FFFFFF;
                border: 1px solid #616161;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)
class AmadindaKey(QPushButton):
    """A custom button representing a single amadinda key"""
    def __init__(self, note, octave, use_note_names=False, parent=None):
        # Use numbered labels by default, note names only if specified
        display_text = note if use_note_names else NOTE_TO_NUMBER[note]
        super().__init__(display_text, parent)
        self.note = note
        self.octave = octave
        self.setMinimumSize(QSize(60, 80))  # Smaller, more compact keys
        self.setFont(QFont('Arial', 16, QFont.Bold))  # Larger font

        # Style the button like a wooden key
        if note in ['C', 'E', 'A']:  # Alternating colors
            self.setStyleSheet("""
                QPushButton {
                    background-color: #8B4513; /* SaddleBrown */
                    color: white;
                    border: 2px solid #654321;
                    border-radius: 5px;
                }
                QPushButton:pressed {
                    background-color: #654321;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #A0522D; /* Sienna */
                    color: white;
                    border: 2px solid #654321;
                    border-radius: 5px;
                }
                QPushButton:pressed {
                    background-color: #654321;
                }
            """)

    def update_display(self, use_note_names):
        """Update the button text based on display mode"""
        display_text = self.note if use_note_names else NOTE_TO_NUMBER[self.note]
        self.setText(display_text)


class TUBSCell(QPushButton):
    """A single cell in the TUBS notation grid"""
    def __init__(self, position, player='a', parent=None):
        super().__init__(parent)
        self.position = position
        self.player = player
        self.note = None
        self.focused = False
        self.is_problematic = False
        self.setFixedSize(QSize(85, 85))  # Even larger cells
        self.setCheckable(True)
        self.update_style()

        # Custom tooltip for warning messages
        self.custom_tooltip = None
        self.warnings = []

    def set_note(self, note):
        """Set the note for this cell"""
        self.note = note
        self.update_style()

    def get_note(self):
        """Get the current note"""
        return self.note

    def set_focused(self, focused):
        """Set whether this cell is currently in focus (for keyboard input)"""
        self.focused = focused
        self.update_style()

    def set_problematic(self, is_problematic, warnings=None):
        """Mark this cell as part of a problematic pattern"""
        if warnings is None:
            warnings = []
        self.is_problematic = is_problematic
        self.warnings = warnings
        self.update_style()

    def update_style(self):
        """Update button appearance based on state"""
        # Base styles
        focused_border = "3px solid #1E88E5" if self.focused else "1px solid #9E9E9E"
        font_size = "42px"  # INCREASED font size (was 24px)

        # Different style for Player A and B
        bg_color = "#4CAF50" if self.player == 'a' else "#FF9800"  # Green for A, Orange for B
        dark_color = "#2E7D32" if self.player == 'a' else "#E65100"  # Darker versions

        # Add warning style if this cell is part of a problematic pattern
        if self.is_problematic:
            warning_border = "3px dashed #FFD700"  # Golden dashed border for warning
        else:
            warning_border = ""

        if self.note:
            # Cell has a note
            self.setText(self.note)
            base_style = f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: white;
                    border: {focused_border};
                    {warning_border};
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: {font_size};
                }}
                QPushButton:checked {{
                    background-color: {dark_color};
                }}
            """

            # Add warning styling if problematic
            if self.is_problematic:
                self.setStyleSheet(base_style.replace("background-color", "background: linear-gradient(to bottom, #FFD700, %s)" % bg_color))
                self.setToolTip("\n".join(self.warnings))
            else:
                self.setStyleSheet(base_style)
                self.setToolTip("")
        else:
            # Empty cell
            self.setText("")
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #424242; /* Dark Gray for drum machine look */
                    border: {focused_border};
                    border-radius: 4px;
                    font-size: {font_size};
                }}
                QPushButton:checked {{
                    background-color: #616161; /* Lighter Gray */
                }}
            """)
            self.setToolTip("")

    def enterEvent(self, event):
        """Handle mouse hover entry"""
        super().enterEvent(event)
        if self.is_problematic and self.warnings:
            # Show custom tooltip
            global_pos = self.mapToGlobal(QPoint(self.width() + 5, 0))
            tooltip_text = "\n".join(self.warnings)
            QToolTip.showText(global_pos, tooltip_text)

    def leaveEvent(self, event):
        """Handle mouse hover exit"""
        super().leaveEvent(event)
        QToolTip.hideText()
class StatusIndicator(QWidget):
    """A visual indicator for pattern status"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.status = "good"  # Can be "good" or "warning"
        self.tooltip_text = "Pattern is valid in traditional Kiganda music"

    def set_status(self, status, tooltip=None):
        """Set the status indicator color"""
        self.status = status
        if tooltip:
            self.tooltip_text = tooltip
        self.setToolTip(self.tooltip_text)
        self.update()

    def paintEvent(self, event):
        """Draw the status indicator"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.status == "good":
            painter.setBrush(QColor("#4CAF50"))  # Green
            self.setToolTip("Pattern follows traditional Kiganda composition rules")
        else:
            painter.setBrush(QColor("#FFC107"))  # Amber

        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 12, 12)

        painter.end()


class SequencerLED(QLabel):
    """A LED indicator for the sequencer transport"""
    def __init__(self, position, parent=None):
        super().__init__(parent)
        self.position = position
        self.setFixedSize(QSize(20, 20))
        self.setAlignment(Qt.AlignCenter)
        self.setActive(False)

    def setActive(self, active):
        """Set whether this LED is currently active"""
        if active:
            self.setStyleSheet("""
                background-color: #F44336; /* Red */
                border-radius: 10px;
                border: 1px solid #D32F2F;
            """)
        else:
            self.setStyleSheet("""
                background-color: #424242; /* Dark Gray */
                border-radius: 10px;
                border: 1px solid #212121;
            """)


class AmadindaTrainer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize pygame for audio
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            print("Pygame mixer initialized successfully")
        except Exception as e:
            print(f"Failed to initialize pygame mixer: {e}")
        
        pygame.init()

        # Set up the window
        self.setWindowTitle("Amadinda Trainer")
        self.setMinimumSize(1200, 600)

        # Create main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # Initialize variables
        self.countoff_enabled = False
        self.octave_plus = True
        self.omukoonezi_mode = False
        self.metronome_enabled = False
        
        # Volume control variables
        self.overall_volume = 70  # Default 70% - master volume
        self.main_volume = 80  # Default 80% - main notes
        self.upper_octave_volume = 70  # Default 70% - upper octave notes
        self.omukoonezi_volume = 80  # Default 80% - omukoonezi notes
        self.volume_dialog = None  # Volume control dialog
        self.pattern_length = DEFAULT_PATTERN_LENGTH  # Default is 6 notes per player (12 total)
        self.tempo = DEFAULT_TEMPO
        self.use_note_names = False
        self.metronome_volume = 0.2  # Start with 20% volume for metronome
        self.current_pattern_a = self.create_empty_pattern()
        self.current_pattern_b = self.create_empty_pattern()
        self.current_position = 0  # Initialize to 0 for playback position tracking
        self.current_focus_cell = None
        self.current_beat_position = 0
        self.is_playing = False
        self.play_thread = None
        self.current_note_selection = 'C'
        self.leds = []  # Initialize the LEDs list
        self.currently_playing_samples = {}  # Track playing samples

        # Create signaler for thread communication
        self.signaler = Signaler()
        self.signaler.update_position.connect(self.highlight_position)
        self.signaler.playback_finished.connect(self.playback_complete)
        self.signaler.pattern_check_needed.connect(self.check_pattern_validity)

        # Create custom tooltip for pattern warnings
        self.custom_tooltip = CustomToolTip()

        # Set paths to samples
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.xylophone_samples_path = os.path.join(self.base_path, "samples", "xylophone")
        self.metronome_samples_path = os.path.join(self.base_path, "samples", "metronome")
        
        # For packaged version, samples might be in a different location
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            self.base_path = sys._MEIPASS
            self.xylophone_samples_path = os.path.join(self.base_path, "samples", "xylophone")
            self.metronome_samples_path = os.path.join(self.base_path, "samples", "metronome")
            print(f"Running as packaged executable. Base path: {self.base_path}")
        else:
            print(f"Running as Python script. Base path: {self.base_path}")

        # Load samples
        self.load_samples()

        # Set up the UI
        self.init_ui()
    def load_samples(self):
        """Load all the samples into memory"""
        self.samples = {}
        missing_samples = []

        print(f"Loading samples from: {self.xylophone_samples_path}")
        print(f"Base path: {self.base_path}")
        print(f"Xylophone path exists: {os.path.exists(self.xylophone_samples_path)}")

        # Load xylophone samples
        if os.path.exists(self.xylophone_samples_path):
            print(f"Found xylophone samples directory: {self.xylophone_samples_path}")
            for filename in os.listdir(self.xylophone_samples_path):
                if filename.endswith('.wav'):
                    try:
                        sample_path = os.path.join(self.xylophone_samples_path, filename)
                        print(f"Loading sample: {sample_path}")
                        self.samples[filename] = pygame.mixer.Sound(sample_path)
                        # Set the default volume lower for all samples
                        self.samples[filename].set_volume(0.8)
                        print(f"Successfully loaded: {filename}")
                    except Exception as e:
                        print(f"Failed to load {filename}: {e}")
        else:
            print(f"WARNING: Xylophone samples directory not found: {self.xylophone_samples_path}")
            # Try alternative paths for packaged version
            if getattr(sys, 'frozen', False):
                alt_paths = [
                    os.path.join(os.path.dirname(sys.executable), "samples", "xylophone"),
                    os.path.join(os.getcwd(), "samples", "xylophone")
                ]
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        print(f"Found alternative xylophone path: {alt_path}")
                        self.xylophone_samples_path = alt_path
                        # Try loading from this path
                        for filename in os.listdir(alt_path):
                            if filename.endswith('.wav'):
                                try:
                                    sample_path = os.path.join(alt_path, filename)
                                    self.samples[filename] = pygame.mixer.Sound(sample_path)
                                    self.samples[filename].set_volume(0.8)
                                    print(f"Loaded from alternative path: {filename}")
                                except Exception as e:
                                    print(f"Failed to load {filename} from alternative path: {e}")
                        break

        # Load metronome sample
        if os.path.exists(self.metronome_samples_path):
            print(f"Found metronome samples directory: {self.metronome_samples_path}")
            for filename in os.listdir(self.metronome_samples_path):
                if filename.endswith(('.flac', '.wav')):
                    try:
                        sample_path = os.path.join(self.metronome_samples_path, filename)
                        print(f"Loading metronome: {sample_path}")
                        self.samples[filename] = pygame.mixer.Sound(sample_path)
                        # Set the metronome volume very low by default
                        self.samples[filename].set_volume(0.2)
                        print(f"Successfully loaded metronome: {filename}")
                    except Exception as e:
                        print(f"Failed to load {filename}: {e}")
        else:
            print(f"WARNING: Metronome samples directory not found: {self.metronome_samples_path}")
            # Try alternative paths for packaged version
            if getattr(sys, 'frozen', False):
                alt_paths = [
                    os.path.join(os.path.dirname(sys.executable), "samples", "metronome"),
                    os.path.join(os.getcwd(), "samples", "metronome")
                ]
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        print(f"Found alternative metronome path: {alt_path}")
                        self.metronome_samples_path = alt_path
                        # Try loading from this path
                        for filename in os.listdir(alt_path):
                            if filename.endswith(('.flac', '.wav')):
                                try:
                                    sample_path = os.path.join(alt_path, filename)
                                    self.samples[filename] = pygame.mixer.Sound(sample_path)
                                    self.samples[filename].set_volume(0.2)
                                    print(f"Loaded metronome from alternative path: {filename}")
                                except Exception as e:
                                    print(f"Failed to load {filename} from alternative path: {e}")
                        break

        # Check for missing essential samples - only check for samples we actually have
        for note in PENTATONIC_NOTES:
            # Only check octaves 2 and 3 since we don't have octave 4 samples
            for octave in range(2, 4):  # Check octaves 2 and 3 only
                sample_name = f"Mallet {note}{octave}.wav"
                if sample_name not in self.samples:
                    missing_samples.append(sample_name)

        print(f"Loaded {len(self.samples)} samples")

        if missing_samples:
            print("WARNING: Missing essential samples:")
            for sample in missing_samples[:10]:  # Print first 10 only to avoid flood
                print(f"  - {sample}")
            if len(missing_samples) > 10:
                print(f"  - ... and {len(missing_samples) - 10} more")

        # Print out available samples for debugging
        print("Available samples:")
        for sample_name in sorted(self.samples.keys()):
            print(f"  - {sample_name}")
        print(f"Total samples loaded: {len(self.samples)}")
    def create_empty_pattern(self):
        """Create empty pattern of specified length"""
        return [None] * self.pattern_length

    def get_combined_pattern_as_string(self):
        """Converts the combined pattern to a string for analysis"""
        total_pattern = []
        for i in range(self.pattern_length):
            if self.current_pattern_a[i]:
                total_pattern.append(self.current_pattern_a[i])
            if self.current_pattern_b[i]:
                total_pattern.append(self.current_pattern_b[i])

        # Convert note names to numbers for analysis
        pattern_numbers = [NOTE_TO_NUMBER[note] if note in NOTE_TO_NUMBER else note for note in total_pattern]
        return "".join(pattern_numbers)

    def check_pattern_validity(self):
        """Check if the current pattern follows traditional Kiganda composition rules"""
        combined_pattern = self.get_combined_pattern_as_string()
        problematic_cells = []

        # Reset all cells to non-problematic state
        for cells in [self.tubs_cells_a, self.tubs_cells_b]:
            for cell in cells:
                cell.set_problematic(False)

        # Check if both players have notes - traditional rules only apply to combined patterns
        has_player_a_notes = any(self.current_pattern_a)
        has_player_b_notes = any(self.current_pattern_b)
        
        # If only one player has notes, don't apply traditional rules
        if not (has_player_a_notes and has_player_b_notes):
            self.status_indicator.set_status("good", "Traditional rules apply to combined A+B patterns")
            return

        # No problematic patterns if pattern is too short
        if len(combined_pattern) < 3:
            self.status_indicator.set_status("good", "Pattern is too short for analysis")
            return

        # Check for problematic patterns
        found_issues = []

        # Look for each prohibited pattern
        for i in range(len(combined_pattern) - 2):
            pattern_fragment = combined_pattern[i:i+3]
            if pattern_fragment in PROHIBITED_PATTERNS:
                found_issues.append(pattern_fragment)

                # Determine which cells are part of this problematic pattern
                # We need to find the corresponding cells in the UI grid

                # Start tracking the pattern position in the combined sequence
                pattern_pos = 0
                found_cells = []

                # Go through a-cells and b-cells in interleaved order
                for j in range(self.pattern_length):
                    # Check a-cell
                    if self.current_pattern_a[j]:
                        if pattern_pos >= i and pattern_pos < i + 3:  # Is this part of the problematic pattern?
                            found_cells.append((self.tubs_cells_a[j], pattern_fragment))
                        pattern_pos += 1

                    # Check b-cell
                    if self.current_pattern_b[j]:
                        if pattern_pos >= i and pattern_pos < i + 3:  # Is this part of the problematic pattern?
                            found_cells.append((self.tubs_cells_b[j], pattern_fragment))
                        pattern_pos += 1

                # Add these cells to the problematic cells list
                problematic_cells.extend(found_cells)

        # Mark the cells that are part of problematic patterns
        for cell, pattern in problematic_cells:
            warning = f"Pattern '{pattern}' is not used in traditional Kiganda music.\n"
            warning += "This sequence would not appear in traditional compositions."

            if pattern[0] == pattern[1] == pattern[2]:
                warning += "\n\nThree identical notes in sequence is avoided."
            elif pattern == "123" or pattern == "234" or pattern == "345":
                warning += "\n\nThree ascending notes in sequence is avoided."

            cell.set_problematic(True, [warning])

        # Update status indicator
        if found_issues:
            issues_text = ", ".join(set(found_issues))  # Remove duplicates
            self.status_indicator.set_status("warning",
                f"Non-traditional patterns found: {issues_text}")
        else:
            self.status_indicator.set_status("good",
                "Pattern follows traditional Kiganda composition rules")
    def suggest_alternative_pattern(self, problematic_pattern):
        """Suggest an alternative pattern to replace a problematic one"""
        # Map problematic patterns to suggested alternatives
        alternatives = {
            "111": ["121", "131", "151"],
            "222": ["232", "242", "252"],
            "333": ["343", "353", "313"],
            "444": ["454", "414", "434"],
            "555": ["515", "525", "545"],
            # Add more mappings as needed
        }

        if problematic_pattern in alternatives:
            return alternatives[problematic_pattern]
        return ["Try changing one of the notes"]

    def show_about_dialog(self):
        """Show the About Amadinda dialog with tabbed information"""
        dialog = AboutDialog(self)
        dialog.exec_()

    def show_pattern_dialog(self):
        """Show the pattern selection dialog"""
        dialog = PatternDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Get selected pattern
            current_item = dialog.pattern_list.currentItem()
            if current_item:
                pattern_name = current_item.text().split('\n')[0]
                self.load_traditional_pattern(pattern_name)

    def load_traditional_pattern(self, pattern_name):
        """Load a traditional pattern into the current interface"""
        if pattern_name not in TRADITIONAL_PATTERNS:
            return
        
        pattern = TRADITIONAL_PATTERNS[pattern_name]
        
        # Stop playback if running
        if self.is_playing:
            self.toggle_playback()
        
        # Set pattern length to 12 if needed
        if self.pattern_length != 12:
            self.pattern_length = 12
            self.pattern_size_button.setText("12 → 6")
            self.recreate_ui()
        
        # Load the patterns
        self.current_pattern_a = pattern["okunaga"].copy()
        self.current_pattern_b = pattern["okwawula"].copy()
        
        # Update the UI cells
        self.update_pattern_display()
        
        # Show confirmation
        QMessageBox.information(
            self,
            "Pattern Loaded",
            f"Loaded: {pattern_name}\n{pattern['description']}"
        )

    def update_pattern_display(self):
        """Update the display of all cells with current patterns"""
        # Update Player A cells
        for i, note in enumerate(self.current_pattern_a):
            if i < len(self.tubs_cells_a):
                display_text = self.get_display_text(note) if note else ""
                self.tubs_cells_a[i].set_note(display_text if note else None)
        
        # Update Player B cells
        for i, note in enumerate(self.current_pattern_b):
            if i < len(self.tubs_cells_b):
                display_text = self.get_display_text(note) if note else ""
                self.tubs_cells_b[i].set_note(display_text if note else None)
        
        # Check pattern validity
        self.check_pattern_validity()

    def init_ui(self):
        """Initialize the user interface"""
        # Apply a dark theme to the entire application
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #212121;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #424242;
                color: #FFFFFF;
                border: 1px solid #616161;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: #616161;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #424242;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #FF9800;
                border: 1px solid #FF9800;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QComboBox {
                background-color: #424242;
                color: #FFFFFF;
                border: 1px solid #616161;
                border-radius: 4px;
                padding: 5px;
            }
            QGroupBox {
                border: 1px solid #616161;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
            QScrollArea {
                border: none;
                background-color: #212121;
            }
        """)

        # Title section (compact)
        title_layout = QHBoxLayout()
        
        # Add logo
        logo_label = QLabel()
        logo_path = os.path.join(self.base_path, "samples", "Groove_Builders_Logo.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            # Scale logo to reasonable size (40px height)
            logo_pixmap = logo_pixmap.scaledToHeight(40, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignLeft)
            title_layout.addWidget(logo_label)
            title_layout.addSpacing(10)  # Add some space between logo and title
        
        title_label = QLabel("Amadinda Trainer")
        title_label.setAlignment(Qt.AlignLeft)
        title_label.setFont(QFont('Arial', 18, QFont.Bold))
        title_layout.addWidget(title_label)

        # Status indicator for pattern validity
        self.status_indicator = StatusIndicator()
        status_label = QLabel("Pattern Status:")
        status_layout = QHBoxLayout()
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_indicator)
        status_layout.addStretch()

        title_layout.addLayout(status_layout)
        
        # Add About button
        about_btn = QPushButton("About Amadinda")
        about_btn.clicked.connect(self.show_about_dialog)
        title_layout.addWidget(about_btn)
        
        # Add Load Pattern button
        load_pattern_btn = QPushButton("Load Traditional Pattern")
        load_pattern_btn.clicked.connect(self.show_pattern_dialog)
        title_layout.addWidget(load_pattern_btn)

        # Add title to main layout
        self.main_layout.addLayout(title_layout)
        # Top controls layout
        top_controls = QHBoxLayout()

        # Control sections arranged horizontally to save vertical space

        # Transport controls (play, stop, reset)
        transport_group = QWidget()
        transport_layout = QHBoxLayout(transport_group)
        transport_layout.setContentsMargins(0, 0, 0, 0)

        self.play_button = QPushButton(PLAY_SYMBOL)
        self.play_button.setFont(QFont('Arial', 16))
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setFixedSize(QSize(50, 40))
        transport_layout.addWidget(self.play_button)

        self.reset_button = QPushButton(RESET_SYMBOL)
        self.reset_button.setFont(QFont('Arial', 16))
        self.reset_button.clicked.connect(self.reset_patterns)
        self.reset_button.setFixedSize(QSize(50, 40))
        transport_layout.addWidget(self.reset_button)

        top_controls.addWidget(transport_group)

        # Tempo control
        tempo_group = QWidget()
        tempo_layout = QHBoxLayout(tempo_group)
        tempo_layout.setContentsMargins(0, 0, 0, 0)

        tempo_label = QLabel("Tempo:")
        tempo_layout.addWidget(tempo_label)

        self.tempo_slider = QSlider(Qt.Horizontal)
        self.tempo_slider.setMinimum(60)
        self.tempo_slider.setMaximum(180)
        self.tempo_slider.setValue(DEFAULT_TEMPO)
        self.tempo_slider.setFixedWidth(100)
        self.tempo_slider.valueChanged.connect(self.update_tempo)
        tempo_layout.addWidget(self.tempo_slider)

        self.tempo_display = QLabel(f"{DEFAULT_TEMPO}")
        tempo_layout.addWidget(self.tempo_display)

        top_controls.addWidget(tempo_group)



        # Display options
        options_group = QWidget()
        options_layout = QHBoxLayout(options_group)
        options_layout.setContentsMargins(0, 0, 0, 0)

        self.note_names_checkbox = QCheckBox("Note Names")
        self.note_names_checkbox.toggled.connect(self.toggle_note_names)
        options_layout.addWidget(self.note_names_checkbox)

        self.octave_plus_checkbox = QCheckBox("Octave +")
        self.octave_plus_checkbox.setChecked(True)  # Set to checked by default
        self.octave_plus_checkbox.toggled.connect(self.toggle_octave_plus)
        options_layout.addWidget(self.octave_plus_checkbox)

        self.omukoonezi_checkbox = QCheckBox("Omukoonezi")
        self.omukoonezi_checkbox.toggled.connect(self.toggle_omukoonezi)
        options_layout.addWidget(self.omukoonezi_checkbox)

        self.countoff_checkbox = QCheckBox("Count-off")
        self.countoff_checkbox.toggled.connect(self.toggle_countoff)
        options_layout.addWidget(self.countoff_checkbox)

        self.metronome_checkbox = QCheckBox("Enable Metronome")
        self.metronome_checkbox.setChecked(False)
        self.metronome_checkbox.toggled.connect(self.on_metronome_toggled)
        options_layout.addWidget(self.metronome_checkbox)

        # Pattern size control
        pattern_size_label = QLabel("Pattern Size:")
        options_layout.addWidget(pattern_size_label)
        
        self.pattern_size_button = QPushButton("6 → 12")
        self.pattern_size_button.setToolTip("Toggle between 6 and 12 beats per player")
        self.pattern_size_button.clicked.connect(self.toggle_pattern_size)
        # Set initial button text based on current pattern length
        if self.pattern_length == 12:
            self.pattern_size_button.setText("12 → 6")
        options_layout.addWidget(self.pattern_size_button)
        
        # Pattern validation mode
        self.strict_rules_checkbox = QCheckBox("Strict Rules")
        self.strict_rules_checkbox.setToolTip("Enable strict Kubik rules (some traditional pieces may break these)")
        self.strict_rules_checkbox.setChecked(False)  # Default to relaxed
        self.strict_rules_checkbox.toggled.connect(self.toggle_strict_rules)
        options_layout.addWidget(self.strict_rules_checkbox)

        top_controls.addWidget(options_group)

        # Add stretching space to right-align the key selection
        top_controls.addStretch(1)

        # Note selection - right aligned
        note_selection = QWidget()
        note_layout = QHBoxLayout(note_selection)
        note_layout.setContentsMargins(0, 0, 0, 0)

        note_layout.addWidget(QLabel("Select Note:"))

        self.note_buttons = {}
        self.note_group = QButtonGroup()
        self.note_group.setExclusive(True)

        for i, note in enumerate(PENTATONIC_NOTES):
            number = NOTE_TO_NUMBER[note]
            display_text = note if self.use_note_names else number
            button = QPushButton(display_text)
            button.setFixedSize(QSize(40, 40))
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.clicked.connect(lambda checked, n=note: self.select_note(n))
            note_layout.addWidget(button)
            self.note_buttons[note] = button
            self.note_group.addButton(button)

        # Select first note by default
        self.note_buttons['C'].setChecked(True)

        top_controls.addWidget(note_selection)

        # Add top controls to main layout
        self.main_layout.addLayout(top_controls)
        # Create a scroll area for the pattern editor
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Container for the pattern
        pattern_container = QWidget()
        pattern_layout = QVBoxLayout(pattern_container)
        pattern_layout.setSpacing(10)

        # Player labels with tooltips
        player_a_label = QLabel("Player A (Omunazi)")
        player_a_label.setFont(QFont('Arial', 12, QFont.Bold))
        player_a_label.setAlignment(Qt.AlignLeft)
        player_a_label.setToolTip("Player A (Omunazi) - Plays the main theme or okunaga")
        
        # Player B label needs to be directly above orange boxes - adjusted in grid layout
        player_b_label = QLabel("Player B (Omwawuzi)")
        player_b_label.setFont(QFont('Arial', 12, QFont.Bold))
        player_b_label.setAlignment(Qt.AlignLeft)  # Left-aligned to match player A
        player_b_label.setToolTip("Player B (Omwawuzi) - Plays the second part or okwawula")

        # LED row
        led_container = QWidget()
        led_layout = QHBoxLayout(led_container)
        led_layout.setContentsMargins(0, 0, 0, 0)
        led_layout.setSpacing(15)  # Same spacing as cells

        # Beat numbers and LEDs (centered over each cell)
        led_header_row = QHBoxLayout()
        led_header_row.setContentsMargins(0, 0, 0, 0)
        led_header_row.setSpacing(0)

        # LED label removed - not useful
        led_header_row.addStretch(1)

        pattern_layout.addLayout(led_header_row)

        # Clear existing LEDs
        self.leds = []

        # Create the main grid for both players and LEDs
        pattern_grid = QGridLayout()
        pattern_grid.setSpacing(15)  # Consistent spacing
        
        # Add player A label in the grid - spanning full row, left aligned
        pattern_grid.addWidget(player_a_label, 0, 0, 1, 2, Qt.AlignLeft)
        
        # Create beat number labels for first row (beats 1-6)
        for i in range(6 * 2):  # Always 6 beats per row
            beat_num = (i // 2) + 1
            if i % 2 == 0:  # Player A beats
                beat_label = QLabel(f"{beat_num}")
                beat_label.setAlignment(Qt.AlignCenter)
                pattern_grid.addWidget(beat_label, 1, i)

        # Create LEDs under the beat numbers for first row
        for i in range(6 * 2):
            led = SequencerLED(i)
            self.leds.append(led)
            pattern_grid.addWidget(led, 2, i, Qt.AlignCenter)

        # Player A cells for first row (beats 1-6)
        self.tubs_cells_a = []
        for i in range(6):  # First 6 cells
            cell = TUBSCell(i, 'a')
            cell.clicked.connect(lambda checked, pos=i, player='a': self.cell_clicked(pos, player))
            self.tubs_cells_a.append(cell)
            pattern_grid.addWidget(cell, 3, i*2)  # Even positions for Player A
        
        # Add player B label in the grid above the B cells - left aligned
        pattern_grid.addWidget(player_b_label, 4, 1, 1, 2, Qt.AlignLeft)  # Place left-aligned next to B cells

        # Player B cells for first row (beats 1-6)
        self.tubs_cells_b = []
        for i in range(6):  # First 6 cells
            cell = TUBSCell(i, 'b')
            cell.clicked.connect(lambda checked, pos=i, player='b': self.cell_clicked(pos, player))
            self.tubs_cells_b.append(cell)
            pattern_grid.addWidget(cell, 5, i*2+1)  # Odd positions for Player B, offset by 1

        # If pattern length is 12, add second row
        if self.pattern_length == 12:
            # Create beat number labels for second row (beats 7-12)
            for i in range(6 * 2):  # 6 more beats
                beat_num = (i // 2) + 7  # Beats 7-12
                if i % 2 == 0:  # Player A beats
                    beat_label = QLabel(f"{beat_num}")
                    beat_label.setAlignment(Qt.AlignCenter)
                    pattern_grid.addWidget(beat_label, 6, i)

            # Create LEDs under the beat numbers for second row
            for i in range(6 * 2):
                led = SequencerLED(i + 12)  # Offset by 12 for second row
                self.leds.append(led)
                pattern_grid.addWidget(led, 7, i, Qt.AlignCenter)

            # Player A cells for second row (beats 7-12)
            for i in range(6, 12):  # Second 6 cells
                cell = TUBSCell(i, 'a')
                cell.clicked.connect(lambda checked, pos=i, player='a': self.cell_clicked(pos, player))
                self.tubs_cells_a.append(cell)
                pattern_grid.addWidget(cell, 8, (i-6)*2)  # Even positions for Player A

            # Player B cells for second row (beats 7-12)
            for i in range(6, 12):  # Second 6 cells
                cell = TUBSCell(i, 'b')
                cell.clicked.connect(lambda checked, pos=i, player='b': self.cell_clicked(pos, player))
                self.tubs_cells_b.append(cell)
                pattern_grid.addWidget(cell, 9, (i-6)*2+1)  # Odd positions for Player B, offset by 1

        # Add the grid to the pattern layout
        pattern_layout.addLayout(pattern_grid)
        pattern_layout.addStretch(1)

        # Add the pattern container to the scroll area
        scroll_area.setWidget(pattern_container)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(scroll_area, 3)

        # Bottom area for keys and player info - replaced with compact bottom area
        bottom_area = QHBoxLayout()

        # Amadinda keys - left side
        keys_group = QWidget()
        keys_layout = QVBoxLayout(keys_group)

        keys_label = QLabel("Amadinda Keys:")
        keys_label.setAlignment(Qt.AlignCenter)
        keys_layout.addWidget(keys_label)

        keys_row = QHBoxLayout()
        keys_row.setAlignment(Qt.AlignCenter)
        self.key_buttons = {}

        for note in PENTATONIC_NOTES:
            # Create a key button with the current display mode
            key = AmadindaKey(note, PRIMARY_OCTAVE, self.use_note_names)
            key.clicked.connect(lambda checked, n=note: self.play_note(n))
            keys_row.addWidget(key)
            self.key_buttons[note] = key

        keys_layout.addLayout(keys_row)
        bottom_area.addWidget(keys_group)

        # Volume control button - center
        volume_group = QWidget()
        volume_layout = QVBoxLayout(volume_group)
        
        volume_label = QLabel("Mixer")
        volume_label.setAlignment(Qt.AlignCenter)
        volume_layout.addWidget(volume_label)
        
        # Create a large mixer button with custom SVG icon
        self.volume_button = QPushButton()
        self.volume_button.setFixedSize(QSize(80, 80))
        self.volume_button.setToolTip("Click to open mixer controls")
        self.volume_button.clicked.connect(self.show_volume_controls)
        
        # Load and set the custom SVG icon
        icon_path = os.path.join(self.base_path, "docs", "Paomedia_small-n-flat_mixer.svg")
        if os.path.exists(icon_path):
            self.volume_button.setIcon(QIcon(icon_path))
            self.volume_button.setIconSize(QSize(50, 50))
        else:
            # Fallback to text if icon not found
            self.volume_button.setText("🔊")
            self.volume_button.setFont(QFont('Arial', 24))
        
        self.volume_button.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: white;
                border: 2px solid #333333;
                border-radius: 40px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
            }
            QPushButton:pressed {
                background-color: #666666;
            }
        """)
        
        volume_layout.addWidget(self.volume_button, alignment=Qt.AlignCenter)
        bottom_area.addWidget(volume_group)

        # Keyboard help info - simplified
        keyboard_help = QLabel(
            "Keyboard: Select cell + press 1-5 for notes, arrows to navigate.\n"
            "Some patterns shown in amber are not used in traditional Kiganda music."
        )
        keyboard_help.setAlignment(Qt.AlignCenter)
        bottom_area.addWidget(keyboard_help)

        # Add bottom area to main layout
        self.main_layout.addLayout(bottom_area)

        # Set up keyboard focus handling for TUBS cells
        self.setFocusPolicy(Qt.StrongFocus)

        # Apply initial volumes
        self.update_metronome_volume(20)  # Default 20%
        self.update_overall_volume(80)  # Default 80%
        self.update_main_volume(100)  # Default 100%
        self.update_upper_octave_volume(70)  # Default 70%
        self.update_omukoonezi_volume(70)  # Default 70%
    def toggle_pattern_size(self):
        """Toggle between 6 and 12 beats per player"""
        # Stop playback if running
        if self.is_playing:
            self.toggle_playback()
        
        if self.pattern_length == 6:
            self.pattern_length = 12
            self.pattern_size_button.setText("12 → 6")
        else:
            self.pattern_length = 6
            self.pattern_size_button.setText("6 → 12")
        
        # Create new empty patterns with the new length
        self.current_pattern_a = self.create_empty_pattern()
        self.current_pattern_b = self.create_empty_pattern()
        
        # Recreate the UI with new pattern length
        self.recreate_ui()

    def toggle_strict_rules(self, checked):
        """Toggle between strict and relaxed compositional rules"""
        global PROHIBITED_PATTERNS
        
        # Update the prohibited patterns list based on strict mode
        if checked:
            # Strict mode - include all Kubik rules
            PROHIBITED_PATTERNS = [
                "111", "222", "333", "444", "555",  # Three identical notes
                "121", "232", "343", "454",  # Adjacent notes around a central note
                "151", "212", "323", "434", "545",  # Adjacent notes around a central note (alt pattern)
                "112", "334", # Certain rising patterns
                "115", "332", "443", "554",  # Certain falling patterns
                "155", "544",  # Certain patterns with repeated notes
                "123", "234", "345", "451", "512"   # Rising scalar patterns
            ]
        else:
            # Relaxed mode - only the most basic rules
            PROHIBITED_PATTERNS = [
                "111", "222", "333", "444", "555",  # Three identical notes
            ]
        
        # Recheck current pattern validity
        self.check_pattern_validity()

    def select_note(self, note):
        """Select the current note to insert into TUBS cells"""
        self.current_note_selection = note

    def cell_clicked(self, position, player):
        """Handle clicking on a TUBS cell"""
        # Get the appropriate cells list and pattern based on player
        if player == 'a':
            cells = self.tubs_cells_a
            pattern = self.current_pattern_a
        else:
            cells = self.tubs_cells_b
            pattern = self.current_pattern_b

        # Set focus to this cell for keyboard input
        if self.current_focus_cell:
            self.current_focus_cell.set_focused(False)

        cell = cells[position]
        cell.set_focused(True)
        self.current_focus_cell = cell

        # Toggle note or set new note
        display_text = self.get_display_text(self.current_note_selection)

        previous_note = cell.get_note()
        if cell.get_note() == display_text:
            # If same note is already there, remove it
            cell.set_note(None)
            pattern[position] = None
        else:
            # Set the currently selected note
            cell.set_note(display_text)
            pattern[position] = self.current_note_selection
            
            # Play the note
            self.play_note(self.current_note_selection)

        # Update the reference to the pattern
        if player == 'a':
            self.current_pattern_a = pattern
        else:
            self.current_pattern_b = pattern

        # Check pattern validity after any change
        self.check_pattern_validity()

    def get_display_text(self, note):
        """Get the text to display in a cell based on current display mode"""
        if self.use_note_names:
            return note
        else:
            return NOTE_TO_NUMBER[note]

    def toggle_note_names(self, checked):
        """Toggle between note names and numbers in the grid"""
        self.use_note_names = checked

        # Update note buttons labels
        for note, button in self.note_buttons.items():
            if checked:
                button.setText(f"{note}")
            else:
                button.setText(f"{NOTE_TO_NUMBER[note]}")

        # Update amadinda key labels
        for note, key in self.key_buttons.items():
            key.update_display(checked)

        # Update all cells
        self.update_all_cell_display()

    def update_all_cell_display(self):
        """Update the display text for all cells based on the current mode"""
        # Player A cells
        for i, note in enumerate(self.current_pattern_a):
            if note:
                self.tubs_cells_a[i].set_note(self.get_display_text(note))

        # Player B cells
        for i, note in enumerate(self.current_pattern_b):
            if note:
                self.tubs_cells_b[i].set_note(self.get_display_text(note))

    def toggle_octave_plus(self, checked):
        """Toggle the octave+ state"""
        self.octave_plus = checked

    def toggle_omukoonezi(self, checked):
        """Toggle the Omukoonezi mode"""
        self.omukoonezi_mode = checked

    def update_metronome_volume(self, value):
        """Update metronome volume"""
        self.metronome_volume = value / 100.0 * 0.4  # Scale down the volume by 40% of max

        # Update volume of metronome sample if loaded
        metronome_filename = "Highmetronome.flac"
        if metronome_filename in self.samples:
            self.samples[metronome_filename].set_volume(self.metronome_volume)

    def update_overall_volume(self, value):
        """Update overall volume (master volume)"""
        self.overall_volume = value / 100.0
        print(f"Overall volume set to {value}%")

    def update_main_volume(self, value):
        """Update main volume"""
        self.main_volume = value / 100.0
        print(f"Main volume set to {value}%")



    def update_upper_octave_volume(self, value):
        """Update upper octave volume"""
        self.upper_octave_volume = value / 100.0
        print(f"Upper octave volume set to {value}%")

    def update_omukoonezi_volume(self, value):
        """Update omukoonezi volume"""
        self.omukoonezi_volume = value / 100.0
        print(f"Omukoonezi volume set to {value}%")

    def show_volume_controls(self):
        """Show the volume control dialog"""
        print("Opening mixer dialog...")
        if not hasattr(self, 'volume_dialog') or self.volume_dialog is None:
            print("Creating new volume dialog...")
            self.volume_dialog = VolumeControlDialog(self)
        self.volume_dialog.show()
        self.volume_dialog.raise_()
        self.volume_dialog.activateWindow()
        print("Mixer dialog should now be visible")

    def update_tempo(self, value):
        """Update the tempo display and internal state"""
        self.tempo = value
        self.tempo_display.setText(f"{value}")

    def recreate_ui(self):
        """Recreate the UI with the current pattern length"""
        # Clear the LED list before recreating the UI
        self.leds = []

        # First clear everything
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Rebuild the interface
        self.init_ui()

    def cleanup_none_channels(self):
        """Remove None channels from currently_playing_samples dictionary"""
        none_keys = [key for key, channel in self.currently_playing_samples.items() if channel is None]
        for key in none_keys:
            del self.currently_playing_samples[key]

    def play_note(self, note, octave=None):
        """Play a note with options for octave selection"""
        # Clean up any None channels first
        self.cleanup_none_channels()
        
        # If octave is specified, use it, otherwise use PRIMARY_OCTAVE
        use_octave = octave if octave is not None else PRIMARY_OCTAVE

        # Format for the actual sample naming convention with "Mallet "
        primary_sample = f"Mallet {note}{use_octave}.wav"

        # Stop any currently playing instance of this sample
        if primary_sample in self.currently_playing_samples:
            channel = self.currently_playing_samples[primary_sample]
            if channel is not None:
                channel.stop()
            # Remove the channel from tracking since it's been stopped
            del self.currently_playing_samples[primary_sample]

        # If the primary sample exists, play it
        if primary_sample in self.samples:
            print(f"Playing sample: {primary_sample}")
            try:
                # Set main volume with overall volume blend (for octave 2 notes)
                main_volume = self.main_volume * self.overall_volume
                self.samples[primary_sample].set_volume(main_volume)
                channel = self.samples[primary_sample].play()
                self.currently_playing_samples[primary_sample] = channel
                print(f"Successfully started playback of: {primary_sample}")
            except Exception as e:
                print(f"Error playing sample {primary_sample}: {e}")

            # Play octave above if enabled (and only for default octave)
            if self.octave_plus and octave is None:
                upper_sample = f"Mallet {note}{PRIMARY_OCTAVE+1}.wav"  # This is octave 3
                if upper_sample in self.samples:
                    # Stop any currently playing instance of the upper octave sample
                    if upper_sample in self.currently_playing_samples:
                        upper_channel = self.currently_playing_samples[upper_sample]
                        if upper_channel is not None:
                            upper_channel.stop()
                        # Remove the channel from tracking since it's been stopped
                        del self.currently_playing_samples[upper_sample]

                    # Set upper octave volume with overall volume blend (for octave 3 notes)
                    upper_volume = self.upper_octave_volume * self.overall_volume
                    self.samples[upper_sample].set_volume(upper_volume)
                    channel = self.samples[upper_sample].play()
                    self.currently_playing_samples[upper_sample] = channel

            # Omukoonezi mode: play C and D notes at octave 4 (highest notes)
            if self.omukoonezi_mode and octave is None and note in ['C', 'D']:
                high_sample = f"Mallet {note}4.wav"  # This is octave 4 (C4, D4)
                if high_sample in self.samples:
                    # Stop any currently playing instance
                    if high_sample in self.currently_playing_samples:
                        high_channel = self.currently_playing_samples[high_sample]
                        if high_channel is not None:
                            high_channel.stop()
                        # Remove the channel from tracking since it's been stopped
                        del self.currently_playing_samples[high_sample]

                    # Set omukoonezi volume with overall volume blend (for octave 4 notes)
                    omukoonezi_volume = self.omukoonezi_volume * self.overall_volume
                    self.samples[high_sample].set_volume(omukoonezi_volume)
                    channel = self.samples[high_sample].play()
                    self.currently_playing_samples[high_sample] = channel
        else:
            print(f"Sample not found: {primary_sample}")
            print(f"Available samples: {list(self.samples.keys())}")

    def toggle_playback(self):
        """Start or stop pattern playback"""
        if self.is_playing:
            self.is_playing = False
            self.play_button.setText(PLAY_SYMBOL)
            # Thread will notice is_playing is False and terminate
        else:
            self.is_playing = True
            self.play_button.setText(STOP_SYMBOL)
            self.play_thread = threading.Thread(target=self.playback_thread)
            self.play_thread.daemon = True
            self.play_thread.start()

    def playback_thread(self):
        """Thread function for pattern playback"""
        # Get metronome sample
        metronome_sample = self.samples.get("Highmetronome.flac")

        if metronome_sample:
            metronome_sample.set_volume(self.metronome_volume)

        # Calculate time per beat based on tempo
        beat_time = 60.0 / self.tempo

        if self.countoff_enabled:
            print(">>> Count-off triggered")
            # 2 clicks (beats 1 and 3), then 4 clicks (beats 1-4)
            for i in range(6):
                if (i < 4 and i % 2 == 0) or i >= 4:
                    # Always play metronome for count-off, regardless of metronome toggle
                    if metronome_sample:
                        metronome_sample.play()
                # Wait a full beat before next count
                time.sleep(beat_time)

        position = 0
        current_player = 'a'  # Start with player A
        led_position = 0  # Start with the first LED

        while self.is_playing:
            # Highlight the current position on the transport bar
            self.signaler.update_position.emit(led_position)

            # Play metronome to mark the beat (only if metronome is enabled)
            if self.metronome_enabled and metronome_sample:
                metronome_sample.play()

            if current_player == 'a':
                # Play note for Player A
                note_a = self.current_pattern_a[position]
                if note_a:
                    self.play_note(note_a)

                # Switch to player B for next turn
                current_player = 'b'
                led_position += 1
            else:
                # Play note for Player B
                note_b = self.current_pattern_b[position]
                if note_b:
                    self.play_note(note_b)

                # Switch back to player A and advance position
                current_player = 'a'
                position = (position + 1) % self.pattern_length
                led_position = 2 * position  # Calculate LED position

            # Wait for next beat (half the time for interlocking patterns)
            time.sleep(beat_time / 2)

        # Cleanup
        self.signaler.update_position.emit(-1)
        self.signaler.playback_finished.emit()

    def highlight_position(self, position):
        """Highlight the current position in playback"""
        # Reset all LEDs
        for led in self.leds:
            led.setActive(False)

        # Light up the current LED if in valid range
        if 0 <= position < len(self.leds):
            self.leds[position].setActive(True)

        # Figure out which player's cell to highlight
        # Even positions (0, 2, 4...) are player A, odd positions (1, 3, 5...) are player B
        is_player_a = (position % 2 == 0)
        cell_position = position // 2  # Convert LED position to cell position

        # Reset all cell highlighting
        for cell in self.tubs_cells_a:
            cell.setChecked(False)
        for cell in self.tubs_cells_b:
            cell.setChecked(False)

        # Highlight appropriate cell based on position
        if is_player_a and cell_position < len(self.tubs_cells_a):
            self.tubs_cells_a[cell_position].setChecked(True)
        elif not is_player_a and cell_position < len(self.tubs_cells_b):
            self.tubs_cells_b[cell_position].setChecked(True)

    def playback_complete(self):
        """Called when playback thread completes"""
        self.play_button.setText(PLAY_SYMBOL)
        self.is_playing = False

    def reset_patterns(self):
        """Reset both patterns"""
        # Stop playback if running
        if self.is_playing:
            self.toggle_playback()

        # Clear pattern arrays
        self.current_pattern_a = self.create_empty_pattern()
        self.current_pattern_b = self.create_empty_pattern()

        # Clear TUBS cells
        for cell in self.tubs_cells_a:
            cell.set_note(None)
            cell.setChecked(False)
            cell.set_problematic(False)

        for cell in self.tubs_cells_b:
            cell.set_note(None)
            cell.setChecked(False)
            cell.set_problematic(False)

        # Reset position indicators
        for led in self.leds:
            led.setActive(False)

        # Reset pattern status
        self.status_indicator.set_status("good", "Pattern is empty")

    def keyPressEvent(self, event):
        """Handle keyboard input for note entry"""
        key = event.key()

        # Global shortcuts (work even without cell focus)
        if key == Qt.Key_M:
            # Toggle metronome
            self.metronome_checkbox.setChecked(not self.metronome_checkbox.isChecked())
            return
        elif key == Qt.Key_C:
            # Toggle count-off
            self.countoff_checkbox.setChecked(not self.countoff_checkbox.isChecked())
            return
        elif key == Qt.Key_Space:
            # Toggle playback - always handle spacebar for playback
            self.toggle_playback()
            return  # Always return to prevent cell from processing spacebar
        elif key == Qt.Key_Left or key == Qt.Key_Right:
            # Step through playback position (if not playing)
            if not self.is_playing:
                if key == Qt.Key_Left:
                    # Move playback position left
                    if self.current_position > 0:
                        self.current_position -= 1
                    else:
                        self.current_position = self.pattern_length - 1
                else:  # Right arrow
                    # Move playback position right
                    if self.current_position < self.pattern_length - 1:
                        self.current_position += 1
                    else:
                        self.current_position = 0
                
                # Update LED display
                led_position = self.current_position * 2  # Convert to LED position
                self.highlight_position(led_position)
                return

        # Only process cell-specific shortcuts if a cell is focused
        if not self.current_focus_cell:
            return super().keyPressEvent(event)

        # Delete or Backspace - Clear current cell
        if key == Qt.Key_Delete or key == Qt.Key_Backspace:
            # Find which list contains the current cell
            player = 'a'
            position = -1
            for i, cell in enumerate(self.tubs_cells_a):
                if cell == self.current_focus_cell:
                    position = i
                    break

            if position == -1:
                player = 'b'
                for i, cell in enumerate(self.tubs_cells_b):
                    if cell == self.current_focus_cell:
                        position = i
                        break

            # Clear the cell
            if position != -1:
                self.current_focus_cell.set_note(None)
                if player == 'a':
                    self.current_pattern_a[position] = None
                else:
                    self.current_pattern_b[position] = None
                
                # Check pattern validity after clearing
                self.check_pattern_validity()
            return

        # Number keys 1-5 for note entry
        if Qt.Key_1 <= key <= Qt.Key_5:
            number = str(key - Qt.Key_0)  # Convert key code to actual number

            if number in NUMBER_TO_NOTE:
                note = NUMBER_TO_NOTE[number]
                self.current_note_selection = note

                # Update button states to reflect selection
                for n, button in self.note_buttons.items():
                    button.setChecked(n == note)

                # Find which list contains the current cell
                player = 'a'
                position = -1
                for i, cell in enumerate(self.tubs_cells_a):
                    if cell == self.current_focus_cell:
                        position = i
                        break

                if position == -1:
                    player = 'b'
                    for i, cell in enumerate(self.tubs_cells_b):
                        if cell == self.current_focus_cell:
                            position = i
                            break

                # Call cell_clicked to set the note and play it
                if position != -1:
                    self.cell_clicked(position, player)

                    # Move focus to the next cell (if it exists)
                    if player == 'a' and position < len(self.tubs_cells_a) - 1:
                        self.current_focus_cell.set_focused(False)
                        self.current_focus_cell = self.tubs_cells_a[position + 1]
                        self.current_focus_cell.set_focused(True)
                    elif player == 'b' and position < len(self.tubs_cells_b) - 1:
                        self.current_focus_cell.set_focused(False)
                        self.current_focus_cell = self.tubs_cells_b[position + 1]
                        self.current_focus_cell.set_focused(True)

        # Arrow keys for navigation (only when not stepping through playback)
        elif key == Qt.Key_Left:
            # Move to the previous cell
            player = 'a'
            position = -1

            for i, cell in enumerate(self.tubs_cells_a):
                if cell == self.current_focus_cell:
                    position = i
                    break

            if position == -1:
                player = 'b'
                for i, cell in enumerate(self.tubs_cells_b):
                    if cell == self.current_focus_cell:
                        position = i
                        break

            if position > 0:
                self.current_focus_cell.set_focused(False)

                if player == 'a':
                    self.current_focus_cell = self.tubs_cells_a[position - 1]
                else:
                    self.current_focus_cell = self.tubs_cells_b[position - 1]

                self.current_focus_cell.set_focused(True)

        elif key == Qt.Key_Right:
            # Move to the next cell
            player = 'a'
            position = -1

            for i, cell in enumerate(self.tubs_cells_a):
                if cell == self.current_focus_cell:
                    position = i
                    break

            if position == -1:
                player = 'b'
                for i, cell in enumerate(self.tubs_cells_b):
                    if cell == self.current_focus_cell:
                        position = i
                        break

            if position >= 0 and position < (self.pattern_length - 1):
                self.current_focus_cell.set_focused(False)

                if player == 'a':
                    self.current_focus_cell = self.tubs_cells_a[position + 1]
                else:
                    self.current_focus_cell = self.tubs_cells_b[position + 1]

                self.current_focus_cell.set_focused(True)

        elif key == Qt.Key_Up:
            # Move from player B to player A
            position = -1

            for i, cell in enumerate(self.tubs_cells_b):
                if cell == self.current_focus_cell:
                    position = i
                    break

            if position >= 0:
                self.current_focus_cell.set_focused(False)
                self.current_focus_cell = self.tubs_cells_a[position]
                self.current_focus_cell.set_focused(True)

        elif key == Qt.Key_Down:
            # Move from player A to player B
            position = -1

            for i, cell in enumerate(self.tubs_cells_a):
                if cell == self.current_focus_cell:
                    position = i
                    break

            if position >= 0:
                self.current_focus_cell.set_focused(False)
                self.current_focus_cell = self.tubs_cells_b[position]
                self.current_focus_cell.set_focused(True)

        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Handle window close event"""
        # Stop playback if running
        if self.is_playing:
            self.is_playing = False
            if self.play_thread:
                self.play_thread.join(1.0)

        # Call parent close event
        super().closeEvent(event)

    def toggle_countoff(self, checked):
        """Enable or disable the count-off"""
        self.countoff_enabled = checked

    def on_metronome_toggled(self, checked):
        """Enable or disable metronome"""
        self.metronome_enabled = checked


class VolumeControlDialog(QDialog):
    """Dialog for controlling various volume settings"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Mixer")
        self.setModal(False)  # Make non-modal so it doesn't block playback
        self.setFixedSize(450, 400)  # Larger size to make sliders more visible
        
        # Initialize volume variables from parent if available
        if parent:
            self.overall_volume = int(parent.overall_volume * 100)
            self.main_volume = int(parent.main_volume * 100)
            self.upper_octave_volume = int(parent.upper_octave_volume * 100)
            self.omukoonezi_volume = int(parent.omukoonezi_volume * 100)
            self.metronome_volume = int(parent.metronome_volume * 100)
        else:
            self.overall_volume = 70  # Default 70%
            self.main_volume = 80  # Default 80%
            self.upper_octave_volume = 70  # Default 70%
            self.omukoonezi_volume = 80  # Default 80%
            self.metronome_volume = 20  # Default 20%
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Reduce spacing to fit everything
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins
        
        # Set dialog style for better visibility
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #f0f0f0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #5c6bc0;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #45a049;
            }
        """)
        
        # Title
        title = QLabel("Mixer")
        title.setFont(QFont('Arial', 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Overall volume (master)
        overall_group = QGroupBox("Master Volume")
        overall_layout = QHBoxLayout(overall_group)
        
        self.overall_slider = QSlider(Qt.Horizontal)
        self.overall_slider.setMinimum(0)
        self.overall_slider.setMaximum(100)
        self.overall_slider.setValue(self.overall_volume)
        self.overall_slider.valueChanged.connect(self.update_overall_volume)
        self.overall_slider.setFixedHeight(35)
        
        self.overall_label = QLabel(f"{self.overall_volume}%")
        self.overall_label.setFixedWidth(60)
        self.overall_label.setFont(QFont('Arial', 12, QFont.Bold))
        
        overall_layout.addWidget(self.overall_slider)
        overall_layout.addWidget(self.overall_label)
        layout.addWidget(overall_group)
        
        # Main volume
        main_group = QGroupBox("Main Notes (C2-A2)")
        main_layout = QHBoxLayout(main_group)
        
        self.main_slider = QSlider(Qt.Horizontal)
        self.main_slider.setMinimum(0)
        self.main_slider.setMaximum(100)
        self.main_slider.setValue(self.main_volume)
        self.main_slider.valueChanged.connect(self.update_main_volume)
        self.main_slider.setFixedHeight(30)
        
        self.main_label = QLabel(f"{self.main_volume}%")
        self.main_label.setFixedWidth(60)
        
        main_layout.addWidget(self.main_slider)
        main_layout.addWidget(self.main_label)
        layout.addWidget(main_group)
        

        
        # Upper octave volume
        upper_octave_group = QGroupBox("Upper Octave (C3-A3)")
        upper_octave_layout = QHBoxLayout(upper_octave_group)
        
        self.upper_octave_slider = QSlider(Qt.Horizontal)
        self.upper_octave_slider.setMinimum(0)
        self.upper_octave_slider.setMaximum(100)
        self.upper_octave_slider.setValue(self.upper_octave_volume)
        self.upper_octave_slider.valueChanged.connect(self.update_upper_octave_volume)
        self.upper_octave_slider.setFixedHeight(30)
        
        self.upper_octave_label = QLabel(f"{self.upper_octave_volume}%")
        self.upper_octave_label.setFixedWidth(60)
        
        upper_octave_layout.addWidget(self.upper_octave_slider)
        upper_octave_layout.addWidget(self.upper_octave_label)
        layout.addWidget(upper_octave_group)
        
        # Omukoonezi volume
        omukoonezi_group = QGroupBox("Omukoonezi (C4-D4)")
        omukoonezi_layout = QHBoxLayout(omukoonezi_group)
        
        self.omukoonezi_slider = QSlider(Qt.Horizontal)
        self.omukoonezi_slider.setMinimum(0)
        self.omukoonezi_slider.setMaximum(100)
        self.omukoonezi_slider.setValue(self.omukoonezi_volume)
        self.omukoonezi_slider.valueChanged.connect(self.update_omukoonezi_volume)
        self.omukoonezi_slider.setFixedHeight(30)
        
        self.omukoonezi_label = QLabel(f"{self.omukoonezi_volume}%")
        self.omukoonezi_label.setFixedWidth(60)
        
        omukoonezi_layout.addWidget(self.omukoonezi_slider)
        omukoonezi_layout.addWidget(self.omukoonezi_label)
        layout.addWidget(omukoonezi_group)
        
        # Metronome volume
        metro_group = QGroupBox("Metronome")
        metro_layout = QHBoxLayout(metro_group)
        
        self.metro_slider = QSlider(Qt.Horizontal)
        self.metro_slider.setMinimum(0)
        self.metro_slider.setMaximum(100)
        self.metro_slider.setValue(self.metronome_volume)
        self.metro_slider.valueChanged.connect(self.update_metronome_volume)
        self.metro_slider.setFixedHeight(30)
        
        self.metro_label = QLabel(f"{self.metronome_volume}%")
        self.metro_label.setFixedWidth(60)
        
        metro_layout.addWidget(self.metro_slider)
        metro_layout.addWidget(self.metro_label)
        layout.addWidget(metro_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setFixedHeight(35)
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(35)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def update_overall_volume(self, value):
        print(f"Dialog: Overall volume changed to {value}%")
        self.overall_volume = value
        self.overall_label.setText(f"{value}%")
        if self.parent:
            self.parent.update_overall_volume(value)
            
    def update_main_volume(self, value):
        self.main_volume = value
        self.main_label.setText(f"{value}%")
        if self.parent:
            self.parent.update_main_volume(value)
            

            
    def update_upper_octave_volume(self, value):
        self.upper_octave_volume = value
        self.upper_octave_label.setText(f"{value}%")
        if self.parent:
            self.parent.update_upper_octave_volume(value)
            
    def update_omukoonezi_volume(self, value):
        self.omukoonezi_volume = value
        self.omukoonezi_label.setText(f"{value}%")
        if self.parent:
            self.parent.update_omukoonezi_volume(value)
            
    def update_metronome_volume(self, value):
        self.metronome_volume = value
        self.metro_label.setText(f"{value}%")
        if self.parent:
            self.parent.update_metronome_volume(value)
            
    def reset_to_defaults(self):
        self.overall_slider.setValue(80)
        self.main_slider.setValue(100)
        self.upper_octave_slider.setValue(70)
        self.omukoonezi_slider.setValue(70)
        self.metro_slider.setValue(20)
        
    def closeEvent(self, event):
        """Handle dialog close event"""
        self.hide()  # Hide instead of closing to prevent crashes
        event.ignore()  # Don't actually close the dialog


class AmadindaKey(QPushButton):
    """A custom button representing a single amadinda key"""
    def __init__(self, note, octave, use_note_names=False, parent=None):
        # Use numbered labels by default, note names only if specified
        display_text = note if use_note_names else NOTE_TO_NUMBER[note]
        super().__init__(display_text, parent)
        self.note = note
        self.octave = octave
        self.setMinimumSize(QSize(60, 80))  # Smaller, more compact keys
        self.setFont(QFont('Arial', 16, QFont.Bold))  # Larger font

        # Style the button like a wooden key
        if note in ['C', 'E', 'A']:  # Alternating colors
            self.setStyleSheet("""
                QPushButton {
                    background-color: #8B4513; /* SaddleBrown */
                    color: white;
                    border: 2px solid #654321;
                    border-radius: 5px;
                }
                QPushButton:pressed {
                    background-color: #654321;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #A0522D; /* Sienna */
                    color: white;
                    border: 2px solid #654321;
                    border-radius: 5px;
                }
                QPushButton:pressed {
                    background-color: #654321;
                }
            """)

    def update_display(self, use_note_names):
        """Update the button text based on display mode"""
        display_text = self.note if use_note_names else NOTE_TO_NUMBER[self.note]
        self.setText(display_text)

def main():
    print("Starting Amadinda Trainer...")
    print(f"Working directory: {os.getcwd()}")

    app = QApplication(sys.argv)

    # Set global tooltip styling
    app.setStyleSheet("""
        QToolTip {
            background-color: #FFFFD3;
            color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 4px;
            padding: 6px;
            font-size: 12px;
            max-width: 300px;
        }
    """)

    window = AmadindaTrainer()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
