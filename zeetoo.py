import configparser
import datetime
import logging
import pathlib
import shutil


class Backuper:

	def __init__(self, configfile: str = '') -> None:
		self.configfile = pathlib.Path(configfile) if configfile else None
		if configfile and self.configfile.exists():
			self.config = configparser.ConfigParser(
				allow_no_value=True, delimiters=('=',)
			)
			with open(self.configfile, 'r') as file:
				self.config.read_file(file)
		elif configfile and not self.configfile.exists():
			raise FileNotFoundError(f'No such file: {configfile}')
		else:
			self.config = configparser.ConfigParser(
				allow_no_value=True, delimiters=('=',)
			)
			self.config['BACKUP'] = {'destination': str(pathlib.Path.cwd())}
			self.config['SOURCE'] = {}
			self.config['IGNORE'] = {}
		self._copyists = {
			'f': self.copy_file,
			'd': self.copy_directory,
			'r': self.copy_recursive
		}

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
		self.config['BACKUP']['destination'] = destination
		logging.debug(f'Destination set to {destination}')
		
	@property
	def ignored(self):
		return set(self.config['IGNORE'])
		
	def add_source(self, source: str, mode: str) -> None:
		if not mode in ('f', 'd', 'r'):
			raise ValueError(
				"Invalid mode. Mode should be one of: 'f', 'd', 'r'"
			)
		if not pathlib.Path(source).exists():
			logging.warning(f"Source doesn't exist: {source}")
		# raise if source incompatible with mode
		self.config['SOURCE'][source] = mode
		
	def remove_source(self, source: str) -> bool:
		return self.config.remove_option('SOURCE', source)
		
	def add_ignored(self, ignored: str):
		self.config['IGNORE'][ignored] = None
		logging.debug(f"Ignored path registered: {ignored}")
		
	def remove_ignored(self, ignored: str) -> bool:
		return self.config.remove_option('IGNORED', ingored)
		
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

		
if __name__ == '__main__':
	backuper = Backuper()
	backuper.save_config('someconf.ini')
	print(backuper.destination)
	