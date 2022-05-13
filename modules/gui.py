from pyqtgraph.Qt import QtGui, QtWidgets
import pyqtgraph as pg
from datetime import datetime
from pyqtgraph.parametertree import Parameter, ParameterTree
from collections import OrderedDict


class Gui:
    def __init__(self, extProgram, xWindowSize=800, yWindowSize=600):
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')   
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title="Odszumianie sygnałów EMG")
        self.win.resize(xWindowSize, yWindowSize)
        self.window = QtWidgets.QWidget()
        self.layout = QtWidgets.QGridLayout()
        self.runButton = QtGui.QPushButton('Start')
        self.win.show()
        self.param = None
        self.wavParam = None
        self.scale = None
        self.extProgram = extProgram
        self.programRunning = False

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
            # print(f.read())
            self.param.restoreState(eval(f.read()))
        except Exception as e:
            print(f"error {e} occurred while loading state")

    def plotConf(self):
        labels = {'left': "U [mV]", 'bottom': "time [ms]"}
        self.topPlot = self.win.addPlot(title="sygnał oryginalny", labels=labels, row=1, col=0)
        self.middlePlot = self.win.addPlot(title="sygnał zaszumiony", labels=labels, row=2, col=0)
        self.bottomPlot = self.win.addPlot(title="sygnał odszumiony", labels=labels, row=3, col=0)
        self.curveTop = self.topPlot.plot(pen='b')
        self.curveMiddle = self.middlePlot.plot(pen='b')
        self.curveBottom = self.bottomPlot.plot(pen='b')
        # self.curveTopRMS = self.topPlot.plot(pen='k')
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
            dict(name='INDEKS PROBKI', type='int', readonly=False, value=0),
            dict(name='SNR', type='float', readonly=True, value=0),
            dict(name='NOISE STRENGTH', type='float', readonly=False, value=10),
            dict(name='EMD-IT', type='bool', readonly=False, value=False),
            dict(name='HARD THRESHOLDING', type='bool', readonly=False, value=False),
            dict(name='KROK ADAPTACJI', type='float', readonly=False, value=0.1),
            ]

        algorithmList = Parameter.create(name='ALGORYTM', type='list')
        algorithmList.setLimits({"DWT": 0,
                                 "ADAPTACYJNY": 1,
                                 "EMD": 2,
                                 "EEMD": 3,
                                 "CEEMDAN": 4})

        fuzzList = Parameter.create(name='ZASZUMIENIE', type='list')
        fuzzList.setLimits({"SZUM BIALY": 0,
                            "50HZ": 1,
                            "50HZ + DRYFT LINIJ BAZOWEJ": 2,
                            "50HZ + DRYFT LINIJ BAZOWEJ + SZUM BIALY": 3,
                            "50HZ + SZUM BIALY": 4,
                            "BRAK": 5})

        waveletsList = Parameter.create(name='RODZAJ FALEK', type='list')
        waveletsList.setLimits({'bior1.1': 'bior1.1',
                                'bior1.3': 'bior1.3',
                                'bior3.3': 'bior3.3',
                                'coif2': 'coif2',
                                'coif6': 'coif6',
                                'coif10': 'coif10',
                                'db2': 'db2',
                                'db4': 'db4',
                                'db6': 'db6',
                                'db8': 'db8'})

        decompositionLevelParam = dict(name='POZIOM DEKOMPOZYCJI', type='int', readonly=False, value=1)

        self.param = Parameter.create(name='', type='group', children=paramspec)
        self.param.addChild(algorithmList)
        self.param.addChild(fuzzList)
        # TODO SHOW WAVELET PARAMS ONLY WHEN DWT METHOD IS CHOSEN
        self.param.addChild(waveletsList)
        self.param.addChild(decompositionLevelParam)

        tree = ParameterTree()
        tree.setParameters(self.param)

        self.window.setWindowTitle("OKNO KONFIGURACYJNE")
        self.window.setLayout(self.layout)
        l = QtWidgets.QLabel("KONFIGURACJA")
        self.layout.addWidget(l)
        self.layout.addWidget(tree)

        self.runButton.clicked.connect(self.runExternalProgram)
        self.layout.addWidget(self.runButton)

        self.loadState()
        self.param.sigTreeStateChanged.connect(self.paramChange)
        
        self.window.setGeometry(500, 500, 400, 500) 
        self.window.show()

    # only new pack of date come into this, not full n finished buffer
    def paramChange(self):
        self.plotConfUpdate()

    def updatePlot(self, data: list):  # data is list with x1,y1, x2,y2 etc.
        self.curveTop.setData(data[0])
        self.curveMiddle.setData(data[1])
        self.curveBottom.setData(data[2])  # 2
        QtGui.QApplication.processEvents()

    # if btn clicked them -> settings Ready -> run program
    def runExternalProgram(self):
        if not self.programRunning:
            self.programRunning = 1
            self.programRunning = self.extProgram()
        else: 
            print("program is still running")


if __name__ == '__main__':
    pg.exec()
