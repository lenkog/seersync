"""
Main package of the seersync application.

This application calls rsync in dry-run mode and parses the output to list the
changes that would be made by rsync. The results can be viewed in a GUI or output
to stdout.

The 'main' function in the 'app' module is the entry point for the application. 
"""
"""
Copyright (c) 2019 Lenko Grigorov.
This work is licensed under the 3-clause BSD License.
https://opensource.org/licenses/BSD-3-Clause
"""

from ._version import __version__

