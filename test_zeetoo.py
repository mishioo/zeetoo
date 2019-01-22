from pathlib import Path
from zeetoo import Backuper
import logging

if __name__ == '__main__':
	logging.getLogger().setLevel(logging.DEBUG)
	dest = Path(__file__).resolve().parent
	test = Path(dest, 'test')
	b = Backuper()
	b.destination = str(Path(dest, 'backup'))
	print(f'DEST: {b.destination}')
	b.add_source(str(Path(test, 'recursive')), 'r')
	b.add_source(str(Path(test, 'dir')), 'd')
	b.add_source(str(Path(test, 'files')), 'd')
	b.add_ignored(str(Path(test, 'recursive', 'ignored')))
	b.add_ignored(str(Path(test, 'dir', 'file_ignored.txt')))
	b.save_config('test_config.ini')
	b.backup()