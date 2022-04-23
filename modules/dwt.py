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
        coeff = pywt.wavedec(signal, wavelet, mode="per")

        sigma = (1 / 0.6745) * madev(coeff[-level])
        # Calculate the universal threshold
        uthresh = sigma * np.sqrt(2 * np.log(len(signal)))

        coeff[1:] = (pywt.threshold(i, value=uthresh, mode='hard') for i in coeff[1:])

        # Reconstruct the signal using the thresholded coefficients
        return pywt.waverec(coeff, wavelet, mode='per')
