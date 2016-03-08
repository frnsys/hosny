import math


def ewms(p_mean, p_stddev, val, alpha=0.8):
    """computes exponentially weighted moving statistics (mean, stddev)"""
    mean = p_mean + (alpha * (val - p_mean))
    var = p_stddev**2 + (alpha * (val - p_mean)**2)
    return mean, math.sqrt(var)


def hyperbolic_discount(value, days, k):
    discount = 1/(1+days*k)
    return discount * value
