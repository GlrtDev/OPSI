from PyEMD import EMD, EEMD, CEEMDAN, Visualisation
from enum import Enum

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
            self.visualisation.plot_imfs(IFMs)
            self.visualisation.show()
            print("verbose")
        return IFMs
            

    def denoise(self, signal):
        return signal