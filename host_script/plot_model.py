from pathlib import Path
import itertools
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d import art3d, Axes3D

DATA = Path(__file__).parent.joinpath('../data')
# DATA = Path(__file__).parent.joinpath('apple30mm.csv')

if __name__ == '__main__':
    with open('outjson.json', 'r') as f:
        ray = json.load(f)

    x = np.arange(0, 164, 4)
    xgrid, ygrid = np.meshgrid(x, x)
    z = np.array(ray)

    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.plot_surface(xgrid, ygrid, z, rstride=1, cstride=1, cmap='viridis', edgecolor='none')
    
    # p = Circle((67, 55), 40, ec='k', fc="none")
    # ax.add_patch(p)
    # art3d.patch_2d_to_3d(p, z=100)

    # x=np.linspace(67-40, 67+40, 100)
    # z=np.linspace(0, 255, 100)
    # Xc, Zc=np.meshgrid(x, z)
    # Yc = np.sqrt(40**2 - (Xc - 67)**2) + 55
    # cstride = 10
    # ax.plot_surface(Xc, Yc, Zc, alpha=1, cstride=cstride)
    # ax.plot_surface(Xc, (2*55-Yc), Zc, alpha=1, cstride=cstride)

    plt.show(block=True)