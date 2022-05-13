from distutils.log import error
from itertools import count
import numpy as np
import csv
from modules.emd import SchedulerEMD
from modules.dataLoader import DataLoader
from modules.gui import Gui
from modules.dwt import DWT
from modules.adaptiveFilter import AdaptiveFilterLMS


class Scheduler:
    def __init__(self, mode):
        self.dataLoader = DataLoader()
        self.emd = SchedulerEMD()
        self.dwt = DWT()
        self.adaptiveFilter = AdaptiveFilterLMS()
        self.mode = mode
        if self.mode == 0:
            self.guiHandler = Gui(self.run)
            self.guiHandler.plotConf()
            self.guiHandler.setupConf()

    def generateNoise(self, signal=None, noiseType=0, noiseStrength=0.1):
        if signal is None:
            signal = [np.zeros(10), np.zeros(10)]
        mean = 0
        std = 1
        num_samples = signal.shape[0]  # idk if correct size is taken

        noise = np.zeros(signal.shape)
        signalPtP = np.ptp(signal, axis=0)[1]
        signalPower = np.sqrt(np.mean(signal[:, -1] ** 2))
        noise[:, 0] = np.copy(signal[:, 0])
        whiteNoisePower = 0
        PLINoisePower = 0

        if noiseType in [0, 3, 4]:
            whiteNoisePower = 1
            whiteNoise = signalPtP * whiteNoisePower * np.random.normal(mean, std, size=num_samples) * noiseStrength
            whiteNoisePower = np.sqrt(np.mean(whiteNoise ** 2))
            noise[:, -1] += np.transpose(whiteNoise)

        frequencyNoise = np.zeros(num_samples)

        # if noiseType in [1, 4]:
        PLIFrequencies = [50]
        # else:
        #     PLIFrequencies = [50, 100, 150, 200, 250, 300]
        PLIInterferencePower = 1.0

        # PLI noise
        if noiseType in [1, 2, 3, 4]:
            for freq in PLIFrequencies:
                frequencyNoise += signalPtP * PLIInterferencePower * np.sin(
                    freq * 2 * np.pi * noise[:, 0]) * noiseStrength
        noise[:, -1] += np.transpose(frequencyNoise)

        # baseline wandering
        if noiseType in [2, 3]:
            freq = 0.1
            frequencyNoise += signalPtP * 10.3 * PLIInterferencePower * np.sin(
                freq * 2 * np.pi * noise[:, 0]) * noiseStrength
        noise[:, -1] += np.transpose(frequencyNoise)

        PLINoisePower = np.sqrt(np.mean(frequencyNoise ** 2))  # TODO RMS is really needed ?
        if self.mode == 0:
            self.guiHandler.setParam("SNR", (signalPower ** 2) / (whiteNoisePower + PLINoisePower) ** 2)
            return noise
        else:
            SNR = (signalPower ** 2) / (whiteNoisePower + PLINoisePower) ** 2
            return noise, SNR

    def run(self):
        signal = self.dataLoader.load("samples/emg_healthy.txt")
        denoisedSignal = [np.zeros(10), np.zeros(10)]

        # "FALKI": 0
        # "ADAPTACYJNY": 1
        # "EMD": 2
        algorithm = self.guiHandler.getParam("ALGORYTM")

        # "SZUM BIAŁY": 0
        # "50HZ" : 1
        # "50HZ + DRYFT": 2
        # "50HZ + DRYFT + SZUM BIAŁY": 3
        # "50HZ + SZUM BIAŁY" : 4
        noiseType = self.guiHandler.getParam("ZASZUMIENIE")

        # float
        noiseStrength = self.guiHandler.getParam("NOISE STRENGTH")

        # indeks probki, int # TODO is it needed?
        sampleIndex = self.guiHandler.getParam("INDEKS PROBKI")

        noise = self.generateNoise(signal, noiseType=noiseType, noiseStrength=noiseStrength)
        noisedSignal = self.addSignals(signal, noise)

        if algorithm == 0:
            wavelet = self.guiHandler.getParam("RODZAJ FALEK")
            level = self.guiHandler.getParam("POZIOM DEKOMPOZYCJI")

            denoisedSignal = self.dwt.denoise(signal=noisedSignal[:, 1], wavelet=wavelet, level=level)

        if algorithm == 1:
            learningRate = self.guiHandler.getParam("KROK ADAPTACJI")

            denoisedSignal = self.adaptiveFilter.denoise(
                x=noisedSignal,
                mu=learningRate,
                d=noise)  # ??????????????????

        if algorithm in [2, 3, 4]:
            self.emd.setStopConditions(fixe=5)
            IFMs = self.emd.decomposeAndGetIMFs(
                signal=[noisedSignal[:, 1], noisedSignal[:, 0]],
                mode=algorithm,
                verbose=True
            )

            IFMsPLI = self.emd.removePLIFromIFMs(
                IFMs,
                verbose=True
            )

            IFMsWN = self.emd.removeWhiteNoiseFromIFMs(
                IFMsPLI,
                hardThresholding=self.guiHandler.getParam("HARD THRESHOLDING"),
                intervalThresholding=self.guiHandler.getParam("EMD-IT"),
                verbose=True
            )

            IFMsBW = self.emd.removeBaselineWanderFromIFMs(
                IFMsWN,
                verbose=True
            )

            denoisedSignal = self.emd.parseIFMsToSignal(
                originalSignal=signal,
                IFMs=IFMsBW
            )

        self.guiHandler.updatePlot([signal, noisedSignal, denoisedSignal])
        # PLIFrequencies=[50, 100, 150, 200, 250, 300]

    def runCmd(self):
        listOfFiles = ["samples/emg_healthy.txt"]
        signals = list()
        for file in listOfFiles:
            signals.append(self.dataLoader.load(file))
        print("CMD START")

        f = open('data.csv', 'w', newline="")
        writer = csv.writer(f)
        header = ['SNR', 'mode', 'fixe', 'hardThresholding', 'varLevelActivation', 'omega 0', 'M', 'error']

        writer.writerow(header)
        i = 0
        fixeRange = range(2, 10, 1)
        thresholdRange = [True, False]
        varActivRange = np.arange(0.01, 0.011, 0.001)
        omega0Range = np.arange(10, 100, 10)
        MRange = np.arange(1, 1.01, 0.05)
        maxIterations = len(fixeRange) * len(thresholdRange) * varActivRange.size * omega0Range.size * MRange.size - 1

        for signal in signals:
            noise, SNR = self.generateNoise(signal, noiseType=0, noiseStrength=0.005)
            noisedSignal = self.addSignals(signal, noise)

            for fixe in fixeRange:
                for mode in [2]:
                    for hardThresholding in thresholdRange:
                        for varLevelActivation in varActivRange:
                            for omega0 in omega0Range:
                                for M in MRange:
                                    denoisedSignal = self.emd.denoise(
                                        signal=noisedSignal,
                                        mode=mode,
                                        fixe=fixe,
                                        hardThresholding=hardThresholding,
                                        varLevelActivation=varLevelActivation,
                                        omega0=omega0,
                                        M=M
                                    )
                                    print(f"{i}/{maxIterations}")
                                    row = [SNR, mode, fixe, hardThresholding, varLevelActivation, omega0, M,
                                           self.countError(signal, denoisedSignal)]
                                    writer.writerow(row)
                                    i += 1

        f.close()

    @staticmethod
    def countError(originalSignal, denoisedSignal, mode=2):
        if mode == 2:
            errors = np.copy(originalSignal)
            errors[:, -1] -= denoisedSignal[:, -1]
            return np.mean(errors[:, -1] ** 2)

    @staticmethod
    def addSignals(signal, signalToAdd):
        newSignal = np.copy(signal)
        newSignal[:, -1] += signalToAdd[:, -1]
        return newSignal
