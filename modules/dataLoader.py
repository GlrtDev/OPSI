import numpy as np

class DataLoader:
    def is_float(string):
        """ True if given string is float else False"""
        try:
            return float(string)
        except ValueError:
            return False

    def load(self, path):        
        data = np.loadtxt(path, dtype=float,delimiter =' ')
        return data

