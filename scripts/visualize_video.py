"""Generate a video rotating a 3D surface plot of an apple scan. Requires FFMPEG to be installed."""

from pathlib import Path
import itertools
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from mpl_toolkits.mplot3d import art3d, Axes3D

DATA = Path(__file__).parent.joinpath('../data')
SENSOR = 'lidar'

if __name__ == '__main__':
    for p in DATA.iterdir():
        if not p.is_file() or p.suffix != '.csv':
            continue
        
        df = pd.read_csv(p)

        # average every distance
        df = df.groupby(['x', 'y'], as_index=False).median()
        mindist = df[SENSOR].min()
        maxdist = df[SENSOR].max()

        # convert to mesh grid
        x_vals = df['x'].unique()
        y_vals = df['y'].unique()
        x, y = np.meshgrid(x_vals, y_vals)
        z = np.zeros(x.shape)

        for (ix, vx), (iy, vy) in itertools.product(enumerate(x_vals), enumerate(y_vals)):
            z[iy, ix] = df[(df['x'] == vx) & (df['y'] == vy)][SENSOR].iloc[0]


        max_range = 400
        fig = plt.figure()
        fig.suptitle(f'ToF: {p.stem}', y=.9)
        ax = fig.add_subplot(111, projection='3d')
        surf1 = ax.plot_surface(x, y, z, rstride=1, cstride=1, vmin=0, vmax=max_range, cmap='plasma', edgecolor='none')
        ax.set_zlim(0, max_range)
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')

        fig.colorbar(surf1, shrink=0.5, aspect=5, pad=0.1, label='Measured Distance (mm)')

        def animate(i):
          ax.view_init(azim=i)
          return surf1,

        anim = animation.FuncAnimation(fig, animate, frames=500, blit=True)
        anim.save('basicanimation.mp4', fps=60)

  


       

    # plt.show(block=True)