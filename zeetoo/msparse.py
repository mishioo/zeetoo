import argparse
import pathlib
import itertools
import logging


def get_parser():
    prs = argparse.ArgumentParser(
        'Extract MS data from text files and write it as a list of signals to '
        'another file.'
    )
    prs.add_argument(
        'files', type=pathlib.Path, nargs='+',
        help='One or more text files with MS data to process or directories '
             'containing such files.'
    )
    prs.add_argument(
        '-o', '--output-file', type=pathlib.Path, default='msdata.txt',
        help='Output file. Defaults to [current-working-dir]/msdata.txt'
    )
    prs.add_argument(
        '-t', '--threshold', type=float, default=10,
        help='Threshold of signal strength as percent of highest peak '
             'intensity. Signals below this threshold will be ignored. '
             'Defaults to 10%%.'
    )
    prs.add_argument(
        '-m', '--max-value', type=float, default=float('inf'),
        help='Maximum m/z value that will be considered significant. No higher '
             'values will be reported. Defaults to infinity.'
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


def parse_txt(handle, threshold, max_value=float('inf')):
    mzs, inten = zip(*(map(float, line.split()) for line in handle if line))
    logging.debug('number of entries in file: %s', len(mzs))
    maximum = max(inten)
    logging.debug('maximum intensity %s', maximum)
    percent = (i/maximum for i in inten)
    output = [
        mz for mz, p in zip(mzs, percent) if p >= threshold and mz <= max_value
    ]
    logging.debug('number of signals filtered: %s', len(output))
    return output


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
        if path.is_file() and path.suffix == '.txt'
    )
    args_files = (
        path for path in args.files
        if path.is_file() and path.suffix == '.txt'
    )
    items = list(itertools.chain(args_files, inner_files))
    logging.debug('got %s files to parse', len(items))
    with open(args.output_file, 'a') as out:
        for file in items:
            logging.info('Working with file: %s', file)
            with open(file, 'r') as msfile:
                data = parse_txt(msfile, args.threshold / 100, args.max_value)
                out.write(file.name)
                out.write('\n')
                out.write(', '.join(map(str, data)))
                out.write('\n\n')
    logging.info('Done.')


if __name__ == '__main__':
    main()
