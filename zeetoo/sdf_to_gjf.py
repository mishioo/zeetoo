import argparse
import logging as lgg
import re
import pathlib


coords = re.compile(r'\s*(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*(\w\w?)')


def get_args(argv=None):
    prsr = argparse.ArgumentParser(
        description="Generate .gjf files from .sdf file."
    )
    prsr.add_argument('sdf', type=pathlib.Path, help="source .sdf file")
    prsr.add_argument('-o', '--out_dir', type=pathlib.Path, help="Path to output directory.")
    prsr.add_argument('-r', '--route', required=True, help="Calculations specification.")
    prsr.add_argument('-d', '--dscr', default='', help="Brief description of the calculation.")
    prsr.add_argument('-l', '--link', default='', help="space separated link-0 commands.")
    prsr.add_argument('-s', '--sufix', default='', help="Everything after molecule specification.")
    prsr.add_argument('-c', '--charge', required=True, type=int, help="Molecule charge.")
    prsr.add_argument('-m', '--multiplicity', required=True, type=int, help="Molecule spin multiplicity.")
    prsr.add_argument('-n', '--name', help='Core of output files names, it will be appended with [number].gjf')
    prsr.add_argument('-f', '--first_num', type=int, default=0, help='Number of first conformer.')
    return prsr.parse_args(argv)
    
    
def get_coords(file, line):
    match = coords.search(line)
    while match is not None:
        x, y, z, a = match.groups()
        yield a, float(x), float(y), float(z)
        match = coords.search(file.readline())


def get_molecules(source: pathlib.Path):
    with source.open() as sdf:
        for line in sdf:
            if coords.search(line) is not None:
                yield get_coords(sdf, line)
        
        
def save_molecule(
    dest: pathlib.Path, charge: int, multipl: int, coords: list, command: str,
    comment: str = '', prefix: str = '', sufix: str = ''
):
    with dest.open('w') as gjf:
        if prefix:
            gjf.write(prefix)
            gjf.write('\n')
        if not command.startswith('#'):
            command = '# ' + command
        gjf.write(command)
        gjf.write('\n\n')
        if comment:
            gjf.write(comment)
            gjf.write('\n\n')
        gjf.write('0 1\n')
        for a, x, y, z in coords:
            gjf.write(
                f" {a: <2} {x: > .7f} {y: > .7f} {z: > .7f}\n"
            )
        if sufix:
            gjf.write('\n')
            gjf.write(sufix)
        gjf.write('\n\n')
        

def main(argv: list = None):
    args = get_args(argv)
    args.out_dir.mkdir(exist_ok=True)
    gjfname = args.name if args.name is not None else args.sdf.stem
    out_dir = args.out_dir if args.out_dir is not None else args.sdf.parent
    for num, mol in enumerate(get_molecules(args.sdf)):
        output_file = args.out_dir / (gjfname + f'{num+args.first_num:0>3}.gjf')
        save_molecule(
            dest=output_file,
            charge=args.charge,
            multipl=args.multiplicity,
            coords=mol,
            command=args.route,
            comment=args.dscr,
            prefix=args.link,
            sufix=args.sufix
        )


if __name__ == '__main__':
    
    main()
    