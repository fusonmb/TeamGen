import tkinter as tk
from gui import TeamBuilderGUI
import os
import sys



if __name__ == "__main__":

    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)
    
    root = tk.Tk()
    root.iconbitmap(resource_path("frisbee-24.ico"))
    app = TeamBuilderGUI(root)
    root.mainloop()
