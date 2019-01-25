import logging
import pathlib
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import (askopenfilename, askopenfilenames,
                                askdirectory, asksaveasfilename)

from zeetoo import Backuper


def make_button(master, text, row=0, column=0, sticky='nwe', textvariable=None,
                command=None):
    b = ttk.Button(
        master, text=text, textvariable=textvariable, command=command
    )
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
    
    
def add_file(tree: ttk.Treeview, bcp: Backuper):
    paths = askopenfilenames()
    for path in paths:
        if str(pathlib.Path(path).resolve()) not in bcp.config['SOURCE']:
            path = bcp.add_source(path, 'f')
            tree.insert('', 'end', text=str(path))


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
    paths = askopenfilenames()
    for path in paths:
        if str(pathlib.Path(path).resolve()) not in bcp.ignored:
            path = bcp.add_ignored(path)
            tree.insert('', 'end', text=str(path))


def add_ignored_dir(tree: ttk.Treeview, bcp: Backuper):
    path = askdirectory()
    if path and str(pathlib.Path(path).resolve()) not in bcp.ignored:
        path = bcp.add_ignored(path)
        tree.insert('', 'end', text=str(path) + '\\')


def remove_item(tree: ttk.Treeview, bcp: Backuper, pathtype: str):
    for item in tree.selection():
        path = str(pathlib.Path(tree.item(item)['text'].strip('*')).resolve())
        done = bcp.config.remove_option(pathtype, path)
        if done:
            tree.delete(item)


def changed_time(
        period: tk.StringVar, hour: tk.StringVar, minute: tk.StringVar,
        bcp: Backuper
):
    bcp.set_time(period.get(), int(hour.get()), int(minute.get()))


def save(bcp: Backuper):
    path = asksaveasfilename(
        defaultextension='ini', initialfile='config.ini',
        initialdir=str(pathlib.Path(__file__).resolve().parent),
        filetypes=[('Config files', '*.ini'), ('All files', '*.*')]
    )
    if path:
        bcp.save_config()


def load(bcp: Backuper):
    file = askopenfilename()
    if file:
        bcp.load_config(file)
        fill_gui(bcp)


def schedule(bcp: Backuper):
    bcp.schedule()

    
def _run(bcp: Backuper):
    run_text_var.set('Running...')
    run_button.config(state='disabled')
    bcp.backup()
    try:
        run_text_var.set('Run Now')
        run_button.config(state='normal')
    except Exception:
        logging.debug('Could not change button state')


def unschedule(bcp: Backuper):
    bcp.unschedule()


def run_now(bcp: Backuper):
    thread = threading.Thread(target=_run, args=[bcp])
    thread.start()


def fill_gui(bcp: Backuper):
    dest_var.set(bcp.destination)
    source.delete(*source.get_children())
    ignored.delete(*ignored.get_children())
    for path, mode in bcp.config['SOURCE'].items():
        appendix = '\\' if mode == 'd' else '\\*' if mode == 'r' else ''
        source.insert('', 'end', text=path + appendix)
    for path in bcp.ignored:
        appendix = '\\' if pathlib.Path(path).is_dir() else ''
        ignored.insert('', 'end', text=path + appendix)
    period_var.set(bcp.config['BACKUP']['schedule'])
    hour, minute = bcp.config['BACKUP']['starttime'].split(':')
    hour_var.set(hour)
    min_var.set(minute)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('zeetoo backuper')
    tk.Grid.columnconfigure(root, 0, weight=1)
    tk.Grid.rowconfigure(root, 1, weight=1)
    dest_frame = tk.Frame(root)
    dest_frame.grid(row=0, column=0, sticky='nwe')
    tk.Label(dest_frame, text='Destination').grid(row=0, column=0, sticky='w')
    dest_var = tk.StringVar()
    dest_entry = tk.Entry(dest_frame, textvariable=dest_var,
                          validate="focusout",
                          validatecommand=lambda: changed_dest(dest_var,
                                                               backuper))
    dest_entry.grid(row=0, column=1, sticky='we')
    choose = make_button(dest_frame, 'Choose', 0, 2, 'we',
                         command=lambda: choose_dest(dest_var, backuper))
    tk.Grid.columnconfigure(dest_frame, 1, weight=1)
    tk.Grid.rowconfigure(dest_frame, 0, weight=1)

    source_frame = tk.Frame(root)
    source_frame.grid(row=1, column=0, sticky='nwes')
    source_label = tk.LabelFrame(
        source_frame, text='Source files and directories:'
    )
    source_label.grid(row=0, column=0, sticky='nwes')
    source = ttk.Treeview(source_label)
    source.grid(row=0, column=0, sticky='nwse')
    source['show'] = 'tree'
    source_bar = ttk.Scrollbar(
        source_label, orient='vertical', command=source.yview
    )
    source_bar.grid(row=0, column=1, sticky='nse')
    buttons_frame = tk.Frame(source_frame)
    buttons_frame.grid(row=0, column=1, pady=7, sticky='nwse')
    add_file_butt = make_button(buttons_frame, 'Add Files', 0, 1,
                                command=lambda: add_file(source, backuper))
    add_dir_butt = make_button(buttons_frame, 'Add Folder', 1, 1,
                               command=lambda: add_dir(source, backuper))
    add_tree_burr = make_button(buttons_frame, 'Add Folder Tree', 2, 1,
                                command=lambda: add_tree(source, backuper))
    remove_butt = make_button(
        buttons_frame, 'Remove Selected', 3, 1,
        command=lambda: remove_item(source, backuper, 'SOURCE')
    )
    tk.Grid.columnconfigure(source_frame, 0, weight=1)
    tk.Grid.rowconfigure(source_frame, 0, weight=1)
    tk.Grid.columnconfigure(source_label, 0, weight=1)
    tk.Grid.rowconfigure(source_label, 0, weight=1)

    ignored_frame = tk.Frame(root)
    ignored_frame.grid(row=2, column=0, sticky='nwe')
    ignored_label = tk.LabelFrame(
        ignored_frame, text='Ignored files and directories:'
    )
    ignored_label.grid(row=0, column=0, sticky='nwes')
    ignored = ttk.Treeview(ignored_label)
    ignored['show'] = 'tree'
    ignored.grid(row=0, column=0, sticky='nwse')
    ignored.config(height=5)
    source_bar = ttk.Scrollbar(
        ignored_label, orient='vertical', command=ignored.yview
    )
    source_bar.grid(row=0, column=1, sticky='nse')
    buttons_frame = tk.Frame(ignored_frame)
    buttons_frame.grid(row=0, column=1, pady=7, sticky='nwes')
    ignore_file_butt = make_button(
        buttons_frame, 'Add Files', 0, 1,
        command=lambda: add_ignored_file(ignored, backuper)
    )
    ignore_dir_butt = make_button(
        buttons_frame, 'Add Folder', 1, 1,
        command=lambda: add_ignored_dir(ignored, backuper)
    )
    remignore_butt = make_button(
        buttons_frame, 'Remove Selected', 2, 1,
        command=lambda: remove_item(ignored, backuper, 'IGNORE')
    )
    tk.Grid.columnconfigure(ignored_frame, 0, weight=1)
    tk.Grid.columnconfigure(ignored_label, 0, weight=1)

    time_frame = tk.Frame(root)
    time_frame.grid(row=3, column=0, sticky='nwes')
    tk.Label(time_frame, text='Backup frequency: ').grid(row=0, column=0)
    period_var = tk.StringVar()
    period_box = ttk.Combobox(time_frame, textvariable=period_var)
    period_box['values'] = ['DAILY', 'WEEKLY', 'MONTHLY']
    period_box.grid(row=0, column=1)
    period_box.config(width=11)
    period_box.bind(
        '<<ComboboxSelected>>',
        lambda e: changed_time(period_var, hour_var, min_var, backuper)
    )
    tk.Label(time_frame, text='Hour: ').grid(row=0, column=2)
    hour_var = tk.StringVar()
    hour_box = ttk.Combobox(time_frame, textvariable=hour_var)
    hour_box['values'] = [f'{x:0>2}' for x in range(1, 25)]
    hour_box.grid(row=0, column=3)
    hour_box.config(width=3)
    hour_box.bind(
        '<<ComboboxSelected>>',
        lambda e: changed_time(period_var, hour_var, min_var, backuper)
    )
    tk.Label(time_frame, text='Min: ').grid(row=0, column=4)
    min_var = tk.StringVar()
    min_box = ttk.Combobox(time_frame, textvariable=min_var)
    min_box['values'] = [f'{x:0>2}' for x in range(0, 60, 5)]
    min_box.grid(row=0, column=5)
    min_box.config(width=3)
    min_box.bind(
        '<<ComboboxSelected>>',
        lambda e: changed_time(period_var, hour_var, min_var, backuper)
    )
    bottom_frame = tk.Frame(root)
    bottom_frame.grid(row=4, column=0, sticky='nwes')
    sched_button = make_button(bottom_frame, 'Schedule', 0, 0,
                               command=lambda: schedule(backuper))
    unsched_button = make_button(bottom_frame, 'Unschedule', 0, 1,
                                 command=lambda: unschedule(backuper))
    run_text_var = tk.StringVar()
    run_text_var.set('Run Now')
    run_button = make_button(bottom_frame, '', 0, 2, textvariable=run_text_var,
                             command=lambda: run_now(backuper))
    tk.Frame(bottom_frame).grid(row=0, column=3, sticky='we')
    load_button = make_button(bottom_frame, 'Load Config', 0, 4,
                              command=lambda: load(backuper))
    save_button = make_button(bottom_frame, 'Save Config', 0, 5,
                              command=lambda: save(backuper))
    tk.Grid.columnconfigure(bottom_frame, 3, weight=1)
    tk.Grid.rowconfigure(bottom_frame, 0, weight=1)

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    backuper = Backuper(
        pathlib.Path(__file__).resolve().with_name('config.ini')
    )
    fill_gui(backuper)

    root.mainloop()
