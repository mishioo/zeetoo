import logging
import pathlib
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import (askopenfilename, askopenfilenames,
                                askdirectory, asksaveasfilename)

from backuper import Backuper


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('zeetoo backuper')
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.rowconfigure(self, 1, weight=1)
        dest_frame = tk.Frame(self)
        dest_frame.grid(row=0, column=0, sticky='nwe')
        tk.Label(dest_frame, text='Destination').grid(row=0, column=0,
                                                      sticky='w')
        self.dest_var = tk.StringVar()
        dest_entry = tk.Entry(dest_frame, textvariable=self.dest_var)
        dest_entry.grid(row=0, column=1, sticky='we')
        dest_entry.bind('<FocusOut>', lambda e: self.changed_dest())
        choose = make_button(
            dest_frame, 'Choose', 0, 2, 'we', command=self.choose_dest
        )
        tk.Grid.columnconfigure(dest_frame, 1, weight=1)
        tk.Grid.rowconfigure(dest_frame, 0, weight=1)

        source_frame = tk.Frame(self)
        source_frame.grid(row=1, column=0, sticky='nwes')
        source_label = tk.LabelFrame(
            source_frame, text='Source files and directories:'
        )
        source_label.grid(row=0, column=0, sticky='nwes')
        self.source = ttk.Treeview(source_label)
        self.source.grid(row=0, column=0, sticky='nwse')
        self.source['show'] = 'tree'
        source_bar = ttk.Scrollbar(
            source_label, orient='vertical', command=self.source.yview
        )
        source_bar.grid(row=0, column=1, sticky='nse')
        buttons_frame = tk.Frame(source_frame)
        buttons_frame.grid(row=0, column=1, pady=7, sticky='nwse')
        add_file_butt = make_button(
            buttons_frame, 'Add Files', 0, 1, command=self.add_file
        )
        add_dir_butt = make_button(
            buttons_frame, 'Add Folder', 1, 1, command=self.add_dir
        )
        add_tree_burr = make_button(
            buttons_frame, 'Add Folder Tree', 2, 1, command=self.add_tree
        )
        remove_butt = make_button(
            buttons_frame, 'Remove Selected', 3, 1,
            command=lambda: self.remove_item(self.source, 'SOURCE')
        )
        tk.Grid.columnconfigure(source_frame, 0, weight=1)
        tk.Grid.rowconfigure(source_frame, 0, weight=1)
        tk.Grid.columnconfigure(source_label, 0, weight=1)
        tk.Grid.rowconfigure(source_label, 0, weight=1)

        ignored_frame = tk.Frame(self)
        ignored_frame.grid(row=2, column=0, sticky='nwe')
        ignored_label = tk.LabelFrame(
            ignored_frame, text='Ignored files and directories:'
        )
        ignored_label.grid(row=0, column=0, sticky='nwes')
        self.ignored = ttk.Treeview(ignored_label)
        self.ignored['show'] = 'tree'
        self.ignored.grid(row=0, column=0, sticky='nwse')
        self.ignored.config(height=5)
        source_bar = ttk.Scrollbar(
            ignored_label, orient='vertical', command=self.ignored.yview
        )
        source_bar.grid(row=0, column=1, sticky='nse')
        buttons_frame = tk.Frame(ignored_frame)
        buttons_frame.grid(row=0, column=1, pady=7, sticky='nwes')
        ignore_file_butt = make_button(
            buttons_frame, 'Add Files', 0, 1, command=self.add_ignored_file
        )
        ignore_dir_butt = make_button(
            buttons_frame, 'Add Folder', 1, 1, command=self.add_ignored_dir
        )
        remignore_butt = make_button(
            buttons_frame, 'Remove Selected', 2, 1,
            command=lambda: self.remove_item(self.ignored, 'IGNORE')
        )
        tk.Grid.columnconfigure(ignored_frame, 0, weight=1)
        tk.Grid.columnconfigure(ignored_label, 0, weight=1)

        time_frame = tk.Frame(self)
        time_frame.grid(row=3, column=0, sticky='nwes')
        tk.Label(time_frame, text='Backup frequency: ').grid(row=0, column=0)
        self.period_var = tk.StringVar()
        period_box = ttk.Combobox(time_frame, textvariable=self.period_var)
        period_box['values'] = ['DAILY', 'WEEKLY', 'MONTHLY']
        period_box.grid(row=0, column=1)
        period_box.config(width=11)
        period_box.bind(
            '<<ComboboxSelected>>', lambda e: self.changed_time()
        )
        tk.Label(time_frame, text='Hour: ').grid(row=0, column=2)
        self.hour_var = tk.StringVar()
        hour_box = ttk.Combobox(time_frame, textvariable=self.hour_var)
        hour_box['values'] = [f'{x:0>2}' for x in range(1, 25)]
        hour_box.grid(row=0, column=3)
        hour_box.config(width=3)
        hour_box.bind(
            '<<ComboboxSelected>>', lambda e: self.changed_time()
        )
        tk.Label(time_frame, text='Min: ').grid(row=0, column=4)
        self.min_var = tk.StringVar()
        min_box = ttk.Combobox(time_frame, textvariable=self.min_var)
        min_box['values'] = [f'{x:0>2}' for x in range(0, 60, 5)]
        min_box.grid(row=0, column=5)
        min_box.config(width=3)
        min_box.bind(
            '<<ComboboxSelected>>', lambda e: self.changed_time()
        )
        bottom_frame = tk.Frame(self)
        bottom_frame.grid(row=4, column=0, sticky='nwes')
        sched_button = make_button(
            bottom_frame, 'Schedule', 0, 0, command=self.schedule
        )
        unsched_button = make_button(
            bottom_frame, 'Unschedule', 0, 1, command=self.unschedule
        )
        self.run_text_var = tk.StringVar()
        self.run_text_var.set('Run Now')
        self.run_button = make_button(
            bottom_frame, '', 0, 2, textvariable=self.run_text_var,
            command=self.run_now
        )
        tk.Frame(bottom_frame).grid(row=0, column=3, sticky='we')
        load_button = make_button(
            bottom_frame, 'Load Config', 0, 4, command=self.load
        )
        save_button = make_button(
            bottom_frame, 'Save Config', 0, 5, command=self.save
        )
        tk.Grid.columnconfigure(bottom_frame, 3, weight=1)
        tk.Grid.rowconfigure(bottom_frame, 0, weight=1)

        self.backuper = Backuper(
            pathlib.Path(__file__).resolve().with_name('config.ini')
        )
        self.fill_gui()

    def choose_dest(self):
        path = askdirectory()
        if path:
            self.backuper.destination = path
            self.dest_var.set(self.backuper.destination)

    def changed_dest(self):
        path = self.dest_var.get()
        self.backuper.destination = path

    def add_file(self):
        paths = askopenfilenames()
        for path in paths:
            if str(pathlib.Path(path).resolve()) \
                    not in self.backuper.config['SOURCE']:
                path = self.backuper.add_source(path, 'f')
                self.source.insert('', 'end', text=str(path))

    def add_dir(self):
        path = askdirectory()
        if path and str(pathlib.Path(path).resolve()) \
                not in self.backuper.config['SOURCE']:
            path = self.backuper.add_source(path, 'd')
            self.source.insert('', 'end', text=str(path) + '\\')

    def add_tree(self):
        path = askdirectory()
        if path and str(pathlib.Path(path).resolve()) \
                not in self.backuper.config['SOURCE']:
            path = self.backuper.add_source(path, 'r')
            self.source.insert('', 'end', text=str(path) + '\\*')

    def add_ignored_file(self):
        paths = askopenfilenames()
        for path in paths:
            if str(pathlib.Path(path).resolve()) \
                    not in self.backuper.ignored:
                path = self.backuper.add_ignored(path)
                self.ignored.insert('', 'end', text=str(path))

    def add_ignored_dir(self):
        path = askdirectory()
        if path and str(pathlib.Path(path).resolve()) \
                not in self.backuper.ignored:
            path = self.backuper.add_ignored(path)
            self.ignored.insert('', 'end', text=str(path) + '\\')

    def remove_item(self, tree: ttk.Treeview, pathtype: str):
        for item in tree.selection():
            path = str(
                pathlib.Path(tree.item(item)['text'].strip('*')).resolve()
            )
            done = self.backuper.config.remove_option(pathtype, path)
            if done:
                tree.delete(item)

    def changed_time(self):
        self.backuper.set_time(
            self.period_var.get(),
            int(self.hour_var.get()),
            int(self.min_var.get())
        )

    def save(self):
        path = asksaveasfilename(
            defaultextension='ini', initialfile='config.ini',
            initialdir=str(pathlib.Path(__file__).resolve().parent),
            filetypes=[('Config files', '*.ini'), ('All files', '*.*')]
        )
        if path:
            self.backuper.save_config()

    def load(self):
        file = askopenfilename()
        if file:
            self.backuper.load_config(file)
            self.fill_gui()

    def schedule(self):
        self.backuper.schedule()

    def _run(self):
        self.run_text_var.set('Running...')
        self.run_button.config(state='disabled')
        self.backuper.backup()
        try:
            self.run_text_var.set('Run Now')
            self.run_button.config(state='normal')
        except Exception:
            logging.debug('Could not change button state')

    def unschedule(self):
        self.backuper.unschedule()

    def run_now(self):
        thread = threading.Thread(target=self._run, args=[self.backuper])
        thread.start()

    def fill_gui(self):
        self.dest_var.set(self.backuper.destination)
        self.source.delete(*self.source.get_children())
        self.ignored.delete(*self.ignored.get_children())
        for path, mode in self.backuper.config['SOURCE'].items():
            appendix = '\\' if mode == 'd' else '\\*' if mode == 'r' else ''
            self.source.insert('', 'end', text=path + appendix)
        for path in self.backuper.ignored:
            appendix = '\\' if pathlib.Path(path).is_dir() else ''
            self.ignored.insert('', 'end', text=path + appendix)
        self.period_var.set(self.backuper.config['BACKUP']['schedule'])
        hour, minute = self.backuper.config['BACKUP']['starttime'].split(':')
        self.hour_var.set(hour)
        self.min_var.set(minute)


def make_button(master, text, row=0, column=0, sticky='nwe', textvariable=None,
                command=None):
    b = ttk.Button(
        master, text=text, textvariable=textvariable, command=command
    )
    b.grid(row=row, column=column, sticky=sticky)
    b.config(width=15)
    return b


def main(argv=None):
    logging.basicConfig(
        format='%(levelname)s: %(message)s', level=logging.INFO
    )
    root = App()
    root.mainloop()


if __name__ == '__main__':

    main()
