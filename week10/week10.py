from math import hypot
from time import perf_counter
from geopandas import read_file
from rasterio import open as rio_open
from rasterio.transform import rowcol
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from rasterio.plot import show as rio_show
from matplotlib.pyplot import subplots, savefig
from skimage.draw import line, circle_perimeter
from matplotlib_scalebar.scalebar import ScaleBar
from multiprocessing.shared_memory import SharedMemory
from concurrent.futures import ProcessPoolExecutor, as_completed
from numpy import column_stack, array, dtype, ndarray, nan, intp, sum as np_sum

def coord_2_img(transform, x, y):
    """ 
    * Convert from coordinate space to image space
    """
    r, c = rowcol(transform, x, y)
    return int(r), int(c)


def line_of_sight_coords(r0, c0, z0, r1, c1, radius, dsm_data):
    """
    * Use Bresenham's Line algorithm to calculate a line of sight from one point to another point, 
    *	returning a list of visible cells
    """
    
    # init variable for biggest dydx so far (starts at -infinity)
    max_dydx = -float('inf')
    
    # iterate along integer raster cells on line from observer to target
    visible_coords = []
    for r, c in column_stack(line(r0, c0, r1, c1))[1:]: # skip the observer cell itself
        
        # distance in pixels from observer (Euclidean)
        dx = hypot(c0 - c, r0 - r)

        # if we go too far, or go off the edge of the data, stop looping
        if dx > radius or not (0 <= r < dsm_data.shape[0]) or not (0 <= c < dsm_data.shape[1]):
            break

        # slope from observer to the *top* of this cell
        cur_dydx =  (dsm_data[r, c] - z0) / dx

        # if this slope is greater than any previous slope, this cell is visible
        if cur_dydx > max_dydx:
            visible_coords.append((int(r), int(c)))

            # update max_slope to block further lower-angle points
            max_dydx = cur_dydx

    return visible_coords