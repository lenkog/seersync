# seersync

Seersync is an application which can list the changes that a particular run of rsync would make.
The application can work in GUI mode or in batch mode via the command line. Seersync itself does
not make any changes. It uses the dry-run mode of rsync and then lets the user preview the collected
information. Generally, arbitrary rsync command lines are supported with the exception of
command lines which contain the quiet flag, `-q`. The rsync output is fully suppressed when the
quiet flag is used and seersync cannot operate correctly in such situations.

*Note that the information in seersync represents only a snapshot. If the file system gets modified
after running seersync, the list shown may no longer represent correctly what would happen when rsync
gets executed.*

Seersync is only tested on a Linux system. However, the application is written in Python 3 and may
be able to function correctly on other systems where Python 3 and rsync are available.

## Installation

To install and use seersync, you need to have Python3 on your system. Then from the command line you
can run:
```
pip install seersync
```
Note: On some systems you may need to call `pip3` instead of `pip`.

## Launching

To launch seersync, from the command line run:
```
seersync
```
or
```
python -m seersync
```
Note: On some systems you may need to call `python3` instead of `python`.

The `pyqt5` package is needed to launch the seersync GUI. If this package is not available on your
system, you can still use seersync in batch mode.

## Using the GUI

Follow these steps:
1. Launch seersync.
2. Enter the desired rsync command line in the "Command line" text field.
3. Click the "Check" button.
4. Explore the list of changes that rsync would make in the bottom half of the screen.

![(Screenshot of the seersync GUI)](screenshot.png)

## Passing the rsync command line

Let us assume that we want to check what changes the command `rsync -a src_folder dst_folder` would
make. As an alternative to entering the command manually in the GUI, it is possible to pass the
desired rsync command line when launching seersync in one of two ways.

### Pass the rsync command line as arguments to seersync

The full rsync command line can be specified directly as arguments to seersync. 
```
seersync rsync -a src_folder dst_folder
```

### Read the rsync command line from a file

The desired rsync command can be also saved in a file. For example, we can create a file called
`rsync.txt` with the following content:
```
# An example input file for seersync
rsync -a src_folder dst_folder
```
Then, we can call seersync and specify this file as input.
```
seersync -i rsync.txt
```

Seersync interprests lines that start with the `#` character as comments. The first line which is not
a comment is assumed to contain the rsync command line.

## Batch mode

In addition to the GUI, seersync offers batch mode which is useful for integration with other tools
when creating scripts. To run seersync in batch mode, pass the `-b` option. Make sure that the batch
option appers before the start of the rsync command line arguments.
```
seersync -b rsync -a src_folder dst_folder
```

The output of seersync will be a plain list inspired by the short format of the Git status command.
Each line will start with a letter indicating the type of change, followed by the path.

The letter will be one of `A`, `M` and `D`.
- `A` indicates that the path is a new file or folder created at the destination.
- `M` indicates that the file or folder at the destination exists but will be updated.
- `D` indicates that the file or folder at the destination will be removed.

If the path contains a slash at the end, it indicates that this is a folder.

The following is an example output when seersync is run in batch mode.
```
M ./
M modified dir/
M modified dir/nested modified file
A modified dir/nested new file
D modified dir/nested surplus file
M modified file
M modified link
A new dir/
A new file
A new link
D surplus dir/
D surplus file
D surplus link
```

In batch mode, seersync checks automatically for the presence of the quiet flag, `-q`, in the rsync
command line and will exit with an error if it detects the flag. If this behavior is undesirable,
for example, if the detection algorithm results in a false positive, one can pass the
`--skip-detect-quiet` to seersync.
```
seersync -b --skip-detect-quiet rsync ...
```

## Command line options

`-h` or `--help` print command line help and exit

`-i INPUT_FILE` read the rsync command line from INPUT_FILE

`-b` run in batch mode, without opening GUI

`--progress` display the progress of operation (batch mode only)

`--version` print version and exit

`--skip-detect-quiet` do not check if the rsync command line contains the quiet flag -q (batch mode only)

## License

Seersync is licensed under the 3-clause BSD license.
