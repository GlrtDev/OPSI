import padasip as pa

"""
https://matousc89.github.io/padasip/sources/filters/lms.html
"""


class AdaptiveFilterLMS:
    @staticmethod
    def denoise(x, mu, d):
        # n - length of filter
        # mu - learning rate
        # w - initial weights
        f = pa.filters.FilterLMS(n=len(x[0]), mu=mu, w="random")

        y, e, w = f.run(d, x)

        return y



