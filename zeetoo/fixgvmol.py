import argparse
import logging as lgg
from itertools import chain
from pathlib import Path


def fix_cont(mol: str, version: str = 'V2000') -> str:
    mol = mol.replace('    0\n', ' ' + version + '\n', 1)
    if not mol.endswith("M END\n"):
        mol = mol + "M END\n"
    return mol


def fix_file(file: Path, version: str = 'V2000'):
    with file.open('r+') as molfile:
        cont = molfile.read()
        if cont.endswith("M END\n") or '    0\n' not in cont:
            lgg.info(f"File {file.name} already looks good.")
        else:
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
    prs.add_argument('-v', type=str, default='V2000', help='.mol file version.')
    prs.add_argument(
        '-s', '--silent', action='store_true',
        help='Suppress printing to sdtout'
    )
    return prs.parse_args(argv)


def main():
    args = get_args()
    lgg.basicConfig(level='WARNING' if args.silent else 'INFO')
    dirs = (path for path in args.files if path.is_dir())
    inner_files = (
        path for dir in dirs for path in dir.iterdir()
        if path.is_file() and path.suffix is '.mol'
    )
    args_files = (
        path for path in args.files
        if path.is_file() and path.suffix is '.mol'
    )
    for file in chain(args_files, inner_files):
        fix_file(file)


if __name__ == '__main__':
    main()
