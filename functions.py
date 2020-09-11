import numpy as np

def isosurface(func):
    # Wrapper function
    def inner_func(p):
        x, y, z = p
        return func(x, y, z)
    return inner_func


@isosurface
def sphere(x, y, z):
    return x**2 + y**2 + z**2

def torus(R = 0.5):
    # Torus whose center to tube center is R.
    @isosurface
    def func(x, y, z):
        return (np.sqrt(x**2 + y**2) - R)**2 + z**2
    return func
