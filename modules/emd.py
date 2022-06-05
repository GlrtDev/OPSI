from concurrent.futures import process
from PyEMD import EMD, EEMD, CEEMDAN, Visualisation
from enum import Enum
from scipy import signal
import numpy as np
import pywt


class EMDMode(Enum):
    EMD = 1
    GREEN = 2
    BLUE = 3


class SchedulerEMD:
    def __init__(self) -> None:
        self.emd = EMD(parallel=True, process=3)
        self.eemd = EEMD(parallel=True, process=3)
        self.ceemdan = CEEMDAN(parallel=True, process=3)
        self.visualisation = Visualisation()
        self.sampleFreq = 4000

    def denoise(self, signal, mode, fixe=0, hardThresholding=False, varLevelActivation=0.1, omega0=30, M=1.02):
        self.setStopConditions(fixe=fixe)
        noisedSignal = [signal[:, 1], signal[:, 0]]
        step1 = self.decomposeAndGetIMFs(noisedSignal, mode)
        step2 = self.removePLIFromIFMs(step1, varLevelActivation=varLevelActivation)
        step3 = self.removeWhiteNoiseFromIFMs(step2, hardThresholding=hardThresholding)
        step4 = self.removeBaselineWanderFromIFMs(step3, omega0=omega0, M=M)
        return self.parseIFMsToSignal(signal, step4)

    def setStopConditions(self, fixe=0, fixe_h=0):
        """ All methods have the same two conditions, FIXE and FIXE_H,
            for stopping which relate to the number of sifting iterations.
            Setting parameter FIXE to any positive value will fix the number of iterations for each IMF to be exactly FIXE.
        """
        self.emd.FIXE = fixe

        """ parameter FIXE_H relates to the number of iterations when the proto-IMF signal fulfils IMF conditions,
            i.e. number of extrema and zero-crossings differ at most by one and the mean is close to zero.
            This means that there will be at least FIXE_H iteration per IMF.
        """
        self.emd.FIXE_H = fixe_h

    def decomposeAndGetIMFs(self, signal, mode=2, verbose=False):
        self.sampleFreq = np.floor(1 / signal[1][0])
        if mode == 2:
            IFMs = self.emd.emd(signal[0], signal[1], max_imf=9)
            self.visualisation = Visualisation(self.emd)
        elif mode == 3:
            IFMs = self.eemd.eemd(signal[0], signal[1], max_imf=9)
            self.visualisation = Visualisation(self.eemd)
        elif mode == 4:
            IFMs = self.ceemdan.ceemdan(signal[0], signal[1], max_imf=9)
            self.visualisation = Visualisation(self.ceemdan)
        if verbose:
            self.showIFMs(IFMs)
        return IFMs

    def showIFMs(self, IFMs):
        self.visualisation.plot_imfs(IFMs)
        self.visualisation.show()

    def removePLIFromIFMs(self, IFMs, verbose=False, varLevelActivation=0.1):
        samp_freq = self.sampleFreq  # Sample frequency (Hz)

        notch_freq = 50.0  # Frequency to be removed from signal (Hz)
        quality_factor = 5.0  # Quality factor
        b_notch, a_notch = signal.iirnotch(notch_freq, quality_factor, samp_freq)
        IFMsFiltered = np.copy(IFMs)
        i = 0
        for IFM in IFMs:
            a = signal.filtfilt(b_notch, a_notch, IFM)
            if (np.var(IFM - a) / np.var(IFM)) < varLevelActivation:
                IFMsFiltered[i] = IFM
            else:
                IFMsFiltered[i] = a
            i += 1
        if verbose:
            self.showIFMs(IFMsFiltered)
        return IFMsFiltered

    def removeWhiteNoiseFromIFMs(self, IFMs, hardThresholding=False,
                                 verbose=False, intervalThresholding=False):
        IFMsFiltered = np.copy(IFMs)
        i = 0
        for IFM in IFMs:
            noiseLevel = np.median(abs(IFM)) / 0.6745
            threshold = noiseLevel * np.sqrt(2 * np.log(IFM.shape[0]))
            # not used, pywt does automatic threshold
            if intervalThresholding:
                zero_crossings = np.where(np.diff(np.sign(IFM)))[0]
                IFMSplitted = np.hsplit(IFM, zero_crossings)
                j = 0
                for IFMPart in IFMSplitted:
                    if hardThresholding:
                        IFMSplitted[j] = pywt.threshold(IFMPart, threshold, 'hard')
                    elif not hardThresholding:
                        IFMSplitted[j] = pywt.threshold(IFMPart, threshold, 'soft')
                    j += 1
                IFMsFiltered[i] = np.concatenate(IFMSplitted)
            else:
                if hardThresholding:
                    # IFMsFiltered[i] = pywt.threshold(IFM, threshold,'hard')
                    IFMsFiltered[i] = pywt.threshold(IFM, threshold, 'hard')
                elif not hardThresholding:
                    IFMsFiltered[i] = pywt.threshold(IFM, threshold, 'soft')
            i += 1
        if verbose:
            self.showIFMs(IFMsFiltered)
        return IFMsFiltered

    def removeBaselineWanderFromIFMs(self, IFMs, verbose=False, omega0=30, M=1.02):
        IFMsFiltered = np.copy(IFMs)
        N = IFMs.shape[0]
        d = list()  # d is filtered IFM
        b = list()  # b is baselineWander component
        i = 0
        for IFM in IFMs:
            cutOffFrequence = (omega0 / (M ** (N - i)))
            d = (self.butter_lowpass_filter(IFM, cutOffFrequence))
            if np.var(IFM) > 0:
                threshold = np.var(d) / np.var(IFM)
            else:
                threshold = 1
            if threshold < 0.05:
                b.append(np.zeros(IFM.shape))
            elif threshold <= 0.5:
                b.append(d)
            else:
                b.append(IFM)
            i += 1
        i = 0
        for IFM in IFMs:
            IFMsFiltered[i] = IFM - b[i]
            i += 1
        if verbose:
            # self.showIFMs(np.array(b))
            self.showIFMs(IFMsFiltered)
        return IFMsFiltered

    def parseIFMsToSignal(self, originalSignal, IFMs):
        signalToReturn = np.copy(originalSignal)
        signalToReturn[:, -1] = np.zeros(originalSignal.shape[0])
        for IFM in IFMs:
            signalToReturn[:, -1] += IFM
        return signalToReturn

    def butter_lowpass(self, cutoff, fs, order=5):
        return signal.butter(order, cutoff, fs=fs, btype='low', analog=False)

    def butter_lowpass_filter(self, data, cutoff, order=5):
        b, a = self.butter_lowpass(cutoff, self.sampleFreq, order=order)
        y = signal.lfilter(b, a, data)
        return y
