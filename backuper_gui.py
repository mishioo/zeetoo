import tkinter as tk
import tkinter.ttk as ttk


def make_button(master, text, row=0, column=0, sticky='nwe'):
    b = ttk.Button(master, text=text)
    b.grid(row=row, column=column, sticky=sticky)
    b.config(width=15)
    return b


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
choose = make_button(dest_frame, 'Choose', 0, 2, 'we')
tk.Grid.columnconfigure(dest_frame, 1, weight=1)
tk.Grid.rowconfigure(dest_frame, 0, weight=1)

source_frame = tk.Frame(root)
source_frame.grid(row=1, column=0, sticky='nwes')
source_label = tk.LabelFrame(source_frame, text='Source')
source_label.grid(row=0, column=0, sticky='nwes')
source = ttk.Treeview(source_label)
source.grid(row=0, column=0, sticky='nwse')
buttons_frame = tk.Frame(source_frame)
buttons_frame.grid(row=0, column=1, pady=7, sticky='nwse')
add = make_button(buttons_frame, 'Add Source', 0, 1)
remove = make_button(buttons_frame, 'Remove Source', 1, 1)
tk.Grid.columnconfigure(source_frame, 0, weight=1)
tk.Grid.rowconfigure(source_frame, 0, weight=1)
tk.Grid.columnconfigure(source_label, 0, weight=1)
tk.Grid.rowconfigure(source_label, 0, weight=1)

ignored_frame = tk.Frame(root)
ignored_frame.grid(row=2, column=0, sticky='nwe')
ignored_label = tk.LabelFrame(ignored_frame, text='Ignored')
ignored_label.grid(row=0, column=0, sticky='nwes')
ignored = ttk.Treeview(ignored_label)
ignored.grid(row=0, column=0, sticky='nwse')
ignored.config(height=5)
buttons_frame = tk.Frame(ignored_frame)
buttons_frame.grid(row=0, column=1, pady=7, sticky='nwes')
ignore = make_button(buttons_frame, 'Add Ignored', 0, 1)
remignore = make_button(buttons_frame, 'Remove Ignored', 1, 1)
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

if __name__ == '__main__':
    root.mainloop()
