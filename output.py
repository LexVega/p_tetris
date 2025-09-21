import os
import sys


def clear_screen():
    """
    Clears the terminal screen in a cross-platform way.
    """
    if sys.platform.startswith('win'):
        os.system('cls')  # For Windows
    else:
        # For Linux, macOS, and other Unix-like systems, ANSI escape sequence
        print("\033[2J\033[H", end='')
        
