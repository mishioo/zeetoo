import tkinter as tk
import tkinter.ttk as ttk

def make_button(master, text, row=0, column=0, sticky='nwe'):
	b = ttk.Button(master, text=text)
	b.grid(row=row, column=column, sticky=sticky)
	return b

root = tk.Tk()
left = tk.Frame(root)
left.grid(row=0, column=0, sticky='nwse')
tk.Label(left, text='Destination').grid(row=0, column=0, sticky='nw')
dest_var = tk.StringVar()
dest_entry = tk.Entry(left, textvariable=dest_var)
dest_entry.grid(row=0, column=1, sticky='ne')
source_frame = tk.LabelFrame(left, text='Source')
source_frame.grid(row=1, column=0, columnspan=2, sticky='nwes')
source = ttk.Treeview(source_frame)
source.grid(row=0, column=0, sticky='nwse')
ignored_frame = tk.LabelFrame(left, text='Ignored')
ignored_frame.grid(row=2, column=0, columnspan=2, sticky='wes')
ignored = ttk.Treeview(ignored_frame)
ignored.grid(row=0, column=0, sticky='nwse')

right = tk.Frame(root)
right.grid(row=0, column=1, sticky='ns')
choose = make_button(right, 'Choose', 0)
add = make_button(right, 'Add Source', 1)
remove = make_button(right, 'Remove Source', 2)
ignore = make_button(right, 'Add Ignored', 3)
remignore = make_button(right, 'Romove Ignored', 4)
save = make_button(right, 'Save Config', 5)
load = make_button(right, 'Load Config', 6)
sched = make_button(right, 'Schedule', 7, sticky='swe')

if __name__ == '__main__':
	root.mainloop()
