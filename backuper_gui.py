import pathlib
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askdirectory

from zeetoo import Backuper


def make_button(master, text, row=0, column=0, sticky='nwe', command=None):
    b = ttk.Button(master, text=text, command=command)
    b.grid(row=row, column=column, sticky=sticky)
    b.config(width=15)
    return b


def choose_dest(dest: tk.StringVar, bcp: Backuper):
    path = askdirectory()
    if path:
        bcp.destination = path
        dest.set(bcp.destination)


def changed_dest(dest: tk.StringVar, bcp: Backuper):
    path = dest.get()
    bcp.destination = path


def add_dir(tree: ttk.Treeview, bcp: Backuper):
    path = askdirectory()
    if path and str(pathlib.Path(path).resolve()) not in bcp.config['SOURCE']:
        path = bcp.add_source(path, 'd')
        tree.insert('', 'end', text=str(path) + '\\')


def add_tree(tree: ttk.Treeview, bcp: Backuper):
    path = askdirectory()
    if path and str(pathlib.Path(path).resolve()) not in bcp.config['SOURCE']:
        path = bcp.add_source(path, 'r')
        tree.insert('', 'end', text=str(path) + '\\*')


def add_ignored_file(tree: ttk.Treeview, bcp: Backuper):
    path = askdirectory()
    if path and str(pathlib.Path(path).resolve()) not in bcp.ignored:
        path = bcp.add_ignored(path)
        tree.insert('', 'end', text=str(path))


def add_ignored_dir(tree: ttk.Treeview, bcp: Backuper):
    path = askdirectory()
    if path and str(pathlib.Path(path).resolve()) not in bcp.ignored:
        path = bcp.add_ignored(path)
        tree.insert('', 'end', text=str(path) + '\\')


def remove_item(tree: ttk.Treeview, bcp: Backuper, pathtype: str):
    for item in tree.selection():
        path = str(pathlib.Path(tree.item(item)['text']).resolve())
        print(path)
        done = bcp.config.remove_option(pathtype, path)
        if done:
            tree.delete(item)


root = tk.Tk()
root.title('zootoo backuper')
tk.Grid.columnconfigure(root, 0, weight=1)
tk.Grid.rowconfigure(root, 1, weight=1)
dest_frame = tk.Frame(root)
dest_frame.grid(row=0, column=0, sticky='nwe')
tk.Label(dest_frame, text='Destination').grid(row=0, column=0, sticky='w')
dest_var = tk.StringVar()
dest_entry = tk.Entry(dest_frame, textvariable=dest_var)
dest_entry.grid(row=0, column=1, sticky='we')
choose = make_button(dest_frame, 'Choose', 0, 2, 'we',
                     command=lambda: choose_dest(dest_var, backuper))
tk.Grid.columnconfigure(dest_frame, 1, weight=1)
tk.Grid.rowconfigure(dest_frame, 0, weight=1)

source_frame = tk.Frame(root)
source_frame.grid(row=1, column=0, sticky='nwes')
source_label = tk.LabelFrame(source_frame, text='Source')
source_label.grid(row=0, column=0, sticky='nwes')
source = ttk.Treeview(source_label)
source.grid(row=0, column=0, sticky='nwse')
source['show'] = 'tree'
buttons_frame = tk.Frame(source_frame)
buttons_frame.grid(row=0, column=1, pady=7, sticky='nwse')
add_dir_butt = make_button(buttons_frame, 'Add Folder', 0, 1,
                           command=lambda: add_dir(source, backuper))
add_tree_burr = make_button(buttons_frame, 'Add Folder Tree', 1, 1,
                            command=lambda: add_tree(source, backuper))
remove_butt = make_button(
    buttons_frame, 'Remove Selected', 2, 1,
    command=lambda: remove_item(source, backuper, 'SOURCE')
)
tk.Grid.columnconfigure(source_frame, 0, weight=1)
tk.Grid.rowconfigure(source_frame, 0, weight=1)
tk.Grid.columnconfigure(source_label, 0, weight=1)
tk.Grid.rowconfigure(source_label, 0, weight=1)

ignored_frame = tk.Frame(root)
ignored_frame.grid(row=2, column=0, sticky='nwe')
ignored_label = tk.LabelFrame(ignored_frame, text='Ignored')
ignored_label.grid(row=0, column=0, sticky='nwes')
ignored = ttk.Treeview(ignored_label)
ignored['show'] = 'tree'
ignored.grid(row=0, column=0, sticky='nwse')
ignored.config(height=5)
buttons_frame = tk.Frame(ignored_frame)
buttons_frame.grid(row=0, column=1, pady=7, sticky='nwes')
ignore_file_butt = make_button(buttons_frame, 'Add File', 0, 1)
ignore_dir_butt = make_button(buttons_frame, 'Add Folder', 1, 1)
remignore_butt = make_button(
    buttons_frame, 'Remove Selected', 2, 1,
    command=lambda: remove_item(ignored, backuper, 'IGNORE')
)
tk.Grid.columnconfigure(ignored_frame, 0, weight=1)
tk.Grid.columnconfigure(ignored_label, 0, weight=1)

bottom_frame = tk.Frame(root)
bottom_frame.grid(row=3, column=0, sticky='nwes')
tk.Label(bottom_frame, text='Period').grid(row=0, column=0)
period_var = tk.StringVar()
period_box = ttk.Combobox(bottom_frame, textvariable=period_var)
period_box['values'] = ['DAILY', 'WEEKLY', 'MONTHLY']
period_box.grid(row=0, column=1)
period_box.config(width=11)
tk.Label(bottom_frame, text='Hour:').grid(row=0, column=2)
hour_var = tk.StringVar()
hour_box = ttk.Combobox(bottom_frame, textvariable=hour_var)
hour_box['values'] = [f'{x:0>2}' for x in range(1, 25)]
hour_box.grid(row=0, column=3)
hour_box.config(width=3)
tk.Label(bottom_frame, text='Min:').grid(row=0, column=4)
min_var = tk.StringVar()
min_box = ttk.Combobox(bottom_frame, textvariable=min_var)
min_box['values'] = [f'{x:0>2}' for x in range(0, 60, 5)]
min_box.grid(row=0, column=5)
min_box.config(width=3)
save = make_button(bottom_frame, 'Save Config', 0, 9)
load = make_button(bottom_frame, 'Load Config', 0, 8)
sched = make_button(bottom_frame, 'Schedule', 0, 6)
tk.Frame(bottom_frame).grid(row=0, column=7, sticky='we')
tk.Grid.columnconfigure(bottom_frame, 7, weight=1)
tk.Grid.rowconfigure(bottom_frame, 0, weight=1)

backuper = Backuper(pathlib.Path(__file__).resolve().with_name('config.ini'))
dest_var.set(backuper.destination)
for path, mode in backuper.config['SOURCE'].items():
    appendix = '\\' if mode == 'd' else '\\*' if mode == 'r' else ''
    source.insert('', 'end', text=path+appendix)
for path in backuper.ignored:
    appendix = '\\' if pathlib.Path(path).is_dir() else ''
    ignored.insert('', 'end', text=path+appendix)
period_var.set(backuper.config['BACKUP']['schedule'])
hour, minute = backuper.config['BACKUP']['starttime'].split(':')
hour_var.set(hour)
min_var.set(minute)

if __name__ == '__main__':
    root.mainloop()
