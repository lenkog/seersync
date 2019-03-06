"""
Main module of the seersync application.

The 'main' function is the entry point for the application. 
"""
"""
Copyright (c) 2019 Lenko Grigorov.
This work is licensed under the 3-clause BSD License.
https://opensource.org/licenses/BSD-3-Clause
"""

import argparse
import shlex
import sys
import time

from . import rsync
from . import ui
from ._version import __version__
from .models import OperationType

_CONFIG = {
    'opSymbol': {
        OperationType.create: 'A',
        OperationType.update: 'M',
        OperationType.delete: 'D'
    },
}

_timeLastCountRefresh = 0


def _printBatchProgress(items, force=False):
    global _timeLastCountRefresh
    # pace the status update
    # use absolute value to guard against clock adjustments
    if force or abs(time.time() - _timeLastCountRefresh) >= 1:
        _timeLastCountRefresh = time.time()
        print('\rCollecting information from rsync... ({} items received)'.format(len(items)), end='', flush=True)


def main(argv=None):
    """
    Entry point to the application.
    
    Optionally pass an array with the desired command line arguments.
    If no arguments are passed, they will be read from the real command line.
    
    For an overview of acceptable parameters, call this method with '--help' as an argument.
    
    Args:
        argv: the command line arguments of the application 
    """

    parser = argparse.ArgumentParser(description='List the changes that rsync would make if a given rsync command line gets executed.',
                                     usage='seersync [options] [rsync [rsyncArg ...]]')
    parser.add_argument('-i', dest='inputFile', help='rsync command line is read from the specified file')
    parser.add_argument('-b', dest='batchMode', action='store_true', help='run in batch mode, without opening GUI')
    parser.add_argument('--progress', action='store_true', help='display the progress of operation (batch mode only)')
    parser.add_argument('--version', action='store_true', help='print version and exit')
    parser.add_argument('--skip-detect-quiet', dest='skipDetectQuiet', action='store_true', help='do not check if the rsync command line contains the quiet flag -q (batch mode only)')

    if argv is None:
        ourArgv = sys.argv[1:]
    else:
        ourArgv = argv

    rsyncIdx = rsync.indexOfRsync(ourArgv)
    # "rsync" could also be passed as the name of the input file
    if rsyncIdx > 0 and ourArgv[rsyncIdx - 1] == '-i':
        nextRsyncIdx = rsync.indexOfRsync(ourArgv[rsyncIdx + 1:])
        if nextRsyncIdx >= 0:
            rsyncIdx = rsyncIdx + 1 + nextRsyncIdx

    if rsyncIdx >= 0:
        rsyncCommandLine = ourArgv[rsyncIdx:]
        ourArgv = ourArgv[:rsyncIdx]
    else:
        rsyncCommandLine = []

    args = parser.parse_args(ourArgv)

    if args.version:
        print('seersync ' + __version__)
        return

    if args.inputFile:
        commandLine = ''
        try:
            with open(args.inputFile, 'r') as inputFile:
                for line in inputFile.readlines():
                    if not line.startswith('#'):
                        commandLine = line
                        break
        except:
            print('Error:\tCannot read file:', args.inputFile, infile=sys.stderr)
            sys.exit(8)
        rsyncCommandLine = shlex.split(commandLine)

    rsyncCommandLine = rsync.makeRsyncCmdLine(rsyncCommandLine)

    if not args.batchMode:
        ui.launch(rsyncCommandLine)
    else:
        print('rsync command line: ', ' '.join(rsyncCommandLine), file=sys.stderr)
        if not args.skipDetectQuiet and rsync.hasQuietFlag(rsyncCommandLine):
            print(file=sys.stderr)
            print('Error:\tThe quiet flag, -q, is detected in the rsync command line.', file=sys.stderr)
            print('\tseersync cannot operate correctly if rsync output is suppressed.', file=sys.stderr)
            print('\tRemove the flag or run seersync with the --skip-detect-quiet option.', file=sys.stderr)
            print(file=sys.stderr)
            sys.exit(4)

        if args.progress:
            progressCallback = _printBatchProgress
        else:
            progressCallback = None

        items = rsync.seeRsync(rsyncCommandLine, progressCallback)

        if progressCallback == _printBatchProgress:
            _printBatchProgress(items, force=True)
            print()

        items = sorted(items, key=lambda item: item.path)
        for item in items:
            print(_CONFIG['opSymbol'][item.operation], item.path)

