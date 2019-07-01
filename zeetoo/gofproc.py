import openpyxl as opxl
import re
import argparse
from itertools import chain
from pathlib import Path
import logging as lgg

number_group = r'\s*(-?\d+\.?\d*)'
number = number_group.replace('(', '').replace(')', '')
energies = re.compile(
    r' Zero-point correction=\s*(-?\d+\.?\d*) \(Hartree/Particle\)\n'
    r' Thermal correction to Energy=\s*(-?\d+\.?\d*)\n'
    r' Thermal correction to Enthalpy=\s*(-?\d+\.?\d*)\n'
    r' Thermal correction to Gibbs Free Energy=\s*(-?\d+\.?\d*)\n'
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
        help='One or more gaussian output files or directories with such.'
    )
    prs.add_argument(
        '-f', '--file', type=Path, default=None,
        help='Wries output to specified excel file.'
    )
    prs.add_argument(
        '-s', '--silent', action='store_true',
        help='Suppress printing to sdtout.'
    )
    prs.add_argument(
        '-c', '--corrections', action='store_true',
        help='Include corrections in the output.'
    )
    prs.add_argument(
        '-i', '--imag_count', action='store_true',
        help='Include number of imaginary numbers in the output.'
    )
    prs.add_argument(
        '-e', '--energies', action='store_true',
        help='Include energies values in the output.'
    )
    return prs.parse_args(argv)


def get_data(path):
    with path.open('r') as file:
        text = file.read()
    ens = energies.search(text)
    freqs = frequencies.findall(text)
    if not ens or not freqs:
        lgg.info(f'NOT CONVERGED: {path.name}')
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
    if args.file:
        wb = opxl.load_workbook(str(args.file))
        sheet = wb.active
    for file, zcr, tcr, ecr, gcr, zpe, ten, ent, gib, imag in data:
        entries = []
        # entry: name, value, width
        if args.energies:
            entries.append(("ZPE", float(zpe)))
            entries.append(("TEN", float(ten)))
            entries.append(("ENT", float(ent)))
            entries.append(("GIB", float(gib)))
        if args.corrections:
            entries.append(("ZPECORR", float(zcr)))
            entries.append(("TENCORR", float(tcr)))
            entries.append(("ENTCORR", float(ecr)))
            entries.append(("GIBCORR", float(gcr)))
        if args.imag_count:
            entries.append(("Imag.Freqs", int(imag)))
        if entries:
            lgg.info(
                ' '.join((
                    f"{file: <{length}} -",
                    *("{}= {}".format(*e) for e in entries)
                ))
            )
        if entries and args.file:
            sheet.append([
                file, '',  # place for comment on this file
                *(e[1] for e in entries)
            ])
    if args.file:
        wb.save(str(args.file))


if __name__ == '__main__':

    main()
