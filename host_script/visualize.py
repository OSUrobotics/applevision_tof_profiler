from pathlib import Path
import itertools
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d import art3d, Axes3D

DATA = Path(__file__).parent.joinpath('../data')
# DATA = Path(__file__).parent.joinpath('apple30mm.csv')

if __name__ == '__main__':

    for p in DATA.iterdir():
        if not p.is_file() or p.suffix != '.csv':
            continue
        
        df = pd.read_csv(p)


        # average every distance
        df = df.groupby(['x', 'y'], as_index=False).median()
        mindist = df['lidar'].min()
        maxdist = df['lidar'].max()
        # df['lidar'] = 1024 - df['lidar']

        # convert to mesh grid
        x_vals = df['x'].unique()
        y_vals = df['y'].unique()
        x, y = np.meshgrid(x_vals, y_vals)
        z = np.zeros(x.shape)

        for (ix, vx), (iy, vy) in itertools.product(enumerate(x_vals), enumerate(y_vals)):
            z[iy, ix] = df[(df['x'] == vx) & (df['y'] == vy)]['lidar'].iloc[0]


        fig = plt.figure()
        ax = plt.axes(projection='3d')
        ax.plot_surface(x, y, z, rstride=1, cstride=1, cmap='viridis', edgecolor='none')
        ax.set_title(f'{p.stem} min={mindist} max={maxdist}')
        
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