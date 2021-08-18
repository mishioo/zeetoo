import argparse
import re
import csv
import codecs
import logging
from collections import defaultdict, OrderedDict
import tkinter as tk
import io
import traceback
import sys


logger = logging.getLogger(__name__)


class App(tk.Tk):
    def __init__(self, indent, sep, labels, environment):
        super().__init__()
        self.title("Tex-ify analyses")

        self.indent = indent
        self.sep = sep
        self.labels = labels
        self.environment = environment

        inframe = tk.LabelFrame(self, text="Paste in analyses here")
        inframe.pack(expand=True, fill=tk.BOTH, side=tk.TOP)
        outframe = tk.LabelFrame(self, text="Tex-ifyed for copy")
        outframe.pack(expand=True, fill=tk.BOTH, side=tk.TOP)

        self.intext = tk.Text(inframe)
        self.intext.pack(expand=True, fill=tk.BOTH, side=tk.TOP)

        self.outtext = tk.Text(outframe)
        self.outtext.pack(expand=True, fill=tk.BOTH, side=tk.TOP)

        tk.Button(self, text="Tex-ify", command=self._parse).pack(expand=True, fill=tk.X, side='left')
        tk.Button(self, text="Automatic", command=self._auto).pack(expand=True, fill=tk.X, side='left')
        tk.Button(self, text="Copy", command=self._copy).pack(expand=True, fill=tk.X, side='left')

        self._error = None

    def _auto(self):
        text = self.selection_get(selection = "CLIPBOARD")
        self.intext.delete('1.0', 'end')
        self.intext.insert('1.0', text)
        self._parse()
        if not self._error:
            self._copy()

    def _parse(self):
        self._error = None
        text = self.intext.get('1.0', 'end')
        try:
            data = parse_molecule(text)
            # data['label'] = self.labels[data['id']]
            text = format_latex(data, self.sep, self.indent, self.environment)
        except Exception as error:
            self._error = error
            exc_type, exc_value, exc_traceback = sys.exc_info()
            reason = traceback.format_exception(exc_type, exc_value, exc_traceback)
            text = f"CANNOT PARSE INPUT DATA\n\nReason:\n{''.join(reason)}"
        self.outtext.delete('1.0', 'end')
        self.outtext.insert('1.0', text)

    def _copy(self):
        text = self.outtext.get('1.0', 'end')
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()


prsr = argparse.ArgumentParser()
prsr.add_argument(
    "-g", "--gui", action="store_true",
    help="Start GUI mode"
)
prsr.add_argument(
    "source", type=str, default="", nargs='?',
    help="Source file. Required if not starting GUI mode."
)
prsr.add_argument("dest", type=str, default="./analyses.tex", nargs='?')
prsr.add_argument("-s", "--sep", type=str, default="; ")
prsr.add_argument("-i", "--indent", type=str, default="\t")
prsr.add_argument(
    "-e", "--environment", type=str, default="experimental", nargs='?',
    help="Name of environment wrapping analyses definitions. "
    "If evoked without value, environment is not added at all."
)
prsr.add_argument(
    "-n", "--namesfile", type=str,
    help="File containing pairs of cmpd's symbol and in-latex label in csv format."
)
verbosity = prsr.add_mutually_exclusive_group()
verbosity.add_argument(
    '--verbose', action='store_true',
    help='Print more informations to stdout.'
)
verbosity.add_argument(
    '--debug', action='store_true',
    help='Print debug logs to stdout.'
)
verbosity.add_argument(
    '--silent', action='store_true',
    help='Only errors are displayed.'
)


number = r"-?\d+(?:\.\d+)?"
decimal = r"-?\d+\.\d+"
decimalrange = decimal + r"(?: ?[-–,] ?" + decimal + ")?"
numsrange = number + r"(?: ?[-–,] ?" + number + ")?"
coupling = r"\((\w+)(?:, ?J ?= ?(.*?))?(?:, ?(\d+)\w+)\)"
hnmrshifts = "(" + decimalrange + ") ?" + coupling
rotpatt = "(?P<value>" + number + r") \(c ?= ?(?P<conc>" + decimal + r"), solv. (?P<solvent>[\w\d]+)\)"


def _parse_nmr(text, values_regex):
    match = re.match(r"(\d+\w+ NMR) \((\d+) ?(?:MHz)?, ?([\d\w]+)\)", text)
    analysis, frequency, solvent = match.groups()
    values = re.findall(values_regex, text)
    if not values:
        raise ValueError("Unable to find any data.")
    data = {
        "frequency": frequency,
        "solvent": solvent,
        "values": values,
    }
    return data


def parse_coupled_nmr(text):
    return _parse_nmr(text, hnmrshifts)


def parse_uncoupled_nmr(text):
    return _parse_nmr(text, decimal)


def parse_ir(text):
    if not text.lower().startswith("ir"):
        raise ValueError("Should start with 'IR'.")
    data = {
        "method": re.search(r"\((.*?)\)", text).group(1),
        "values": re.findall(r"(\d{3,4})(?: cm-1)?", text),
    }
    return data


def parse_ms(text):
    if not text.lower().startswith("hrms"):
        raise ValueError("Should start with 'HRMS'.")
    data = {
        "method": re.search(r"\((.*?)\)", text).group(1),
        "found": re.search(r"found.*?(" + number + ")", text).group(1),
        "calcd": re.search(r"cal(?:culate)?d.*?(" + number + ")", text).group(1),
        "formula": re.search(r"for ([\w\d]*)", text).group(1),
    }
    return data


def parse_rotation(text):
    data = re.search(rotpatt, text).groupdict()
    return data


def parse_melting(text):
    if not text.lower().startswith("m.p."):
        raise ValueError("Should start with 'm.p.'.")
    return {"value": re.search(r"(" + numsrange + ")", text).group(0)}
    

def parse_yield(text):
    match = re.search(r"(\d+)%?, ([\w\s]+)", text)
    return match.groups()


RESOLUTION_ORDER = OrderedDict([
    ("hnmr", parse_coupled_nmr),
    ("cnmr", parse_uncoupled_nmr),
    ("rotation", parse_rotation),
    ("ir", parse_ir),
    ("ms", parse_ms),
    ("yield_form", parse_yield),
    ("melting", parse_melting),
])


def _trim_line(line):
    if len(line) > 25:
        return line[:25] + "..."
    else:
        return line


def parse_molecule(text):
    """Parses analyses in arbitrary order.
    Expects one analysis per line in same format as `read_molecule()`.
    """
    data = {}
    lines = text.split("\n")
    for line in lines:
        if not line:
            continue
        for key, func in RESOLUTION_ORDER.items():
            try:
                data[key] = func(line)
            except Exception as error:
                continue  # next key (inner loop)
            else:
                logger.debug(f"{key} MATCHED '{_trim_line(line)}'.")
                break  # go to next line (outer loop)
        else:  # no match
            logger.debug(f"nothing found in '{_trim_line(line)}'.")
    if "yield_form" in data:
        data["yield"], data["form"] = data["yield_form"]
        del data["yield_form"]
    return data


def read_molecule(handle):
    """Reads one molecule data from file or file-like object. Expects one analysis
    per line in this format and order:

    <molecule identifier>
    <molecule IUPAC name>
    1H NMR (<frequency>[ MHz], <solvent>)[ = ][comma sep. list of
        <value> (<peaktype>, [J=list of <coup.const.>, ]<num.protons>H)]
    13C NMR (<frequency>[ MHz], <solvent>)[ = ][comma sep. list of <value>]
    IR (<method>)[comma sep. list of <value>[cm-1]]
    """
    data = {}
    line = None
    while not line:
        rawline = handle.readline()
        if not rawline:
            raise EOFError
        line = rawline.strip()
    logger.info(f"Parsing compound '{line}'.")
    data["id"] = line
    data["name"] = handle.readline().strip()
    data["yield"], data["form"] = parse_yield(handle.readline().strip())
    data["hnmr"] = parse_coupled_nmr(handle.readline().strip())
    data["cnmr"] = parse_uncoupled_nmr(handle.readline().strip())
    data["ir"] = parse_ir(handle.readline().strip())
    data["ms"] = parse_ms(handle.readline().strip())
    data["rotation"] = parse_rotation(handle.readline().strip())
    nextline = handle.readline().strip()
    if nextline:
        data["melting"] = parse_melting(nextline)
    return data


def format_iupac(name):
    name = re.sub(  # substitute Cahn-Ingol-Prelog descriptors
        r"\((\d*[\'\"]?\w?(?:R|S)[\d\w, \'\"]*?)\)",
        r"\\cip{\1}",
        name
    )  # only those wrapped in parentheses are substituted
    # TODO: make it handle non-parenthesized descriptors
    name = re.sub(  # substitute easily replaced specifiers
        "\\b(\\d*)(H|O|N|P|D|L|Z|E|tert|sec|cis|trans|fac|mer|sin|ter|syn|anti)\\b",
        r"\1\\\2",
        name
    )
    name = re.sub(r"\\b(\\d*)S\\b", r"\1\\Sf", name)  # for sulphur
    name = re.sub(r"(\\)?\'", r"\\chemprime", name)  # for apostrophes
    name = re.sub(r"(\\)?\"", r"\\chemprime\\chemprime", name)  # for apostrophes
    # TODO: add greek letters
    return f"\\iupac{{{name}}}"


def format_values(values):
    vals = re.findall(number, values)  # shift values
    if len(vals) > 1 and "," in values:
        vals = f"\\numlist{{{';'.join(vals)}}}"
        # using spectroscopy: vals = ", ".join(f"\\val{{{v}}}" for v in vals)
    elif len(vals) == 2:
        vals = f"\\numrange{{{vals[0]}}}{{{vals[1]}}}"
        # using spectroscopy: vals = f"\\val{{{'--'.join(vals)}}}"
    else:
        vals = f"\\num{{{vals[0]}}}"
        # using spectroscopy: vals = f"\\val{{{vals[0]}}}"
    return vals


def format_hnmr(data):
    vals = format_values(data[0])
    vals += f" ({data[1]}, "  # peak type
    if data[2]:
        jconsts = re.findall(decimal, data[2])  # coupling constants
        vals += f"\\J{{{';'.join(jconsts)}}}, "
    vals += f"\\#{{{data[3]}}})"  # num of nuclei
    return vals


FORMATTERS = OrderedDict([
    ("name",
        lambda data: f"{format_iupac(data['name'])} ({data['label']})  % {data['id']}"
    ),
    ("yield",
        lambda data: f"\\data*{{yield}} \\SI{{{data['yield']}}}{{\\percent}} ({data['form']})"
    ),
    ("melting",
        lambda data: f"\\data{{mp.}} {format_values(data['melting']['value'])}\\si{{\\celsius}}"
    ),
    ("rotation",
        lambda data: f"\\data{{specific rot.}} \\num{{{data['rotation']['value']}}} "
        f"($c = {data['rotation']['conc']}$, "
        f"\\ch{{{data['rotation']['solvent']}}})"
    ),
    ("hnmr",
        lambda data: f"\\NMR({data['hnmr']['frequency']})[{data['hnmr']['solvent']}] "
        + ", ".join([format_hnmr(v) for v in data['hnmr']['values']])
    ),
    ("cnmr",
        lambda data: f"\\NMR{{13,C}}({data['cnmr']['frequency']})[{data['cnmr']['solvent']}] "
        + f"\\numlist{{{'; '.join([f'{float(n):.1f}' for n in data['cnmr']['values']])}}}"
    ),
    ("ir",
        lambda data: f"\\data{{IR}}[{data['ir']['method']}] "
        + f"\\numlist{{{'; '.join(data['ir']['values'])}}}"
    ),
    ("ms",
        lambda data: f"\\data{{HRMS}} ({data['ms']['method']}) m/z calcd for \\ch{{{data['ms']['formula']}}}: "
        f"\\num{{{data['ms']['calcd']}}} found: \\num{{{data['ms']['found']}}}"
    ),
])


def format_latex(data, sep=";", indent="\t", environment="experimental"):
    joint = f"{sep}\n{indent}"
    latex_list = [fmt(data) for key, fmt in FORMATTERS.items() if key in data]
    latex = joint.join(latex_list)
    if not environment:
        return latex
    return f"\\begin{{{environment}}}\n{indent}{latex}\n\\end{{{environment}}}"
    

def get_labels(
    labelsfile=None, 
    lblfmt="\\refcmpd{{{}}}", 
    prefmt="\\textbf{{{}}}", 
    postfmt="\\textbf{{{}}}",
    separator="",
):
    labels = defaultdict(lambda: "")
    formatters = (lblfmt, prefmt, postfmt)
    if labelsfile is not None:
        with open(labelsfile, "r", newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            for id_, *args in csvreader:
                formatted = [
                    fmt.format(part) for part, fmt in zip(args, formatters)
                ]
                if len(formatted) > 1:
                    formatted[0], formatted[1] = formatted[1], formatted[0]
                labels[id_] = separator.join(formatted)
    return labels


def main():
    args = prsr.parse_args()
    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    elif args.silent:
        level = logging.ERROR
    else:
        level = logging.WARNING
    logging.basicConfig(level=level)
    labels = get_labels(args.namesfile)
    if args.gui:
        root = App(
            sep=args.sep,
            indent=args.indent,
            labels=labels,
            environment=args.environment,
        )
        root.mainloop()
        return
    elif not args.source:
        prsr.error("Argument 'source' is required.")
    with open(args.dest, 'w') as dest:
        with codecs.open(args.source, encoding="utf-8") as source:
            while True:
                try:
                    data = read_molecule(source)
                except EOFError:
                    logger.info("No more data found.")
                    break
                data['label'] = labels[data['id']]
                dest.write(format_latex(data, args.sep, args.indent, args.environment))


if __name__ == '__main__':
    main()
