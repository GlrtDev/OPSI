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
        data, attr = wfdb.rdsamp(path, channels=[0])
        n = len(data)
        #data = np.loadtxt(path, dtype=float)
        f_sampling = attr["fs"]
        fstep = 1 / f_sampling
        freqs = np.reshape(np.arange(n) * fstep, (n, 1)) # times
        print(f"freqs = {freqs}")
        print(f"dataPreed = {data}")
        data = np.append(freqs,data ,axis=1)
        print(f"dataPooo = {data}")
        data = data[1:]
        return data
