import sys
import atexit
import select

if sys.platform.startswith('win'):
    import msvcrt
else:
    import tty
    import termios


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
    
    def get_dir_by_char(self, char: str) -> str | None:
        match char.lower():
            case 'a': return 'LEFT'
            case 'd': return 'RIGHT'
            case 's': return 'DOWN'
            case 'w': return 'UP'
            case ' ': return 'SPACE'
            case _: return None
    
    WIN_KEY_MAP = {
        'K': 'LEFT',
        'M': 'RIGHT',
        'P': 'DOWN',
        'H': 'UP',
    }
    UNIX_KEY_MAP = {
        '[D': 'LEFT',
        '[C': 'RIGHT',
        '[B': 'DOWN',
        '[A': 'UP',
    }
    
    def get_key(self):
        """Return LEFT/RIGHT/DOWN/UP or None"""
        last = None
        if sys.platform.startswith('win'):
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ('\x00', '\xe0'):
                    ch2 = msvcrt.getwch()
                    last = self.WIN_KEY_MAP.get(ch2, None)
                else:
                    last = self.get_dir_by_char(ch)
            return last
        else:
            while select.select([sys.stdin], [], [], 0)[0]:
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    ch2 = sys.stdin.read(2)
                    last = self.UNIX_KEY_MAP.get(ch2, None)
                else:
                    last = self.get_dir_by_char(ch)
            return last
            
