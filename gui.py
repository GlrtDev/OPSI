from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import numpy as np
import pyqtgraph as pg
from datetime import datetime
from pyqtgraph.parametertree import Parameter, ParameterTree
from collections import OrderedDict
channelInputRanges = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000]

class Gui:

    def __init__(self, extProgram, xWindowSize = 800, yWidnowSize = 600):
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')   
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title="Odszumianie sygnałów EMG")
        self.win.resize(xWindowSize,yWidnowSize)
        self.win.show()
        self.extProgram = extProgram
        self.programRuning = False

    def saveState(self):
        try:
            state = self.param.saveState()
            f = open("conf/savestate.dat", "w")
            f.write(str(state))
        except Exception as e:
            print(f"error {e} occured while saving state")


    def loadState(self):
        try:
            f = open("conf/savestate.dat", "r")
            #print(f.read())
            self.param.restoreState(eval(f.read()))
        except Exception as e:
            print(f"error {e} occured while loading state")

    def plotConf(self):
        labels = {'left': "U [mV]", 'bottom': "time [ms]"}
        self.topPlot = self.win.addPlot(title = "sygnał oryginalny", labels = labels,row=1, col=0)
        self.middlePlot = self.win.addPlot(title = "sygnał zaszumiony", labels = labels,row=2, col=0)
        self.bottomPlot = self.win.addPlot(title = "sygnał odszumiony", labels = labels,row=3, col=0)
        self.curveTop = self.topPlot.plot(pen='b')
        self.curveMiddle = self.middlePlot.plot(pen='b')
        self.curveBottom = self.bottomPlot.plot(pen='b')
        #self.curveTopRMS = self.topPlot.plot(pen='k')
        self.plotConfUpdate()

    def plotConfUpdate(self):
        # TODO get the scale right

        # TODO show signals

        
        self.saveState()

    def getParam(self, paramName):
        return self.param.child(paramName).value()

    def setParam(self, paramName, value):
        self.param.child(paramName).setValue(value)
    
    def getScale(self):
        return self.scale

    def setupConf(self):        
        paramspec = [
            dict(name='INDEKS PRÓBKI', type='int', readonly=False, value=0)
            ]

        self.algorithmList = Parameter.create(name='ALGORYTM', type='list')
        self.algorithmList.setLimits({ "APROKSYMACJA": 0, "MODEL AR" : 1, "TRZECI": 2})
        self.fuzzList = Parameter.create(name='ZASZUMIENIE', type='list')
        self.fuzzList.setLimits({ "10%": 0, "YES2" : 1, "NO": 2})

        self.param = Parameter.create(name='parameters', type='group', children=paramspec)
        self.param.addChild(self.algorithmList)
        self.param.addChild(self.fuzzList)
        tree = ParameterTree()
        tree.setParameters(self.param)
        self.window = QtWidgets.QWidget()
        self.window.setWindowTitle("OKNO KONFIGURACYJNE")
        self.layout = QtWidgets.QGridLayout()
        self.window.setLayout(self.layout)
        l = QtWidgets.QLabel("KONFIGURACJA")
        self.layout.addWidget(l)
        self.layout.addWidget(tree)

        self.runButton = QtGui.QPushButton('Start')
        self.runButton.clicked.connect(self.runExternalProgram)
        self.layout.addWidget(self.runButton)

        self.loadState()
        self.param.sigTreeStateChanged.connect(self.paramChange)
        
        self.window.setGeometry(500, 500, 400, 500) 
        self.window.show()
        

 # only new pack of date come into this, not full n finished buffer

    def paramChange(self):
        self.plotConfUpdate()

    def updatePlot(self, data):
        self.curveTop.setData(x=data[0], y=data[1])
        self.curveMiddle.setData(x=data[0], y=data[1])
        self.curveBottom.setData(x=data[0], y=data[1])
        QtGui.QApplication.processEvents()
        

    #if btn clicked them -> settings Ready -> run program
    def runExternalProgram(self, *args):
        if not self.programRuning:
            self.programRuning = 1
            self.programRuning = self.extProgram(args)
        else: 
            print("program is still running")


if __name__ == '__main__':
    pg.exec()
