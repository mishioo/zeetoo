import argparse
import logging
from itertools import chain
from pathlib import Path


logger = logging.getLogger(__name__)


def fix_cont(mol: str, version: str = 'V2000') -> str:
    if logger.isEnabledFor(logging.DEBUG) and '    0\n' in mol:
        logger.debug("Adding version number.")
    mol = mol.replace('    0\n', ' ' + version + '\n', 1)
    if not mol.endswith("M END\n"):
        logger.debug("Adding 'M END' marker.")
        mol = mol + "M END\n"
    return mol


def fix_file(file: Path, version: str = 'V2000'):
    with file.open('r+') as molfile:
        cont = molfile.read()
        if cont.endswith("M END\n") or '    0\n' not in cont:
            logger.info(f"File {file.name} already looks good.")
        else:
            logger.debug("Trying to fix file %s", file.name)
            new = fix_cont(cont, version)
            molfile.seek(0)
            molfile.write(new)


def get_args(argv=None):
    prs = argparse.ArgumentParser()
    prs.add_argument(
        'files', type=Path, nargs='+',
        help='One or more .mol files created by Gaussview or directories '
             'containing such files.'
    )
    prs.add_argument(
        '-v', type=str, default='V2000',
        help='.mol file version, default is V2000'
    )
    prs.add_argument(
        '-d', '--debug', action='store_true',
        help='print debug information to stdout'
    )
    prs.add_argument(
        '-s', '--silent', action='store_true',
        help='suppress printing to stdout'
    )
    return prs.parse_args(argv)


def main(argv=None):
    args = get_args(argv)
    if args.debug:
        logging.basicConfig(level='DEBUG')
    elif args.silent:
        logging.basicConfig(level='WARNING')
    else:
        logging.basicConfig(level='INFO')
    dirs = (path for path in args.files if path.is_dir())
    if logger.isEnabledFor(logging.DEBUG):
        dirs = list(dirs)
        logger.debug("Got %s dirs to search recursively.", len(dirs))
    inner_files = (
        path for dir in dirs for path in dir.iterdir()
        if path.is_file() and path.suffix is '.mol'
    )
    if logger.isEnabledFor(logging.DEBUG):
        inner_files = list(inner_files)
        logger.debug("Got %s .mol files from recursive search.", len(inner_files))
    args_files = (
        path for path in args.files if path.is_file()
    )
    if logger.isEnabledFor(logging.DEBUG):
        args_files = list(args_files)
        logger.debug("Got %s files given in arguments.", len(args_files))
    for file in chain(args_files, inner_files):
        logger.debug("Checking file %s", file)
        fix_file(file)


if __name__ == '__main__':
    main()
