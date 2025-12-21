import os
import sys

if os.name == "nt":  # Windows
    import msvcrt

    def get_key():
        return msvcrt.getch().decode("utf-8", errors="ignore")

else:  # Linux / macOS
    import tty
    import termios

    def get_key():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch
