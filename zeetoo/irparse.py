import argparse
import pathlib
import itertools
import logging
import PyPDF2 as pypdf
from io import StringIO


def get_parser():
    prs = argparse.ArgumentParser(
        'Extract IR peaks from pdf files and write it as a list of signals to '
        'another file.'
    )
    prs.add_argument(
        'files', type=pathlib.Path, nargs='+',
        help='One or more text files with MS data to process or directories '
             'containing such files.'
    )
    prs.add_argument(
        '-o', '--output-file', type=pathlib.Path, default='irdata.txt',
        help='Output file. Defaults to [current-working-dir]/irdata.txt'
    )
    prs.add_argument(
        '-m', '--min-value', type=float, default=1000.0,
        help='Minimum wavenumber that will be considered significant. No lower '
             'values will be reported. Defaults to 1000.0.'
    )
    prs.add_argument(
        '-u', '--write_units', action='store_true',
        help='If given, units will be included in output.'
    )
    prs.add_argument(
        '-M', '--mode', type=str, default='a', choices=['a', 'w'],
        help='Mode of writing to output file "a" - append, "w" - override.'
    )
    prs.add_argument(
        '-V', '--verbose', action='store_true',
        help='Sets logging level to INFO.'
    )
    prs.add_argument(
        '-D', '--debug', action='store_true',
        help='Sets logging level to DEBUG.'
    )
    return prs


def get_text(file: pathlib.Path) -> StringIO:
    with file.open('rb') as handle:
        pdf = pypdf.PdfFileReader(handle)
        page = pdf.getPage(0)
        text = page.extractText()
    return StringIO(text)


def parse_pdf(handle, min_value=1000.0):
    for line in handle:
        if line == 'Sample name\n':
            name = next(handle)[:-1]
            break
    else:
        name = ''
    logging.debug('Sample name: %s', name or 'NOT FOUND')
    handle.seek(0)
    wavenums = (int(line[:-5]) for line in handle if line.endswith(' cm-1\n'))
    wavenums = [w for w in wavenums if w > min_value]
    logging.debug(
        'number of entries wavenumbers above trheshold: %s', len(wavenums)
    )
    return name, wavenums


def process_files(
        files,
        min_value=1000.0,
        write_units=False,
        output_file='irdata.txt',
        mode='a',
):
    with open(output_file, mode) as out:
        for file in files:
            logging.info('Working with file: %s', file)
            text = get_text(file)
            name, data = parse_pdf(text, min_value)
            out.write(name or file.name)
            out.write('\n')
            data = (f'{d}{" cm-1" if write_units else ""}' for d in data)
            out.write(', '.join(data))
            out.write('\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()
    if args.verbose:
        level = logging.INFO
    elif args.debug:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(level=level)
    logging.debug('args given: %s', vars(args))
    dirs = (path for path in args.files if path.is_dir())
    inner_files = (
        path for dir in dirs for path in dir.iterdir()
        if path.is_file() and path.suffix == '.pdf'
    )
    args_files = (
        path for path in args.files
        if path.is_file() and path.suffix == '.pdf'
    )
    items = list(itertools.chain(args_files, inner_files))
    logging.debug('got %s files to parse', len(items))
    process_files(
        items, args.min_value, args.write_units, args.output_file, args.mode
    )
    logging.info('Done.')


if __name__ == '__main__':
    main()
