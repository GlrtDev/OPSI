from numpy.core.fromnumeric import size
from gui import Gui
import numpy as np
import time
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets, QtTest
import pyqtgraph as pg


class GuiTest:

    SEMPLES_NUMBER = 150
    REFRESH_RATE = 500
    def __init__(self):
        self.dataBuffer = np.zeros(self.SEMPLES_NUMBER)
        self.timebaseBuffer = np.zeros(self.SEMPLES_NUMBER)

        self.guiHandler = Gui(self.scheduler)
        
        self.rng = np.random.default_rng(seed=87)
        self.iteration = 1
    

    def generateData(self):
        randomData = self.rng.uniform(low=-1, high = 1, size =self.SEMPLES_NUMBER)
        return randomData
    
    
    def updateBuffersAndPlots(self):
        self.dataBuffer = self.generateData()
        self.timebaseBuffer = np.arange(
            (self.iteration-1) * self.SEMPLES_NUMBER,
            (self.iteration) * self.SEMPLES_NUMBER)
        self.guiHandler.updatePlot([self.timebaseBuffer, self.dataBuffer])

    def scheduler(self, *args):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(guiTest.updateBuffersAndPlots)
        self.timer.start(guiTest.REFRESH_RATE)
        
        QtTest.QTest.qWait(10000)
        self.timer.stop()
        return 0

if __name__ == '__main__':
    
    guiTest = GuiTest()
    #import pyqtgraph.examples
    #pyqtgraph.examples.run()   

    guiTest.guiHandler.setupConf()
    guiTest.guiHandler.plotConf()
    QtGui.QApplication.instance().exec()
    


