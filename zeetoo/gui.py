import importlib
import tkinter as tk
from tkinter import ttk
import pathlib

directory = pathlib.Path(__file__).resolve().parent
_modules = [
    f.stem for f in directory.glob('*.py') if not f.stem.startswith('_')
]
modules = {}
for name in _modules:
    try:
        module = importlib.import_module(name)
        gui = importlib.import_module('_gui.' + name + '_gui',)
        modules[name] = (module, gui)
    except ImportError as error:
        modules[name] = (None, error)


class App(ttk.Notebook):
    def __init__(self, master):
        super().__init__(master)
        self.master.title('zeetoo')
        for name, (module, gui) in modules.items():
            if name == 'gui':
                continue
            elif module:
                frame = gui.AppFrame(self)
            else:
                frame = ttk.Frame(self)
                tk.Label(
                    frame, text="This module is not available."
                ).pack(fill='both')
                tk.Label(
                    frame, text=f"Reason: {gui.args[0]}"
                ).pack(fill='x')
            self.add(frame, text=name)


def main(argv=None):
    root = tk.Tk()
    notebook = App(root)
    notebook.pack(fill='both', expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
