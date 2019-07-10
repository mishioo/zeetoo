import logging
import pathlib
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import (askopenfilename, askopenfilenames,
                                askdirectory, asksaveasfilename)

from backuper import Backuper


# To be introduced
# ZTHOME = pathlib.Path.home() / 'AppData' / 'zeetoo' / 'backuper'
# ZTHOME.mkdir(parents=True, exist_ok=True)


class JobFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        label_frame = tk.LabelFrame(self, text='Backup jobs')
        label_frame.grid(row=0, column=0, sticky='nwes')
        self.tree = ttk.Treeview(label_frame)
        self.tree.grid(row=0, column=0, sticky='nwse')
        self.tree['columns'] = ('Job name', 'Status')
        scrollbar = ttk.Scrollbar(
            label_frame, orient='vertical', command=self.tree.yview
        )
        scrollbar.grid(row=0, column=1, sticky='nse')
        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=0, column=1, pady=7, sticky='nwse')
        make_button(
            buttons_frame, 'New Job', 0, 1, command=self.new_job
        )
        make_button(
            buttons_frame, 'Remove Selected', 1, 1, command=self.remove_item
        )
        make_button(
            buttons_frame, 'Import Config...', 2, 1, command=self.import_config
        )
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.rowconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(label_frame, 0, weight=1)
        tk.Grid.rowconfigure(label_frame, 0, weight=1)

    def new_job(self):
        pass

    def remove_item(self):
        pass

    def import_config(self):
        pass


class SourceFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        label_frame = tk.LabelFrame(
            self, text='Source files and directories:'
        )
        label_frame.grid(row=0, column=0, sticky='nwes')
        self.tree = ttk.Treeview(label_frame)
        self.tree.grid(row=0, column=0, sticky='nwse')
        self.tree['show'] = 'tree'
        scrollbar = ttk.Scrollbar(
            label_frame, orient='vertical', command=self.tree.yview
        )
        scrollbar.grid(row=0, column=1, sticky='nse')
        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=0, column=1, pady=7, sticky='nwse')
        make_button(
            buttons_frame, 'Add Files', 0, 1, command=self.add_file
        )
        make_button(
            buttons_frame, 'Add Folder', 1, 1, command=self.add_dir
        )
        make_button(
            buttons_frame, 'Add Folder Tree', 2, 1, command=self.add_tree
        )
        make_button(
            buttons_frame, 'Remove Selected', 3, 1, command=self.remove_item
        )
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.rowconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(label_frame, 0, weight=1)
        tk.Grid.rowconfigure(label_frame, 0, weight=1)

    def add_file(self):
        paths = askopenfilenames()
        for path in paths:
            if str(pathlib.Path(path).resolve()) \
                    not in self.master.backuper.config['SOURCE']:
                path = self.master.backuper.add_source(path, 'f')
                self.tree.insert('', 'end', text=str(path))

    def add_dir(self):
        path = askdirectory()
        if path and str(pathlib.Path(path).resolve()) \
                not in self.master.backuper.config['SOURCE']:
            path = self.master.backuper.add_source(path, 'd')
            self.tree.insert('', 'end', text=str(path) + '\\')

    def add_tree(self):
        path = askdirectory()
        if path and str(pathlib.Path(path).resolve()) \
                not in self.master.backuper.config['SOURCE']:
            path = self.master.backuper.add_source(path, 'r')
            self.tree.insert('', 'end', text=str(path) + '\\*')

    def remove_item(self):
        for item in self.tree.selection():
            path = str(
                pathlib.Path(self.tree.item(item)['text'].strip('*')).resolve()
            )
            done = self.master.backuper.config.remove_option('SOURCE', path)
            if done:
                self.tree.delete(item)


class IgnoredFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        label_frame = tk.LabelFrame(
            self, text='Ignored files and directories:'
        )
        label_frame.grid(row=0, column=0, sticky='nwes')
        self.tree = ttk.Treeview(label_frame)
        self.tree['show'] = 'tree'
        self.tree.grid(row=0, column=0, sticky='nwse')
        self.tree.config(height=5)
        scrollbar = ttk.Scrollbar(
            label_frame, orient='vertical', command=self.tree.yview
        )
        scrollbar.grid(row=0, column=1, sticky='nse')
        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=0, column=1, pady=7, sticky='nwes')
        make_button(
            buttons_frame, 'Add Files', 0, 1, command=self.add_ignored_file
        )
        make_button(
            buttons_frame, 'Add Folder', 1, 1, command=self.add_ignored_dir
        )
        make_button(
            buttons_frame, 'Remove Selected', 2, 1,
            command=lambda: self.remove_item()
        )
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(label_frame, 0, weight=1)
        tk.Grid.columnconfigure(label_frame, 0, weight=1)

    def add_ignored_file(self):
        paths = askopenfilenames()
        for path in paths:
            if str(pathlib.Path(path).resolve()) \
                    not in self.master.backuper.ignored:
                path = self.master.backuper.add_ignored(path)
                self.tree.insert('', 'end', text=str(path))

    def add_ignored_dir(self):
        path = askdirectory()
        if path and str(pathlib.Path(path).resolve()) \
                not in self.master.backuper.ignored:
            path = self.master.backuper.add_ignored(path)
            self.tree.insert('', 'end', text=str(path) + '\\')

    def remove_item(self):
        for item in self.tree.selection():
            path = str(
                pathlib.Path(self.tree.item(item)['text'].strip('*')).resolve()
            )
            done = self.master.backuper.config.remove_option('IGNORE', path)
            if done:
                self.tree.delete(item)


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

        self.source = SourceFrame(self)
        self.source.grid(row=1, column=0, sticky='nwes')

        self.ignored = IgnoredFrame(self)
        self.ignored.grid(row=2, column=0, sticky='nwe')

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
        self.source.tree.delete(*self.source.tree.get_children())
        self.ignored.tree.delete(*self.ignored.tree.get_children())
        for path, mode in self.backuper.config['SOURCE'].items():
            appendix = '\\' if mode == 'd' else '\\*' if mode == 'r' else ''
            self.source.tree.insert('', 'end', text=path + appendix)
        for path in self.backuper.ignored:
            appendix = '\\' if pathlib.Path(path).is_dir() else ''
            self.ignored.tree.insert('', 'end', text=path + appendix)
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
