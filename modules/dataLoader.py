import numpy as np
import wfdb


class DataLoader:
    def is_float(string):
        """ True if given string is float else False"""
        try:
            return float(string)
        except ValueError:
            return False

    @staticmethod
    def load(path):
        data, attr = wfdb.rdsamp(path, channels=[2])
        n = len(data)

        f_sampling = attr["fs"]
        fstep = 1 / f_sampling
        freqs = np.reshape(np.arange(n) * fstep, (n, 1))  # times

        data = np.append(freqs, data, axis=1)
        data = data[1:]
        data[:,-1] = np.nan_to_num(data[:,-1])
        data[:,-1] = np.true_divide(data[:,-1], (1000000/96.9408))

        return data
