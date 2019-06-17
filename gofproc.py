import openpyxl as opxl
import re
import argparse
from itertools import chain
from pathlib import Path
import logging as lgg

number_group = r'\s*(-?\d+\.?\d*)'
number = number_group.replace('(', '').replace(')', '')
energies = re.compile(
    r' Sum of electronic and zero-point Energies=\s*(-?\d+\.?\d*)\n'
    r' Sum of electronic and thermal Energies=\s*(-?\d+\.?\d*)\n'
    r' Sum of electronic and thermal Enthalpies=\s*(-?\d+\.?\d*)\n'
    r' Sum of electronic and thermal Free Energies=\s*(-?\d+\.?\d*)'
)  # use .search(text).groups()
frequencies = re.compile(
    'Frequencies(?:\s+(?:Fr= \d+)?--\s+)' + 3 * number_group
)


def get_args(argv=None):
    prs = argparse.ArgumentParser(
        description='Process gaussian optimization files to get energies and '
                    'number of imaginary frequencies.'
    )
    prs.add_argument(
        'files', type=Path, nargs='+',
        help='one or more gaussian output files or directories with such'
    )
    prs.add_argument(
        '--excel', '-e', type=Path, default=None,
        help='path to excel file; if not specified output '
             'will be printed to stdout'
    )
    prs.add_argument(
        '-s', '--silent', action='store_true',
        help='Suppress printing to sdtout'
    )
    return prs.parse_args(argv)


def get_data(path):
    with path.open('r') as file:
        text = file.read()
    ens = energies.search(text)
    freqs = frequencies.findall(text)
    if not ens or not freqs:
        lgg.info(f'{path.name} - NOT CONVERGED')
        return []
    else:
        imag = sum(float(f) < 0 for line in freqs for f in line)
        return [path.name, *ens.groups(), imag]


def main():
    args = get_args()
    lgg.basicConfig(level='WARNING' if args.silent else 'INFO')
    dirs = (path for path in args.files if path.is_dir())
    inner_files = (
        path for dir in dirs for path in dir.iterdir()
        if path.is_file() and path.suffix in ['.log', '.out']
    )
    args_files = (
        path for path in args.files
        if path.is_file() and path.suffix in ['.log', '.out']
    )
    files = chain(args_files, inner_files)
    data = []
    for path in files:
        line = get_data(path)
        if line:
            data.append(line)
    lgg.info(f"Got {len(data)} files to show")
    try:
        length = max(len(line[0]) for line in data)
    except ValueError:
        length = 0
    if args.excel:
        wb = opxl.load_workbook(str(args.excel))
        sheet = wb.active
    for file, zpe, ten, ent, gib, imag in data:
        lgg.info(
            f"{file: <{length}} - "
            f"ZPE= {zpe: >12} "
            f"TEN= {ten: >12} "
            f"ENT= {ent: >12} "
            f"GIB= {gib: >12} "
            f"Imag.Freqs= {imag: >2} "
        )
        if args.excel:
            sheet.append([
                file, '', #  place for comment on this file
                float(zpe),
                float(ten),
                float(ent),
                float(gib),
                imag
            ])
    if args.excel:
        wb.save(str(args.excel))


if __name__ == '__main__':

    main()
