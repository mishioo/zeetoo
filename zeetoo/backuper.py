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
    def configfile(self) -> pathlib.Path:
        return self.__configfile

    @configfile.setter
    def configfile(self, path) -> None:
        self.__configfile = pathlib.Path(path).resolve()

    def save_config(self, file: str = '') -> None:
        if file:
            self.configfile = file
        with open(self.configfile, 'w') as configfile:
            self.config.write(configfile)
        logging.debug(f'Config saved to {self.configfile}')

    def load_config(self, file: str = '') -> None:
        file = file if file else self.configfile
        config = configparser.ConfigParser(
            allow_no_value=True, delimiters=('=',)
        )
        with open(file, 'r') as configfile:
            config.read_file(configfile)
        self.configfile = file
        self.config = config
        logging.debug(f'Config loaded from {file}')

    @property
    def destination(self) -> str:
        return pathlib.Path(self.config['BACKUP']['destination'])

    @destination.setter
    def destination(self, destination: str) -> None:
        path = pathlib.Path(destination)
        if not path.exists():
            path.mkdir(parents=True)
            logging.debug("Created backup destination directory.")
        self.config['BACKUP']['destination'] = str(path.resolve())
        logging.debug(f'Destination set to {destination}')

    @property
    def sources(self) -> iter:
        return (
            (pathlib.Path(path), mode) for path, mode
            in self.config['SOURCE'].items()
            if path not in self.ignored
        )

    @property
    def ignored(self) -> set:
        return set(self.config['IGNORE'])

    def add_source(self, source: str, mode: str) -> pathlib.Path:
        if mode not in ('f', 'd', 'r'):
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

    def count_files(self, directory: pathlib.Path = None) -> int:
        ignored = self.ignored
        if directory is None:
            files = len([path for path, mode in self.sources if path.is_file()])
            dirs = (
                (path, mode) for path, mode in self.sources if path.is_dir()
            )
            for directory, mode in dirs:
                if mode == 'd':
                    files += len([
                        path for path in directory.iterdir() if path.is_file()
                        and str(path) not in ignored
                    ])
                elif mode == 'r':
                    files += self.count_files(directory)
                else:
                    raise ValueError(f"Invalid mode for directory {mode}")
        else:
            files = len([path for path in directory.iterdir() if path.is_file()
                         and str(path) not in self.ignored])
            dirs = (path for path in directory.iterdir() if path.is_dir()
                    and str(path) not in self.ignored)
            for path in dirs:
                files += self.count_files(path)
        return files

    def backup(self) -> None:
        basedest = pathlib.Path(self.config['BACKUP']['destination'])
        msg = f'Starting backup using {self.configfile.name} specification.' \
              if self.configfile.exists() else 'Starting backup as specified ' \
                                               'internally.'
        logging.info(msg)
        for path, mode in self.sources:
            if not path.exists():
                logging.warning(f"Specified source not found: {path}")
                continue
            if mode == 'f':
                logging.info(f'Moving to next source: {path}')
                dest = pathlib.Path(basedest, path.parent.name, path.name)
                if not dest.parent.exists():
                    dest.parent.mkdir(parents=True)
                    logging.debug(f"Dir created: {dest.parent}")
            else:
                dest = pathlib.Path(basedest, path.name)
            copyist = self._copyists[mode]
            copyist(path, dest)
        logging.info('Backup done.')

    def copy_file(self, src: pathlib.Path, dest: pathlib.Path) -> None:
        if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
            # copy
            shutil.copy2(src, dest)
            logging.debug(f"Copied file: {src}")
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
        logging.info(f'Moving to next source: {src}')
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
        self.copy_directory(src, dest)
        dirs = (
            path for path in src.iterdir()
            if path.is_dir() and not str(path) in self.ignored
        )
        for dir_ in dirs:
            self.copy_recursive(dir_, pathlib.Path(dest, dir_.name))

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
        if 'taskname' not in self.config['BACKUP']:
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
        self.save_config()
        cmd = self.schtasks_command
        subprocess.run(cmd, check=True)

    def unschedule(self) -> None:
        cmd = ['schtasks', '/delete', '/TN', f"{self.task_name}", '/F']
        subprocess.run(cmd, check=True)


def get_parser():
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
        '--taskname', '-n',
        help='name of the task scheduled, defaults to "zeetoo backup"'
    )
    parser.add_argument(
        '--period', '-p', choices=['once', 'daily', 'weekly', 'monthly'],
        help='how often should backup be run'
    )
    parser.add_argument(
        '--hour', '-H', type=int, choices=range(24), metavar='H',
        help='at which hour should task start, should be an integer between '
             '0 and 23'
    )
    parser.add_argument(
        '--minute', '-m', type=int, choices=range(60), metavar='M',
        help='how many minutes after specified hour should task start, '
             'should be an integer between 0 and 59'
    )
    parser.add_argument(
        '--schedule', '-s', action='store_true',
        help='schedules backup specified in config.ini file'
    )
    parser.add_argument(
        '--unschedule', '-u', action='store_true',
        help='removes backup task of specified task name from schedule'
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
        '--verbose', '-v', action='store_true', help='shows additional messages'
    )
    parser.add_argument(
        '--version', '-V', action='version', version='%(prog)s 0.1'
    )
    return parser


def main(argv=None):
    args = get_parser().parse_args(argv)
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
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
        for arg in args.add:
            backuper.add_source(arg, 'd')
    if args.recursively:
        for arg in args.recursively:
            backuper.add_source(arg, 'r')
    if args.ignore:
        for arg in args.ignore:
            backuper.add_ignored(arg)
    if args.schedule:
        backuper.schedule()
    if args.unschedule:
        backuper.unschedule()
    if args.run:
        backuper.backup()


if __name__ == '__main__':
    main()
