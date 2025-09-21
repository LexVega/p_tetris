import sys

class Colorizer:
    """Handles cross-platform terminal colorization."""
    
    def __init__(self):
        self.is_windows = sys.platform.startswith('win')
        # For simplicity, no colors in Windows just yet
        self.supports_color = not self.is_windows
        # TODO: more advanced approach to tell if windows terminal can run ASCII or not
    
    def color(self, color_code):
        """Return the color code if supported, else an empty string."""
        if self.supports_color:
            return color_code
        return ""
    
    @property
    def cyan(self):
        return self.color("\033[96m")
    
    @property
    def yellow(self):
        return self.color("\033[93m")
    
    @property
    def magenta(self):
        return self.color("\033[95m")
    
    @property
    def green(self):
        return self.color("\033[92m")
    
    @property
    def red(self):
        return self.color("\033[91m")
    
    @property
    def blue(self):
        return self.color("\033[94m")
    
    @property
    def orange(self):
        return self.color("\033[33m")
    
    @property
    def reset(self):
        return self.color("\033[0m")
