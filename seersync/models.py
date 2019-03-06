"""
Data models for seersync.
"""
"""
Copyright (c) 2019 Lenko Grigorov.
This work is licensed under the 3-clause BSD License.
https://opensource.org/licenses/BSD-3-Clause
"""

from enum import Enum


class OperationType(Enum):
    """
    Enumeration of rsync operation types.
    
    "create"    the item does not exist at the destination and will be created
    "update"    the existing item at the destination will be updated
    "delete"    the existing item at the destination will be deleted 
    """

    create = 1
    update = 2
    delete = 3

    def __lt__(self, other):
        return self == OperationType.create and other != OperationType.create \
             or self == OperationType.update and other == OperationType.delete


class SyncItem:
    """
    An item reported by rsync.
    
    Attributes:
        path: the path of the item
        operation: the type of operation (instance of OperationType)
        isDir: is the item a directory
    """

    def __init__(self, path, operation, isDir):
        self.path = path
        self.operation = operation
        self.isDir = isDir
