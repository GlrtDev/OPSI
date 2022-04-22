from isort import ImportKey
from numpy.core.fromnumeric import size
import numpy as np
import time
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets, QtTest
import pyqtgraph as pg
from modules.scheduler import Scheduler


if __name__ == '__main__':
    print("0 to GUI, 1 to CMD")
    mode = int(input())

    scheduler = Scheduler(mode)
    if mode == 0:
        QtGui.QApplication.instance().exec()
    else:
        scheduler.runCmd()
    


