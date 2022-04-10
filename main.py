from isort import ImportKey
from numpy.core.fromnumeric import size
import numpy as np
import time
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets, QtTest
import pyqtgraph as pg

from modules.scheduler import Scheduler
if __name__ == '__main__':
    scheduler = Scheduler()
    
    QtGui.QApplication.instance().exec()
    


