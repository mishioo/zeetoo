# zeetoo

A collection of various Python scripts created as a help in everyday work in Team II IChO PAS.

- [backuper.py](#backuperpy)
    - [Geting Started](#getting-started)
    - [Graphical User Interface](#graphical-user-interface)
    - [Command Line Tool](#command-line-tool)
    - [Python API](#python-api)
- [confsearch.py](#confsearchpy)
- [fixgvmol.py](#fixgvmolpy)
- [gofproc.py](#gofprocpy)
- [sdf_to_gjf.py](#sdf_to_gjfpy)
- [License](#license)

## backuper.py

Simple Ptyhon script for scheduling and running automated files backup on Windows machines. Minimal graphical user interface included.

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
17. Save configuration file to specfied location.

After scheduling backup task configuration file should not be moved. It can be modified though, backup task will be done with this modified guidelines from now on. Scheduling new backup task, even using different configuration file, will override previous task, unless task_name in this file is specifically changed.

About conflicts solving mechanism: if file with the same name is already present in backup destination directory, action to conduct will be chosen depending on time of last modification of both, source and destination files.
- If source file is newer than backup version, the second will be overrieden.
- If both files have the same last modification time, file will not be copied.
- If backup version is newer, it will be renamed to oldname_last-modification-time.ext and source file will be copied, preserving both versions.

### Command Line Tool

Zeetoo backup functionality is available as command line tool. For more information run 'python backuper.py --help'.

### Python API

This section will be supplemented soon.

## confsearch.py

Performs a conformational search on set of given molecules. Requires RDkit software.

## fixgvmol.py

Adds mol version and END line to .mol files missing these pieces of information.

## gofproc.py

Extracts information about molecule energy from given set of Gaussian output files.

## sdf_to_gjf.py

Writes molecules contained in an .sdf file to a set of .gjf files.

# License

See the LICENSE.txt file for license rights and limitations (MIT).