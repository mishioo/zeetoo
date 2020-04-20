import argparse
import logging as lgg
import re
import pathlib
from typing import Tuple, Generator, Optional, TextIO, List

coords = re.compile(r"\s*(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*(\w\w?)")


def get_parser(argv=None):
    prsr = argparse.ArgumentParser(description="Generate .gjf files from .sdf file.")
    prsr.add_argument("sdf", type=pathlib.Path, help="Source .sdf file.")
    prsr.add_argument(
        "-o",
        "--out_dir",
        type=pathlib.Path,
        help=(
            "Path to output directory. If not given, evaluates to directory "
            "that given .sdf file resides in."
        ),
    )
    prsr.add_argument(
        "-r",
        "--route",
        required=True,
        help=(
            "Calculations specification. If given string doesn't start with "
            "'#' (pound symbol), it is prefixed with '# ' (pound symbol and space)."
        ),
    )
    prsr.add_argument(
        "-d",
        "--dscr",
        default="No additional information given.",
        help=(
            "A comment with brief description of the calculation job. "
            "Defaults to 'No additional information given.'."
        ),
    )
    prsr.add_argument(
        "-l",
        "--link",
        default="",
        help=(
            "List of link-0 commands. Each '%' character (percent sign) will be "
            "interpreted as a beginning of new a command. Defaults to empty string."
        )
    )
    prsr.add_argument(
        "-s",
        "--suffix",
        default="",
        help=(
            "Everything after molecule specification. This part will be written "
            "as-is, so it should use '\\n' as a new line character if suffix will "
            "span multiple lines. It is an empty string by default."
        ),
    )
    prsr.add_argument(
        "-c", "--charge", default=0, type=int, help="Molecule's charge, defaults to 0."
    )
    prsr.add_argument(
        "-m",
        "--multiplicity",
        default=1,
        type=int,
        help="Molecule's spin multiplicity, defaults to 1.",
    )
    prsr.add_argument(
        "-n",
        "--name",
        help=(
            'Base name of the output files, it will be appended with "[number].gjf". '
            "Defaults to base name of the .sdf file given."
        ),
    )
    prsr.add_argument(
        "-f",
        "--first_num",
        type=int,
        default=0,
        help=(
            "Number of the first conformer, defaults to 0. Numeration of resulting "
            "files will start at this number."
        ),
    )
    prsr.add_argument(
        "-p",
        "--precision",
        type=int,
        default=7,
        help=(
            "Desired floating point precision of coordinates as number of decimal "
            "digits. Must be a positive integer. Defaults to 7."
        ),
    )
    return prsr


def get_coords(file: TextIO, line: str) -> Tuple[str, float, float, float]:
    match = coords.search(line)
    while match is not None:
        x, y, z, a = match.groups()
        yield a, float(x), float(y), float(z)
        match = coords.search(file.readline())


def get_molecules(source: pathlib.Path) -> Generator[Tuple[str, float, float, float]]:
    with source.open() as sdf:
        for line in sdf:
            if coords.search(line) is not None:
                yield get_coords(sdf, line)


def save_molecule(
    dest: pathlib.Path,
    charge: int,
    multipl: int,
    coords: Tuple[str, float, float, float],
    route: str,
    comment: str = "",
    linkzero: List[str] = (),
    suffix: str = "",
    precision: int = 7
) -> None:
    with dest.open("w") as gjf:
        if linkzero:
            for cmd in linkzero:
                gjf.write(cmd)
        if not route.startswith("#"):
            route = "# " + route
        gjf.write(route)
        gjf.write("\n\n")
        if comment:
            gjf.write(comment)
            gjf.write("\n\n")
        gjf.write(f"{charge} {multipl}\n")
        for a, x, y, z in coords:
            gjf.write(
                f" {a: <2} "
                f"{x: > .{precision}f} "
                f"{y: > .{precision}f} "
                f"{z: > .{precision}f}\n"
            )
        if suffix:
            gjf.write("\n")
            gjf.write(suffix)
        gjf.write("\n\n")


def parse_link_zero(commands: str) -> List[str]:
    commands = commands.split("%")
    commands = [f"%{c.strip()}\n" for c in commands]
    return commands


def main(argv: Optional[list] = None) -> None:
    args = get_parser().parse_args(argv)
    if args.precision < 0:
        raise ValueError(
            f"Precision must be a positive integer, not {args.precision}."
        )
    gjfname = args.name if args.name is not None else args.sdf.stem
    out_dir = args.out_dir if args.out_dir is not None else args.sdf.parent
    out_dir.mkdir(exist_ok=True)
    start = args.first_num
    for num, mol in enumerate(get_molecules(args.sdf)):
        output_file = out_dir / f"{gjfname}{num+start:0>3}.gjf"
        save_molecule(
            dest=output_file,
            charge=args.charge,
            multipl=args.multiplicity,
            coords=mol,
            route=args.route,
            comment=args.dscr,
            linkzero=args.link,
            suffix=args.suffix,
            precision=args.precision,
        )


if __name__ == "__main__":

    main()
