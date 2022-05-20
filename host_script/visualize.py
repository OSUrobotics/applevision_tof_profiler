from pathlib import Path
import itertools
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d import art3d, Axes3D

DATA = Path(__file__).parent.joinpath('../data')
SENSOR = 'lidar'
# DATA = Path(__file__).parent.joinpath('apple30mm.csv')

if __name__ == '__main__':

    # matplotlib.rcParams.update({'font.size': 18})

    for p in DATA.iterdir():
        if not p.is_file() or p.suffix != '.csv':
            continue
        
        df = pd.read_csv(p)


        # average every distance
        df = df.groupby(['x', 'y'], as_index=False).median()
        mindist = df[SENSOR].min()
        maxdist = df[SENSOR].max()
        # df['lidar'] = 1024 - df['lidar']

        # convert to mesh grid
        x_vals = df['x'].unique()
        y_vals = df['y'].unique()
        x, y = np.meshgrid(x_vals, y_vals)
        z = np.zeros(x.shape)

        for (ix, vx), (iy, vy) in itertools.product(enumerate(x_vals), enumerate(y_vals)):
            z[iy, ix] = df[(df['x'] == vx) & (df['y'] == vy)][SENSOR].iloc[0] # * 10 # TODO: remove


        max_range = 400
        fig = plt.figure()
        fig.set_size_inches(9, 4)
        fig.suptitle(f'ToF: {p.stem}', y=.9)
        ax = fig.add_subplot(121, projection='3d')
        surf1 = ax.plot_surface(x, y, z, rstride=1, cstride=1, vmin=0, vmax=max_range, cmap='plasma', edgecolor='none')
        ax.set_zlim(0, max_range)
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        # ax.set_zlabel(f'')

        ax2 = fig.add_subplot(122, projection='3d')
        surf2 = ax2.plot_surface(x, y, z, rstride=1, cstride=1, vmin=0, vmax=max_range, cmap='plasma', edgecolor='none')
        ax2.set_zlim(0, max_range)
        ax2.set_xlabel('X (mm)')
        ax2.set_ylabel('Y (mm)')
        ax2.set_zticks([])
        ax2.view_init(azim=-90, elev=90)
        
        fig.subplots_adjust(right=0.8)
        cbar_ax = fig.add_axes([0.85, 0.3, 0.05, 0.4])
        fig.colorbar(surf1, cax=cbar_ax, shrink=0.5, aspect=5, pad=0.1, label='Measured Distance (mm)')
        plt.savefig(p.with_suffix('.png').name.replace(' ', '').replace(',', ''), bbox_inches='tight', pad_inches=0, transparent=True)
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

    # plt.show(block=True)