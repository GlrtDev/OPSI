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
        self.emd = EMD()
        self.eemd = EEMD()
        self.ceemdan = CEEMDAN()
        self.visualisation = Visualisation()

    def setStopConditions(self,fixe=0, fixe_h=0):
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

    def decomposeAndGetIMFs(self, signal, mode = "emd", verbose = False):
        if mode == "emd":
            IFMs = self.emd.emd(signal[0],signal[1])
            self.visualisation = Visualisation(self.emd)
        elif mode == "eemd":
            IFMs = self.eemd.emd(signal[0],signal[1])
            self.visualisation = Visualisation(self.eemd)
        elif mode == "ceemdan":
            IFMs = self.ceemdan.emd(signal[0],signal[1])
            self.visualisation = Visualisation(self.ceemdan)
        if verbose:
            self.showIFMs(IFMs)
        return IFMs

    def showIFMs(self, IFMs):
        self.visualisation.plot_imfs(IFMs)
        self.visualisation.show()
            
    def removePLIFromIFMs(self, IFMs,verbose = False):
        samp_freq = 4000  # Sample frequency (Hz)
        notch_freq = 50.0  # Frequency to be removed from signal (Hz)
        quality_factor = 5.0  # Quality factor
        b_notch, a_notch = signal.iirnotch(notch_freq, quality_factor,samp_freq)
        IFMsFiltered = np.copy(IFMs)
        i = 0
        for IFM in IFMs:
            a = signal.filtfilt(b_notch, a_notch, IFM)
            if (np.var(IFM-a)/np.var(IFM)) < 0.1:
                IFMsFiltered[i] = IFM
            else:
                IFMsFiltered[i] = a
            i+=1
        if verbose:
            self.showIFMs(IFMsFiltered)
        print(IFMs)
        print(IFMsFiltered)
        return IFMsFiltered

    def removeWhiteNoiseFromIFMs(self, IFMs, thresholding = "hard", intervalThresholding = False, verbose = False):
        IFMsFiltered = np.copy(IFMs)
        i = 0
        for IFM in IFMs:
            noiseLevel = np.median(abs(IFM))/ 0.6745
            threshold = noiseLevel * np.sqrt(2*np.log(IFM.shape[0]))
            if thresholding == "hard":
                IFMsFiltered[i] = (abs(IFM) > threshold) * IFM
            elif thresholding == "soft":
                IFMsFiltered[i] = pywt.threshold(IFM, threshold,'soft')
            i+=1
        if verbose:
            self.showIFMs(IFMsFiltered)
        print(IFMs)
        print(IFMsFiltered)
        return IFMsFiltered
    
    def parseIFMsToSignal(self, originalSignal, IFMs):
        signalToReturn = np.copy(originalSignal)
        signalToReturn[:,-1] = np.zeros(originalSignal.shape[0])
        for IFM in IFMs:
            signalToReturn[:,-1] += IFM
        return signalToReturn

    def denoise(self, signal):
        return signal