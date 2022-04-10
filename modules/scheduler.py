import numpy as np
from modules.emd import EMD
from modules.dataLoader import DataLoader
from modules.gui import Gui

class Scheduler:

    def __init__(self):
        self.dataLoader = DataLoader()
        self.guiHandler = Gui(self.run)
        self.guiHandler.plotConf()
        self.guiHandler.setupConf()

    def addNoise(self, signal=[np.zeros(10), np.zeros(10)], PLIFrequencies=[50, 100, 150, 200, 250, 300], SNR=1.0):
        mean = 0
        std = 1
        num_samples = signal.shape[0]  # idk if correct size is taken
        whiteNoisePower = 1
        whiteNoise = whiteNoisePower * np.random.normal(mean, std, size=num_samples)/SNR
        
        
        noisedSignal = np.copy(signal)
        noisedSignal[:,-1] += np.transpose(whiteNoise)
        print(noisedSignal)
        # frequencyNoise = np.zeros(num_samples)
        # for freq in PLIFrequencies:
        #     frequencyNoise += np.sin(freq*2*np.pi*noisedSignal[0])/SNR  # 50 hz per sec
        # print(frequencyNoise)
        # noisedSignal[1] += (whiteNoise + frequencyNoise)
        return noisedSignal
    
    def run(self):
        data = self.dataLoader.load("samples/emg_healthy.txt")
        print(data)
        # falka 0, adap 1 , emd 2
        algorithm = self.guiHandler.getParam("ALGORYTM") 
        #"SZUM BIAŁY": 0, "50HZ" : 1, "50HZ + HARMONICZNE": 2,"50HZ + HARMONICZNE + SZUM BIAŁY": 3,"50HZ + SZUM BIAŁY" : 4
        noiseType = self.guiHandler.getParam("ZASZUMIENIE") 
        # float
        snr = self.guiHandler.getParam("SNR")
        # indeks probki, int 
        sampleIndex = self.guiHandler.getParam("INDEKS PROBKI")
        noisedSignal = self.addNoise(data)
        self.guiHandler.updatePlot([data, noisedSignal])
        PLIFrequencies=[50, 100, 150, 200, 250, 300]

