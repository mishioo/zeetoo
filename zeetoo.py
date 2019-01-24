import argparse
import configparser
import datetime
import logging
import pathlib
import shutil
import subprocess
import sys


class Backuper:

    def __init__(self, configfile: str = '') -> None:
        self.configfile = configfile if configfile else \
            f'config_{int(datetime.datetime.now().timestamp())}.ini'
        if configfile and self.configfile.exists():
            self.config = configparser.ConfigParser(
                allow_no_value=True, delimiters=('=',)
            )
            with open(self.configfile, 'r') as file:
                self.config.read_file(file)
        if configfile and not self.configfile.exists():
            logging.warning('Specified file does not exist. '
                            'Initializing with standard parameters')
        # raise FileNotFoundError(f'No such file: {configfile}')
        if not configfile or not self.configfile.exists():
            self.config = configparser.ConfigParser(
                allow_no_value=True, delimiters=('=',)
            )
            self.config['BACKUP'] = {'destination': str(pathlib.Path.cwd()),
                                     'taskname': 'zeetoo backup',
                                     'schedule': 'DAILY',
                                     'starttime': '03:00'}
            self.config['SOURCE'] = {}
            self.config['IGNORE'] = {}
        self._copyists = {
            'f': self.copy_file,
            'd': self.copy_directory,
            'r': self.copy_recursive
        }

    @property
    def configfile(self):
        return self.__configfile

    @configfile.setter
    def configfile(self, path):
        self.__configfile = pathlib.Path(path)

    def save_config(self, file: str) -> None:
        with open(file, 'w') as configfile:
            self.config.write(configfile)
        logging.debug(f'Config saved to {file}')

    def load_config(self, file: str) -> None:
        self.config = configparser.ConfigParser(
            allow_no_value=True, delimiters=('=',)
        )
        with open(file, 'r') as configfile:
            self.config.read_file(configfile)
        logging.debug(f'Config loaded from {file}')

    @property
    def destination(self) -> str:
        return pathlib.Path(self.config['BACKUP']['destination'])

    @destination.setter
    def destination(self, destination: str) -> None:
        path = pathlib.Path(destination)
        if not path.exists():
            raise FileNotFoundError('Backup destination directory must exist.')
        self.config['BACKUP']['destination'] = str(path.resolve())
        logging.debug(f'Destination set to {destination}')

    @property
    def ignored(self):
        return set(self.config['IGNORE'])

    def add_source(self, source: str, mode: str) -> pathlib.Path:
        if not mode in ('f', 'd', 'r'):
            raise ValueError(
                "Invalid mode. Mode should be one of: 'f', 'd', 'r'"
            )
        path = pathlib.Path(source).resolve()
        if not path.exists():
            logging.warning(f"Source doesn't exist: {source}")
        # raise if source incompatible with mode
        self.config['SOURCE'][str(path)] = mode
        return path

    def remove_source(self, source: str) -> bool:
        return self.config.remove_option('SOURCE', source)

    def add_ignored(self, ignored: str) -> pathlib.Path:
        path = pathlib.Path(ignored).resolve()
        self.config['IGNORE'][str(path)] = None
        logging.debug(f"Ignored path registered: {ignored}")
        return path

    def remove_ignored(self, ignored: str) -> bool:
        return self.config.remove_option('IGNORED', ignored)

    def backup(self) -> None:
        basedest = pathlib.Path(self.config['BACKUP']['destination'])
        source = (
            (path, mode) for path, mode in self.config['SOURCE'].items()
            if path not in self.ignored
        )  # generators 4 the win
        for path, mode in source:
            src = pathlib.Path(path)
            dest = pathlib.Path(basedest, src.name)
            copyist = self._copyists[mode]
            copyist(src, dest)

    def copy_file(self, src: pathlib.Path, dest: pathlib.Path) -> None:
        if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
            # copy
            logging.debug(f"Copyied file: {src}")
            shutil.copy2(src, dest)
        elif dest.exists() and src.stat().st_mtime < dest.stat().st_mtime:
            # rename and copy
            filetime = datetime.datetime.fromtimestamp(dest.stat().st_mtime)
            filetime = filetime.strftime('_newer_%Y-%m-%d_%H-%M')
            newer_name = dest.name.split('.')
            newer_name[0] += filetime
            newer_name = '.'.join(newer_name)
            newer_path = pathlib.Path(dest.parent, newer_name)
            dest.rename(newer_path)
            shutil.copy2(src, dest)
            logging.warning(
                f"Newer file version found in backup directory:\n\t{src}"
                f"\n\tNewer file renamed to {newer_name}"
            )
        else:
            # leave it be
            logging.debug(f"File didn't change: {src}")
            pass

    def copy_directory(self, src: pathlib.Path, dest: pathlib.Path) -> None:
        if not dest.exists():
            dest.mkdir(parents=True)
            logging.debug(f"Dir created: {dest}")
        files = (
            path for path in src.iterdir()
            if path.is_file() and not str(path) in self.ignored
        )
        for path in files:
            self.copy_file(path, pathlib.Path(dest, path.name))

    def copy_recursive(self, src: pathlib.Path, dest: pathlib.Path) -> None:
        # log 'debug: copying recursively {dir}'
        if not dest.exists():
            dest.mkdir(parents=True)
            logging.debug(f"Dir created: {dest}")
        files = (
            path for path in src.iterdir()
            if path.is_file() and not str(path) in self.ignored
        )
        for file in files:
            self.copy_file(file, pathlib.Path(dest, file.name))
        dirs = (
            path for path in src.iterdir()
            if path.is_dir() and not str(path) in self.ignored
        )
        for dir in dirs:
            self.copy_directory(dir, pathlib.Path(dest, dir.name))

    def set_time(
            self, period: str = None, hour: int = None, minute: int = None
    ) -> None:
        if period:
            self.config['BACKUP']['schedule'] = period
        if hour is None and minute is None:
            return
        curr_hour, curr_minute = self.config['BACKUP']['starttime'].split(':')
        hour = hour if hour is not None else int(curr_hour)
        minute = minute if minute is not None else int(curr_minute)
        self.config['BACKUP']['starttime'] = f"{hour:0>2}:{minute:0>2}"

    @property
    def task_name(self) -> str:
        if not 'taskname' in self.config['BACKUP']:
            raise ValueError('Task name not specified.')
        else:
            return self.config['BACKUP']['taskname']

    @task_name.setter
    def task_name(self, name: str) -> None:
        self.config['BACKUP']['taskname'] = name

    @property
    def schtasks_command(self) -> list:
        script = pathlib.Path(__file__).resolve()
        cmd = [
            'schtasks', '/create', '/F', '/TN', self.task_name,
            '/SC', self.config['BACKUP']['schedule'],
            '/ST', self.config['BACKUP']['starttime'], '/TR',
            f'"{sys.executable}" "{script}" -c "{self.configfile.resolve()}" -b'
        ]
        return cmd

    def schedule(self) -> None:
        cmd = self.schtasks_command
        self.save_config(self.configfile)
        subprocess.run(cmd, check=True)

    def unschedule(self) -> None:
        cmd = ['schtasks', '/delete', '/TN', f"{self.task_name}", '/F']
        subprocess.run(cmd, check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='zeetoo backuper')
    parser.add_argument(
        '--configfile', '-c', metavar='path', default='',
        help="path to Backupers' config.ini file"
    )
    parser.add_argument(
        '--destination', '-d', metavar='path',
        help="path to Backupers' config.ini file"
    )
    parser.add_argument(
        '--add-sources', '-a', metavar='path', nargs='*', dest='add',
        help="directories to backup"
    )
    parser.add_argument(
        '--recursively', '-r', metavar='path', nargs='*',
        help="directories to backup, including all it's subdirectories"
    )
    parser.add_argument(
        '--ignore', '-i', metavar='path', nargs='*',
        help="files and folders ignored"
    )
    parser.add_argument(
        '--taskname', '-n', help='name of the task scheduled'
    )
    parser.add_argument(
        '--period', '-p', choices=['once', 'daily', 'weekly', 'monthly'],
        help='how often should backup be run'
    )
    parser.add_argument(
        '--hour', '-H', type=int, choices=range(24),
        help='at which hour should task start'
    )
    parser.add_argument(
        '--minute', '-m', type=int, choices=range(60),
        help='how many minutes after specified hour should task start'
    )
    parser.add_argument(
        '--schedule', '-s', action='store_true',
        help='schedules backup specified in config.ini file'
    )
    parser.add_argument(
        '--unschedule', '-u', action='store_true',
        help='runs backup specified in config.ini file'
    )
    parser.add_argument(
        '--run-backup', '-b', action='store_true', dest='run',
        help='runs backup specified in config.ini file'
    )
    parser.add_argument(
        '--debug', '-D', action='store_true',
        help='prints schtasks_command generated from config.ini file'
    )
    parser.add_argument(
        '--version', '-v', action='version', version='%(prog)s 0.1'
    )
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    backuper = Backuper(args.configfile)
    if args.taskname:
        backuper.task_name = args.taskname
    if args.period or args.hour or args.minute:
        backuper.set_time(args.period, args.hour, args.minute)
    if args.destination:
        backuper.destination = args.destination
    if args.add:
        for path in args.add:
            backuper.add_source(path, 'd')
    if args.recursively:
        for path in args.recursively:
            backuper.add_source(path, 'r')
    if args.ignore:
        for path in args.ignore:
            backuper.add_ignored(path)
    if args.debug:
        print(f'Backuper for task: {backuper.task_name}')
        print(f'Backup destination: {backuper.destination}')
        print(f'Command: {backuper.schtasks_command}')
    if args.schedule:
        backuper.schedule()
    if args.unschedule:
        backuper.unschedule()
    if args.run:
        backuper.backup()
