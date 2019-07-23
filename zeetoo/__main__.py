import argparse
import importlib
import pathlib
import sys


def get_parser(available_modules):
    prs = argparse.ArgumentParser(
        prog='zeetoo',
        description=f'A collection of various python scripts for use in '
                    f'Team II IOC PAS. Modules available: '
                    f'{", ".join(available_modules)}. For information '
                    f'regarding specific module run "%(prog)s MODULE -h".',
        usage='%(prog)s [-h] MODULE [options_for_module]'
    )
    prs.add_argument(
        'module', choices=available_modules, metavar='MODULE',
        help='Module to run.'
    )
    return prs


def main():
    directory = pathlib.Path(__file__).resolve().parent
    modules = [
        f.stem for f in directory.glob('*.py') if not f.stem.startswith('_')
    ]
    validator = get_parser(modules)
    _, module, *other = sys.argv
    args = validator.parse_args([module])
    module = args.module
    module = importlib.import_module(module)
    module.main(other)


if __name__ == '__main__':

    main()
