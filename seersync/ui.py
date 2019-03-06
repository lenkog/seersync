"""
Implementation of the seersync GUI.

The 'launch' function is used to open the GUI. 
"""
"""
Copyright (c) 2019 Lenko Grigorov.
This work is licensed under the 3-clause BSD License.
https://opensource.org/licenses/BSD-3-Clause
"""

from PyQt5.Qt import QAbstractTableModel, QVariant, Qt, QFont, QBrush, QColor, \
    QSize, QThread, pyqtSignal, QApplication, QLabel, QWidget, QVBoxLayout, \
    QHBoxLayout, QPushButton, QTableView, QHeaderView, QPlainTextEdit
import shlex
import time

from . import rsync
from ._version import __version__
from .models import OperationType

_CONFIG = {
    'columnTitle': {
        0: QVariant('Operation'),
        1: QVariant('Path')
    },
    'columnAlign': {
        0: Qt.AlignCenter,
        1: None
    },
    'columnFont': {
        0: QFont(),
        1: None
    },
    'opSymbol': {
        OperationType.create: '\u22c6',
        OperationType.update: '\u290f',
        OperationType.delete: '\u00d7'
    },
    'rowBackground': {
        OperationType.create: QBrush(QColor(240, 255, 240)),
        OperationType.update: QBrush(QColor(240, 248, 255)),
        OperationType.delete: QBrush(QColor(255, 228, 225))
    },
    'warnLabelStyle': 'QLabel { color: #ff4500 }',
    'dirSymbol': '\U0001f5c1 ',
    'fileSymbol': ' \U0001f5ce  ',
}
_CONFIG['columnFont'][0].setPointSize(18)


class _ItemsTableModel(QAbstractTableModel):

    def __init__(self):
        super().__init__()
        self.items = []
        self.sortByCol = 0
        self.sortReverse = False

    def setItems(self, items):
        self.layoutAboutToBeChanged.emit()
        self.items = list(items)
        self.sortItems()
        self.layoutChanged.emit()

    def sortItems(self):
        if self.sortByCol == 0:
            sortKey = lambda item: item.operation
        else:
            sortKey = lambda item: item.path
        self.items = sorted(self.items, key=sortKey, reverse=self.sortReverse)

    def rowCount(self, parent=None):
        return len(self.items)

    def columnCount(self, parent=None):
        return 2

    def data(self, index, role=None):
        row = index.row()
        col = index.column()
        if col < 0 or col > 1 or row < 0 or row > self.rowCount() - 1:
            return None
        item = self.items[row]
        if role == Qt.TextAlignmentRole:
            return _CONFIG['columnAlign'][col]
        if role == Qt.FontRole:
            return _CONFIG['columnFont'][col]
        if role == Qt.BackgroundRole:
            return _CONFIG['rowBackground'][item.operation]
        if role != Qt.DisplayRole:
            return None
        if col == 0:
            return _CONFIG['opSymbol'].get(item.operation, '?')
        else:
            if item.isDir:
                return _CONFIG['dirSymbol'] + item.path
            else:
                return _CONFIG['fileSymbol'] + item.path

    def headerData(self, section, orientation, role=None):
        if section < 0 or section > 1 or role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        return _CONFIG['columnTitle'][section]

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        self.sortByCol = column
        self.sortReverse = order != Qt.AscendingOrder
        self.sortItems()
        self.layoutChanged.emit()


class _SeeRsyncRunner(QThread):
    itemCountChanged = pyqtSignal(int)
    resultReady = pyqtSignal(list)

    def __init__(self, commandLine):
        super().__init__()
        self.commandLine = commandLine
        self.rsyncProcess = None

    def run(self):
        self.rsyncProcess = rsync._startRsyncProcess(self.commandLine)
        result = rsync._readRsyncOutput(self.rsyncProcess, lambda items: self.itemCountChanged.emit(len(items)))
        self.resultReady.emit(result)

    def terminate(self):
        if self.rsyncProcess and self.rsyncProcess.poll() is None:
            self.rsyncProcess.kill()
        super().terminate()


class _Window(QWidget):

    def __init__(self, screen, commandLine):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.sizeHint = lambda: QSize(screen.availableSize().width() - 100, screen.availableSize().height() - 100)

        self.model = _ItemsTableModel()
        self.runner = None

        # app state
        self.reportedItemCount = 0
        self.isFreshStart = True
        self.isRunningRsync = False
        self.isCommandLineChangedSinceLastRun = False
        self.timeLastCountRefresh = 0

        self.commandLineTxt = QPlainTextEdit()
        self.commandLineTxt.setFixedHeight(3 * self.commandLineTxt.fontMetrics().lineSpacing() + self.commandLineTxt.contentsMargins().top() + self.commandLineTxt.contentsMargins().bottom() + 2 * self.commandLineTxt.document().documentMargin())
        self.commandLineTxt.setPlainText(' '.join(map(shlex.quote, commandLine)))
        self.commandLineTxt.textChanged.connect(self.onCommandLineChanged)

        self.seeRsyncBtn = QPushButton('Check')
        self.seeRsyncBtn.clicked.connect(self.onStartsRsync)
        buttonBox = QHBoxLayout()
        buttonBox.addStretch(1)
        buttonBox.addWidget(self.seeRsyncBtn)
        buttonBox.addStretch(1)

        itemsTbl = QTableView()
        itemsTbl.setModel(self.model)
        itemsTbl.setSortingEnabled(True)
        itemsTbl.sortByColumn(1, Qt.AscendingOrder)
        itemsTbl.verticalHeader().setVisible(False)
        cols = itemsTbl.horizontalHeader()
        cols.setSectionResizeMode(0, QHeaderView.Interactive)
        cols.setSectionResizeMode(1, QHeaderView.Stretch)

        self.statusLbl = QLabel()
        self.reportedItemCountLbl = QLabel()
        statusBox = QHBoxLayout()
        statusBox.addWidget(self.statusLbl)
        statusBox.addStretch(1)
        statusBox.addWidget(self.reportedItemCountLbl)

        mainBox = QVBoxLayout()
        mainBox.addWidget(QLabel('Command line:'))
        mainBox.addWidget(self.commandLineTxt)
        mainBox.addLayout(buttonBox)
        mainBox.addWidget(QLabel('Legend: ' + _CONFIG['opSymbol'][OperationType.create] + ' create, ' + _CONFIG['opSymbol'][OperationType.update] + ' update, ' + _CONFIG['opSymbol'][OperationType.delete] + ' delete, ' + _CONFIG['dirSymbol'].strip() + ' folder, ' + _CONFIG['fileSymbol'].strip() + ' file'))
        mainBox.addWidget(itemsTbl)
        mainBox.addLayout(statusBox)
        self.setLayout(mainBox)

        self.updateUI()

    def closeEvent(self, event):
        if self.runner and self.runner.isRunning():
            self.runner.terminate()

    def onCommandLineChanged(self):
        self.isCommandLineChangedSinceLastRun = True
        self.updateUI()

    def onStartsRsync(self):
        if self.isRunningRsync:
            return
        self.isRunningRsync = True
        self.isFreshStart = False
        self.isCommandLineChangedSinceLastRun = False
        self.reportedItemCount = 0
        self.model.setItems([])
        self.updateUI()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        self.runner = _SeeRsyncRunner(shlex.split(self.commandLineTxt.toPlainText()))
        self.runner.itemCountChanged.connect(self.itemCountCallback)
        self.runner.resultReady.connect(self.onFinishedRsync)
        self.runner.start()

    def onFinishedRsync(self, items):
        self.model.setItems(items)

        QApplication.restoreOverrideCursor()
        self.isRunningRsync = False
        self.updateUI()

    def itemCountCallback(self, items):
        self.reportedItemCount = items
        # pace the status update
        # use absolute value to guard against clock adjustments
        if abs(time.time() - self.timeLastCountRefresh) >= 1:
            self.timeLastCountRefresh = time.time()
            self.updateUI()

    def updateUI(self):
        self.reportedItemCountLbl.setText('Total items: ' + str(self.reportedItemCount))
        self.commandLineTxt.setEnabled(not self.isRunningRsync)
        self.seeRsyncBtn.setEnabled(not self.isRunningRsync)

        self.statusLbl.setText('')
        if self.isRunningRsync:
            self.showInfoInStatus('Collecting information from rsync...')
        elif rsync.hasQuietFlag(shlex.split(self.commandLineTxt.toPlainText())):
            self.showWarningInStatus('The quiet flag, -q, is detected in the command line. seersync cannot operate if rsync output is suppressed.')
        else:
            if not self.isFreshStart:
                if self.isCommandLineChangedSinceLastRun:
                    self.showWarningInStatus('The listing may be out of date. The rsync command line was edited.')
                elif self.reportedItemCount < 1:
                    self.showWarningInStatus('No items were reported by rsync. Make sure that you don\'t use the quiet flag, -q.')

    def showInfoInStatus(self, msg):
        self.statusLbl.setStyleSheet('')
        self.statusLbl.setText(msg)

    def showWarningInStatus(self, msg):
        self.statusLbl.setStyleSheet(_CONFIG['warnLabelStyle'])
        self.statusLbl.setText('\u26A0 ' + msg)


def launch(commandLine):
    """
    Opens the GUI of the application.
    
    Args:
        commandLine: the rsync command line to check what changes rsync would make
    """
    app = QApplication(['seersync ' + __version__])
    win = _Window(app.primaryScreen(), commandLine)
    win.show()
    app.exec_()
