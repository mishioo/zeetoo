# zeetoo

A collection of various Python scripts created as a help in everyday work in Team II IChO PAS.

- [Command Line Interface](#command-line-interface)
- [backuper](#backuper) - simple automated backup tool for Windows
    - [Geting Started](#getting-started)
    - [Graphical User Interface](#graphical-user-interface)
- [confsearch](#confsearch) - find conformers of given molecule using RDKit
- [fixgvmol](#fixgvmol) - correct .mol files created with GaussView software
- [getcdx](#getcdx) - extract all ChemDraw files embedded in .docx file
- [gofproc](#gofproc) - simple script for processing Gaussian output files
- [sdf_to_gjf](#sdf_to_gjf) - save molecules from .sdf file as separate .gjf files
- [Requirements](#requirements)
- [License](#license)

## Command Line Interface

All zeetoo functionality is available as command line tool. Each module can be accessed with use of `python [module_name] [parameters]`. For more information run `python zeetoo --help` or `python zeetoo [module_name] --help`.

## backuper

A simple Python script for scheduling and running automated files backup on Windows machines. Minimal graphical user interface included.

### Getting Started

To use this script you will need a Python 3 interpreter, you can download an installer of lastest version on [python.org](https://www.python.org) (a shortcut to direct download for Windows: [link](https://www.python.org/ftp/python/3.7.2/python-3.7.2.exe)). Please remember to check 'Add to PATH' during installation.
Next, download this script as zip file using 'Clone or download' button on this site. Unzip package to desired destination, for example 'C:/Program Files/zeetoo'. And that's it, you're ready to go.

### Graphical User Interface

To start up graphical user interface (GUI) dubble-click on start_gui.bat file. A window similar to this one should appear:

![screenshot](https://raw.githubusercontent.com/Mishioo/zeetoo/assets/screenshot.png)

1. This field shows path to backup's main directory. Files will be copied there. You can change this field directly or by clicking 2.
2. Choose backup destination directory using graphical interface.
3. All files and directories that are meant to be backuped are listed here. It will be called 'source' from now on. For more details read 4-7.
4. Add file or files to source. Files will be shown in 3 as line without slash caracter at the end. Each file will be copied to the directory of the same name as directory it is located in; in example shown above it would be 'x:\path_to\backup\destination\some_important\text_file.text'.
5. Add a directory to source. Directories will be shown in 3 as line with slash caracter at the end. All files (but not subdirectories!) present in this directory will be copied to directory with same name.
6. Add a directory tree to source. Trees will be shown in 3 as line with slash and star caracters at the end. The whole content of chosen directory will be copied, including all files and subdirectories.
7. Remove selected path from source.
8. All files and directories marked as ignored will be shown here. Ignored files and directories won't be copied during backup, even if they are inside source directory or tree, or listed as source.
9. Add file or files to ignored.
10. Add directory to ignored.
11. Remove selected item from list of ignored files and directories.
12. Set how often backup should be run (once a day, once a week or once a month) and at what time.
13. Schedule backup task according to specified guidelines. WARNING: this will also automatically save configuration file.
14. Remove backup task scheduled earlier.
15. Run backup task now, according to specified guidelines. Saving configuration to file not needed.
16. Load specified configuration file.
17. Save configuration file to specified location.

After scheduling backup task configuration file should not be moved. It can be modified though, backup task will be done with this modified guidelines from now on. Scheduling new backup task, even using different configuration file, will override previous task, unless task_name in this file is specifically changed.

About conflicts solving mechanism: if file with the same name is already present in backup destination directory, action to conduct will be chosen depending on time of last modification of both, source and destination files.
- If source file is newer than backup version, the second will be overridden.
- If both files have the same last modification time, file will not be copied.
- If backup version is newer, it will be renamed to oldname_last-modification-time.ext and source file will be copied, preserving both versions.

## confsearch

Performs a conformational search on set of given molecules.

## fixgvmol

.mol files created with GaussView (GV5 at least) lack some information, namely a mol version and END line. Without it some programs might not be able to read such files. This script adds these pieces of information to .mol files missing them.

## getcdx

Extracts all embedded ChemDraw files from a .docx document and saves it in a separate directory (which might be specified by user), using in-text description of schemes/drawings as file names. It may be specified if description of the scheme/drawing is located above or underneath it (the former is default). Finally, It may be specified how long filename should be.

## gofproc

Extracts information about molecule energy and imaginary frequencies from given set of Gaussian output files with *freq* job performed. Extracted data might be written to stdout or to specified .xlsx file at the end of the file or appended to a row, based on name of the file parsed. Calculations, that did not converged are reported separately.

## sdf_to_gjf

Writes molecules contained in an .sdf file to a set of .gjf files in accordance with the guidelines given by user.

# Requirements

- getcdx module requires olefile package
- gofproc module requires openpyxl package
- confsearch module requires RDKit software

Please note, that the RDKit **will not** be installed automatically with this package. The recommended way to get RDKit software is through use of Anaconda Python distribution. Please refer to RDKit documentation for more information.

# License

See the LICENSE.txt file for license rights and limitations (MIT).