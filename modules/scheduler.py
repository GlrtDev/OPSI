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

    def generateNoise(self, signal=[np.zeros(10), np.zeros(10)], noiseType = 0, noiseStrength=0.1):
        mean = 0
        std = 1
        num_samples = signal.shape[0]  # idk if correct size is taken
        
        noise = np.zeros(signal.shape)
        signalPtP = np.ptp(signal, axis=0)[1]
        signalPower = np.sqrt(np.mean(signal[:,-1]**2))
        noise[:,0] = np.copy(signal[:,0])
        whiteNoisePower = 0
        PLINoisePower = 0

        if noiseType in [0,3,4]:
            whiteNoisePower = 1
            whiteNoise = signalPtP * whiteNoisePower * np.random.normal(mean, std, size=num_samples) * noiseStrength
            whiteNoisePower = np.sqrt(np.mean(whiteNoise**2))
            noise[:,-1] += np.transpose(whiteNoise)

        frequencyNoise = np.zeros(num_samples)

        if noiseType in [1,4]:
            PLIFrequencies=[50]
        else:
            PLIFrequencies=[50, 100, 150, 200, 250, 300]
        PLIInterferencePower = 1.0
        
        if noiseType in [1,2,3,4]:
            for freq in PLIFrequencies:
                frequencyNoise +=  signalPtP * PLIInterferencePower * np.sin(freq*2*np.pi*noise[:,0])* noiseStrength
                PLIInterferencePower *= 0.45 # TODO search for documentation that tells that every harmoniczna is weaker by 0.45
        noise[:,-1] +=  np.transpose(frequencyNoise)

        PLINoisePower = np.sqrt(np.mean(frequencyNoise**2)) #TODO RMS is really needed ?
        self.guiHandler.setParam("SNR", (signalPower**2)/(whiteNoisePower + PLINoisePower)**2)
        return noise
    
    def addSignals(self, signal, signalToAdd):
        newSignal = signal[:,-1] + signalToAdd[:,-1]
        return newSignal

    def run(self):
        signal = self.dataLoader.load("samples/emg_healthy.txt")
        #print(signal)
        #print("\n\n")
        # falka 0, adap 1 , emd 2
        algorithm = self.guiHandler.getParam("ALGORYTM") 
        #"SZUM BIAŁY": 0, "50HZ" : 1, "50HZ + HARMONICZNE": 2,"50HZ + HARMONICZNE + SZUM BIAŁY": 3,"50HZ + SZUM BIAŁY" : 4
        noiseType = self.guiHandler.getParam("ZASZUMIENIE") 
        # float
        noiseStrength = self.guiHandler.getParam("NOISE STRENGTH")
        # indeks probki, int 
        sampleIndex = self.guiHandler.getParam("INDEKS PROBKI")

        noise = self.generateNoise(signal, noiseType = noiseType, noiseStrength=noiseStrength)
        noisedSignal = self.addSignals(signal, noise)
        print(noisedSignal)

        self.guiHandler.updatePlot([signal, noisedSignal])
        PLIFrequencies=[50, 100, 150, 200, 250, 300]

