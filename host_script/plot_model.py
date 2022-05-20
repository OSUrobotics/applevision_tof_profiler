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
    for fname in ['outjson.json']:
        with open(fname, 'r') as f:
            ray = json.load(f)

        x = np.arange(0, 164, 4)
        xgrid, ygrid = np.meshgrid(x, x)
        z = np.array(ray)

        # fig = plt.figure()
        # ax = plt.axes(projection='3d')
        # ax.plot_surface(xgrid, ygrid, z, rstride=1, cstride=1, cmap='viridis', edgecolor='none')
        # ax.set_zlim(top=400, bottom=200)

        max_range = 1000
        fig = plt.figure()
        fig.set_size_inches(9, 4)
        fig.suptitle(f'Simplified ToF Model: Apple 150mm, Backdrop 1000mm', y=.9)
        ax = fig.add_subplot(121, projection='3d')
        surf1 = ax.plot_surface(xgrid, ygrid, z, rstride=1, cstride=1, vmin=0, vmax=max_range, cmap='plasma', edgecolor='none')
        ax.set_zlim(0, max_range)
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        # ax.set_zlabel(f'')

        ax2 = fig.add_subplot(122, projection='3d')
        surf2 = ax2.plot_surface(xgrid, ygrid, z, rstride=1, cstride=1, vmin=0, vmax=max_range, cmap='plasma', edgecolor='none')
        ax2.set_zlim(0, max_range)
        ax2.set_xlabel('X (mm)')
        ax2.set_ylabel('Y (mm)')
        ax2.set_zticks([])
        ax2.view_init(azim=-90, elev=90)
        
        fig.subplots_adjust(right=0.8)
        cbar_ax = fig.add_axes([0.85, 0.3, 0.05, 0.4])
        fig.colorbar(surf1, cax=cbar_ax, shrink=0.5, aspect=5, pad=0.1, label='Measured Distance (mm)')
        plt.savefig('model.png', bbox_inches='tight', pad_inches=0, transparent=True)

    plt.show(block=True)