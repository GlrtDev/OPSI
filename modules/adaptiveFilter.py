import padasip as pa
import numpy as np
"""
https://matousc89.github.io/padasip/sources/filters/lms.html
"""

# we pass noise sample to predict noise and then substract it from the signal
# n is the size (number of taps) of the filter.

class AdaptiveFilterLMS:
    @staticmethod
    def denoise(x, mu, d, n=2):
        # n - length of filter
        # mu - learning rate
        # w - initial weights
        # f = pa.filters.FilterLMS(n=len(x[0]), mu=mu, w="random")
        
        newX = pa.input_from_history(x[:,-1],n)
        f = pa.filters.FilterLMS(n=n, mu=mu, w="random")

        d = d[:-(n-1),-1]

        y, e, w = f.run(d, newX)

        signalDenoised = np.copy(x)
        signalDenoised[:,-1] -= np.append(y,[0 for i in range(n-1)])

        return signalDenoised



