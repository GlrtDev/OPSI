import pywt
import numpy as np


def madev(d, axis=None):
    """
    Mean Absolute Deviation
    """
    return np.mean(np.absolute(d - np.mean(d, axis)), axis)


class DWT:
    @staticmethod
    def denoise(signal, wavelet, level):
        # Decompose to get the wavelet coefficients
        signalValues = signal[:, -1]
        coeff = pywt.wavedec(signalValues, wavelet, mode="per")

        sigma = (1 / 0.6745) * madev(coeff[-level])
        # Calculate the universal threshold
        uthresh = sigma * np.sqrt(2 * np.log(len(signalValues)))

        coeff[1:] = (pywt.threshold(i, value=uthresh, mode='hard') for i in coeff[1:])

        # Reconstruct the signal using the thresholded coefficients
        denoisedValues = pywt.waverec(coeff, wavelet, mode='per')
        denoisedSignal = np.copy(signal)
        denoisedSignal[:,-1] = denoisedValues[:-1]

        return denoisedSignal
