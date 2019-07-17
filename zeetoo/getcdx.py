import argparse
import logging
import olefile
import pathlib
import zipfile
try:
    from xml.etree.cElementTree import XML
except ImportError:
    from xml.etree.ElementTree import XML

REL = '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'
OLEREL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject'
RELID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
OLEOBJ = '{urn:schemas-microsoft-com:office:office}OLEObject'
WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
PAR = WORD_NAMESPACE + 'p'
TXT = WORD_NAMESPACE + 't'


def get_ole_rels(ziphandle):
    """Returns a dictionary of embedded objects Ids (keys) and locations
    (values)."""
    tree = XML(ziphandle.read("word/_rels/document.xml.rels"))
    rels = {
        a['Id']: a['Target'] for a in
        (e.attrib for e in tree.iter(REL))
        if a['Type'] == OLEREL
    }
    return rels


def find_embeddings(ziphandle, title_first=False):
    """Yields two-element tuple with OLEObject element and paragraph element
    if OLEObject found is a ChemDraw file."""
    tree = XML(ziphandle.read('word/document.xml'))
    embedding, paragrph = None, None
    for elem in tree.iter():
        # yield only if object embedded is ChemDraw file
        if elem.tag == OLEOBJ and elem.attrib['ProgID'].startswith('ChemDraw'):
            embedding = elem
            if title_first:
                # paragraph should be already known so yield and reset
                yield (embedding, paragrph)
                embedding = None
        elif elem.tag == PAR:
            paragrph = elem
            if embedding is not None and not title_first:
                # yield and reset only if embedding found
                yield (embedding, paragrph)
                embedding = None
        else:
            continue


def extract_embeddings(
        path: pathlib.Path, out: pathlib.Path, words_in_name: int = 5,
        title_first: bool = False
             ):
    """Opens a .docx file given in `path`, reads all embedded ChemDraw
    objects and writes them to `out` directory, using first `words_in_name`
    words of the first paragraph after object (or the one directly before,
    if `title_first` is True) as the file name."""
    with zipfile.ZipFile(path) as ziphandle:
        rels = get_ole_rels(ziphandle)
        for embedding, paragraph in find_embeddings(ziphandle, title_first):
            embedded_file = 'word/' + rels[embedding.attrib[RELID]]
            text = [node.text for node in paragraph.iter(TXT) if node.text]
            text = ''.join(text)
            title = ' '.join(text.split()[:words_in_name])
            ole = ziphandle.read(embedded_file)
            with olefile.OleFileIO(ole) as ole_handle:
                content = ole_handle.openstream('CONTENTS').read()
            outfile = out / (title + '.cdx')
            with outfile.open('wb') as out_handle:
                out_handle.write(content)


def get_parser():
    prs = argparse.ArgumentParser('Extract .cdx files from a .docx file.')
    prs.add_argument(
        'file', type=pathlib.Path, help='.docx file with .cdx files embedded.'
    )
    prs.add_argument(
        '-o', '--output-dir', type=pathlib.Path,
        help='Output directory. Defaults to [file-location]/[file-name]-cdx/'
    )
    prs.add_argument(
        '-w', '--words', type=int, default=5,
        help='Number of words included in name of .cdx file.'
    )
    prs.add_argument(
        '-p', '--preceding-title', action='store_true',
        help='Look for scheme description before the scheme.'
    )
    return prs


def main(argv=None):
    logging.basicConfig(level='DEBUG')
    prs = get_parser()
    args = prs.parse_args(argv)
    outdir = args.output_dir or args.file.parent / (args.file.stem + '-cdx')
    outdir.mkdir(exist_ok=True)
    extract_embeddings(args.file, outdir, args.words, args.preceding_title)


if __name__ == "__main__":
    main()
