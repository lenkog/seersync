"""
Utility methods for rsync.
"""
"""
Copyright (c) 2019 Lenko Grigorov.
This work is licensed under the 3-clause BSD License.
https://opensource.org/licenses/BSD-3-Clause
"""

import os
import re
from subprocess import Popen, PIPE
import sys

from .models import OperationType, SyncItem

_quietFlagPattern = re.compile(r'-[\w]*q[\w]*|--quiet')
_itemPattern = re.compile(r'([a-z\.]{4}) (.{11}) "(.*)"')


def indexOfRsync(args):
    """
    In a list of command-line arguments, finds the index of the first argument which refers to rsync.
    
    Args:
        args: a list of command-line arguments

    Returns:
        the index of the first argument which refers to rsync or -1 if no argument refers to rsync
    
    Examples:
    >>> indexOfRsync(['-b', 'rsync', '--help'])
    1
    
    >>> indexOfRsync(['-b', '/usr/bin/rsync', '--help'])
    1
    
    >>> indexOfRsync(['/usr/bin/rsync', 'rsync', '-v'])
    0
    
    >>> indexOfRsync(['-b', '--help', '-v'])
    -1
    """

    for i, arg in enumerate(args):
        if os.path.split(arg)[1] == 'rsync':
            return i
    return -1


def makeRsyncCmdLine(commandLine):
    """
    If needed, prefixes a list of command-line arguments with 'rsync' to make sure that this will be a call to rsync.

    Args:
        commandLine: a list of command-line arguments
        
    Returns:
        the same list of command-line arguments where 'rsync' is inserted in first position if needed
    
    Examples:
    >>> makeRsyncCmdLine(['rsync', '-v'])
    ['rsync', '-v']
    
    >>> makeRsyncCmdLine(['/usr/bin/rsync', '-v'])
    ['/usr/bin/rsync', '-v']
    
    >>> makeRsyncCmdLine(['-v'])
    ['rsync', '-v']
    
    >>> makeRsyncCmdLine(['-v', 'rsync'])
    ['rsync', '-v', 'rsync']
    
    >>> makeRsyncCmdLine([])
    ['rsync']
    """

    rsyncCommandLine = list(commandLine)
    if indexOfRsync(rsyncCommandLine) != 0:
        rsyncCommandLine.insert(0, 'rsync')
    return rsyncCommandLine


def hasQuietFlag(args):
    """
    Checks if the list of command-line arguments contains the rsync quiet flag, -q.
    
    Args:
        args: a list of command-line arguments
    
    Returns:
        True if the list contain the rsync quiet flag, -q; False otherwise
    
    Examples:
    >>> hasQuietFlag(['rsync', '-v'])
    False
    
    hasQuietFlag(['rsync', '-v', '-q'])
    True
    
    hasQuietFlag(['rsync', '-v', '--quiet'])
    True
    
    hasQuietFlag(['rsync', '-vq'])
    True
    """
    for arg in args:
        if _quietFlagPattern.match(arg):
            return True
    return False


def seeRsync(commandLine, itemCountCallback=None):
    """
    Calls rsync in dry-run mode with the given command line arguments and returns a list of changes that rsync would make.
    (No changes are applied by calling this function.)
    
    Optionally, a callback function can be provided which will be called every time a new item is received from rsync.
    The callback function should be able to receive a list of SyncItem elements.
    
    Args:
        commandLine: the rsync command line which will be executed in dry-run mode
        itemCountCallback: the callback which will be called whenever a new item is received from rsync; can be None
    
    Returns:
        the list of SyncItem elements parsed from the rsync output
    
    Note: If the command line contains the rsync quiet flag, -q, the rsync output will be suppressed
    and this function will not be able to detect any items.
    """
    return _readRsyncOutput(_startRsyncProcess(commandLine), itemCountCallback)


def _makeSeeRsyncCmdLine(commandLine):
    """
    Convert the rsync command line to ensure dry-run and output suitable for parsing.
    """
    seeRsyncCommandLine = makeRsyncCmdLine(commandLine)
    seeRsyncCommandLine.insert(1, '--out-format=%o %i \"%n\"')
    seeRsyncCommandLine.insert(1, '-n')
    return seeRsyncCommandLine


def _startRsyncProcess(commandLine):
    """
    Starts and returns the rsync process.
    """
    return Popen(_makeSeeRsyncCmdLine(commandLine), stdout=PIPE, universal_newlines=True)


def _readRsyncOutput(rsyncProcess, itemCountCallback=None):
    """
    Parses the output of the rsync process into a list of SyncItem elements.
    """
    with rsyncProcess:
        items = []
        for line in rsyncProcess.stdout:
            if itemCountCallback: itemCountCallback(items)
            line = line.strip()
            match = _itemPattern.match(line)
            # ignore irrelevant rsync output
            if not match:
                continue
            (op, info, file) = match.group(1, 2, 3)
            # rsync doesn't specify file type when deleting, use trailing slash to detect directories
            isDir = file[-1:] == '/' and (info[0] == '*' or info[1] == 'd')
            if op == 'send':
                if info[0] == '.' and info[2:] == '         ':
                    continue
                elif info[2:] == '+++++++++':
                    items.append(SyncItem(file, OperationType.create, isDir))
                else:
                    items.append(SyncItem(file, OperationType.update, isDir))
            elif op == 'del.':
                items.append(SyncItem(file, OperationType.delete, isDir))
            else:
                print('Cannot parse, skipping rsync item: ', line, file=sys.stderr)
        return items
