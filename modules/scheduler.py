from distutils.log import error
from itertools import count
import numpy as np
import csv
import wfdb

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
        signalPower = np.mean(signal[:, -1] ** 2)
        noise[:, 0] = np.copy(signal[:, 0])
        whiteNoisePower = 0
        PLINoisePower = 0

        if noiseType in [0, 3, 4]:
            whiteNoise = signalPtP * np.random.normal(mean, std, size=num_samples) * noiseStrength
            whiteNoisePower = np.mean(whiteNoise ** 2)
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

        PLINoisePower = np.mean(frequencyNoise ** 2)  # TODO RMS is really needed ?
        if self.mode == 0:
            self.guiHandler.setParam("SNR", (signalPower) / ((whiteNoisePower + PLINoisePower)))
            return noise
        else:
            SNR = (signalPower) / ((whiteNoisePower + PLINoisePower) )
            return noise, SNR

    def run(self):
        signal = self.dataLoader.load("samples/S6")

        denoisedSignal = [np.zeros(10), np.zeros(10)]

        # "FALKI": 0
        # "ADAPTACYJNY": 1
        # "EMD": 2
        algorithm = self.guiHandler.getParam("ALGORYTM")

        # "SZUM BIA??Y": 0
        # "50HZ" : 1
        # "50HZ + DRYFT": 2
        # "50HZ + DRYFT + SZUM BIA??Y": 3
        # "50HZ + SZUM BIA??Y" : 4
        noiseType = self.guiHandler.getParam("ZASZUMIENIE")

        # float
        noiseStrength = self.guiHandler.getParam("NOISE STRENGTH")

        # indeks pr??bki, int
        sampleIndex = self.guiHandler.getParam("INDEKS PROBKI")

        noise = self.generateNoise(signal, noiseType=noiseType, noiseStrength=noiseStrength)
        noiseSampleForAdaptive = self.generateNoise(signal, noiseType=noiseType, noiseStrength=noiseStrength)
        noisedSignal = self.addSignals(signal, noise)

        if algorithm == 0:
            wavelet = self.guiHandler.getParam("RODZAJ FALEK")
            level = self.guiHandler.getParam("POZIOM DEKOMPOZYCJI")

            denoisedSignal = self.dwt.denoise(signal=noisedSignal, wavelet=wavelet, level=level)

        if algorithm == 1:
            learningRate = self.guiHandler.getParam("KROK ADAPTACJI")
            taps = self.guiHandler.getParam("TAPS NUMBER")
            denoisedSignal = self.adaptiveFilter.denoiseLMS(
                x=noisedSignal,
                mu=learningRate,
                d=noiseSampleForAdaptive,
                n=int(taps))

        if algorithm in [2, 3, 4]:
            self.emd.setStopConditions(fixe=self.guiHandler.getParam("FIXE"))
            IFMs = self.emd.decomposeAndGetIMFs(
                signal=[noisedSignal[:, 1], noisedSignal[:, 0]],
                mode=algorithm,
                verbose=False
            )

            IFMsPLI = self.emd.removePLIFromIFMs(
                IFMs,
                verbose=False
            )

            IFMsWN = self.emd.removeWhiteNoiseFromIFMs(
                IFMsPLI,
                hardThresholding=self.guiHandler.getParam("HARD THRESHOLDING"),
                intervalThresholding=self.guiHandler.getParam("EMD-IT"),
                verbose=False
            )

            IFMsBW = self.emd.removeBaselineWanderFromIFMs(
                IFMsWN,
                verbose=False
            )

            denoisedSignal = self.emd.parseIFMsToSignal(
                originalSignal=signal,
                IFMs=IFMsBW
            )

        self.guiHandler.updatePlot([signal, noisedSignal, denoisedSignal])
        # PLIFrequencies=[50, 100, 150, 200, 250, 300]

    def runCmd(self):
        listOfFiles = ["samples/S6"]
        signals = list()
        for file in listOfFiles:
            signals.append(self.dataLoader.load(file))
        print("CMD START")

        # EMD csv file creation
        f1 = open('emd.csv', 'w', newline="")
        writerEmd = csv.writer(f1)
        headerEmd = ['SNR', 'mode', 'fixe', 'hardThresholding', 'varLevelActivation', 'omega 0', 'M', 'error']
        writerEmd.writerow(headerEmd)

        # EMD parameters initialization
        fixeRange = range(2, 10, 1)
        thresholdRange = [True, False]
        varActiveRange = np.arange(0.01, 0.011, 0.003)
        omega0Range = np.arange(10, 70, 20)
        MRange = np.arange(1.01, 1.05, 0.04)
        maxIterationsEmd = len(fixeRange) * len(
            thresholdRange) * varActiveRange.size * omega0Range.size * MRange.size - 1

        # DWT csv file creation
        f2 = open('dwt.csv', 'w', newline="")
        writerDwt = csv.writer(f2)
        headerDwt = ['SNR', 'decomposition level', 'wavelets', 'error']
        writerDwt.writerow(headerDwt)

        # DWT parameters initialization
        decompositionLevels = np.arange(1, 10, 1)
        wavelets = ['bior1.1', 'bior1.3', 'bior3.3', 'coif2', 'coif6', 'coif10', 'db2', 'db4', 'db6', 'db8']
        maxIterationsDwt = len(wavelets) * decompositionLevels.size - 1

        # Adaptive csv file creation
        f3 = open('adaptive.csv', 'w', newline="")
        writerAdap = csv.writer(f3)
        headerAdap = ['SNR', 'number of filter taps', 'learning rate', 'error']
        writerAdap.writerow(headerAdap)

        # Adaptive parameters initialization
        filterTaps = np.arange(2, 11, 2, dtype=int)
        learningRates = np.logspace(-3, -1, num=10)
        maxIterationsAdap = filterTaps.size * learningRates.size - 1

        maxIterationsForSample = maxIterationsDwt + maxIterationsEmd + maxIterationsAdap + 2

        i = 0
        j = 0

        # nothing of value will come if more than one signal is analyzed at a time
        for signal in signals:
            noise, SNR = self.generateNoise(signal, noiseType=0, noiseStrength=0.2)
            noiseSample, SNR2 = self.generateNoise(signal, noiseType=0, noiseStrength=0.2)
            noisedSignal = self.addSignals(signal, noise)

            for mode in [0, 1, 2]:
                if mode == 2:
                    j += i
                    i = 0
                    for fixe in fixeRange:
                        for hardThresholding in thresholdRange:
                            for varLevelActivation in varActiveRange:
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
                                        print(f"{i}/{maxIterationsEmd} {j + i}/{maxIterationsForSample}")
                                        row = [SNR, mode, fixe, hardThresholding, varLevelActivation, omega0, M,
                                               self.countError(signal, denoisedSignal)]
                                        writerEmd.writerow(row)
                                        i += 1
                if mode == 1:
                    j += i
                    i = 0
                    for learningRate in learningRates:
                        for filterTap in filterTaps:
                            denoisedSignal = self.adaptiveFilter.denoiseLMS(
                                x=noisedSignal,
                                mu=learningRate,
                                d=noiseSample,
                                n=filterTap.item())
                            print(f"{i}/{maxIterationsAdap} {j + i}/{maxIterationsForSample}")
                            row = [SNR, filterTap, learningRate,
                                   self.countError(signal, denoisedSignal)]
                            writerAdap.writerow(row)
                            i += 1

                if mode == 0:
                    j += i
                    i = 0
                    for wavelet in wavelets:
                        for level in decompositionLevels:
                            denoisedSignal = self.dwt.denoise(signal=noisedSignal, wavelet=wavelet, level=level)
                            print(f"{i}/{maxIterationsDwt} {j + i}/{maxIterationsForSample}")
                            row = [SNR, level, wavelet,
                                   self.countError(signal, denoisedSignal)]
                            writerDwt.writerow(row)
                            i += 1

        f1.close()
        f2.close()
        f3.close()

        f1 = open('emd.csv', 'r', newline="")
        f2 = open('dwt.csv', 'r', newline="")
        f3 = open('adaptive.csv', 'r', newline="")

        emdCsv = csv.reader(f1)
        emdResultsList = sorted(emdCsv, key=lambda row: row[6], reverse=False)

        dwtCsv = csv.reader(f2)
        dwtResultsList = sorted(dwtCsv, key=lambda row: row[3], reverse=False)

        emdCsv = csv.reader(f3)
        adapResultsList = sorted(emdCsv, key=lambda row: row[3], reverse=False)
        print(f"\nBest EMD parameters:")
        for name, param in zip(emdResultsList[-1], emdResultsList[1]):
            print(f"{name} : {param}")

        print(f"\nBest dwt parameters:")
        for name, param in zip(dwtResultsList[-1], dwtResultsList[1]):
            print(f"{name} : {param}")

        print(f"\nBest adap parameters:")
        for name, param in zip(adapResultsList[-1], adapResultsList[1]):
            print(f"{name} : {param}")

        f1.close()
        f2.close()
        f3.close()

    # MSE
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
