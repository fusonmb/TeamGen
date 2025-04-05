import tkinter as tk
from gui import TeamBuilderGUI

if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap("frisbee-24.ico")
    app = TeamBuilderGUI(root)
    root.mainloop()
