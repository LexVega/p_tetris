import sys
import atexit
import select
from enum import Enum, auto


if sys.platform.startswith('win'):
    import msvcrt
else:
    import tty
    import termios


class Action(Enum):
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    SOFT_DROP = auto()
    HARD_DROP = auto()
    ROTATE = auto()

KEY_MAP = {
    # Windows scan codes
    'K': Action.MOVE_LEFT,
    'M': Action.MOVE_RIGHT,
    'P': Action.SOFT_DROP,
    'H': Action.ROTATE,
    
    # Unix escape sequences
    '[D': Action.MOVE_LEFT,
    '[C': Action.MOVE_RIGHT,
    '[B': Action.SOFT_DROP,
    '[A': Action.ROTATE,
    
    # WASD + Space
    'a': Action.MOVE_LEFT,
    'd': Action.MOVE_RIGHT,
    's': Action.SOFT_DROP,
    ' ': Action.HARD_DROP,
    'w': Action.ROTATE,
}

class Input:
    def __init__(self):
        """Put terminal into cbreak mode in Unix"""
        if not sys.platform.startswith('win'):
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
            atexit.register(self.restore)

    def restore(self):
        """Restore input mode on Unix"""
        if not sys.platform.startswith('win'):
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    
    def get_action(self) -> Action | None:
        """Return LEFT/RIGHT/DOWN/UP or None"""
        last = None
        if sys.platform.startswith('win'):
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ('\x00', '\xe0'):
                    ch2 = msvcrt.getwch()
                    last = KEY_MAP.get(ch2, None)
                else:
                    last = KEY_MAP.get(ch, None)
            return last
        else:
            while select.select([sys.stdin], [], [], 0)[0]:
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    ch2 = sys.stdin.read(2)
                    last = KEY_MAP.get(ch2, None)
                else:
                    last = KEY_MAP.get(ch, None)
            return last
            
