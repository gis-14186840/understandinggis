from math import hypot, atan2
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


def attach_shared_memory(shm_name, shape, dtype_str):
    """
    * Attach to raster dataset in shared memory 
    * Returns: (memory reference, band dataset)
    """
    # get reference to memory location of the shared dataset
    existing_shm = SharedMemory(name=shm_name)
    
    # construct a numpy array object using that location in memory
    shared_data = ndarray(shape, dtype=dtype(dtype_str), buffer=existing_shm.buf)
    
    # return a tuple in the form (memory reference, numpy array)
    return (existing_shm, shared_data)

def gvi_worker(x0, y0, radius_m, observer_height, dsm, trees, transform):
    """
    * Calculate Green Visibility Index based on Labib et al. (2021)
    *   Note that there is no target height in this case, as we are using 
    *   the DSM (so it is 0).
    """
    # Connect to shared memory for DSM and trees datasets
    existing_dsm_shm, dsm_data = attach_shared_memory(*dsm)
    existing_trees_shm, trees_data = attach_shared_memory(*trees)
    
    try:
        # convert observer location to raster row/col
        r0, c0 = coord_2_img(transform, x0, y0)
        
        # catch if the dataset is outside the dataset
        if not (0 <= r0 < dsm_data.shape[0]) or not (0 <= c0 < dsm_data.shape[1]):
            print(f"ERROR: data point {x0},{y0} outside of dataset")
            return None

        # radius in pixels (use absolute of pixel x-scale; assumes square pixels)
        radius_px = int(radius_m / abs(transform[0]))

        # observer absolute elevation: DSM value at observer plus observer height
        observer_abs_elev = dsm_data[r0, c0] + observer_height

        # collect visible coords in a set (to avoid duplicates)
        visible = set()

        # add the observer location
        visible.add((int(r0), int(c0)))

        # iterate perimeter points to cast rays
        for rr, cc in column_stack(circle_perimeter(r0, c0, radius_px)):

            # for each line, get visible coords and add to set
            for rc in line_of_sight_coords(r0, c0, observer_abs_elev, int(rr), int(cc), radius_px, dsm_data):
                visible.add(rc)

        # convert to numpy arrays for fast indexing and ensure indices are valid
        rows, cols = zip(*visible)
        rows = array(rows, dtype=intp) # intp is a convenient alias for the default integer type used by the system
        cols = array(cols, dtype=intp)

        # count visible tree pixels
        visible_trees = np_sum(trees_data[rows, cols] == 1)

        # return GVI value (proportion of visible cells that are tree pixels)
        return visible_trees / float(len(rows))
    
    finally:
        # Close connections to shared memory (do NOT unlink - other processes may still need it)
        existing_dsm_shm.close()
        existing_trees_shm.close()

# Optional: Brinkmann et al. (2022) optimization functions (uncomment to use)
def compute_bresenham_path(r0, c0, r1, c1):
    """Return list of (r,c) for Bresenham line including both endpoints."""
    rr, cc = line(r0, c0, r1, c1)
    return list(zip(rr, cc))

def longest_common_prefix_len(a, b):
    """Length of longest common prefix of two sequences."""
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i

def build_sorted_perimeter_endpoints(r0, c0, radius_px):
    """Return angle-sorted list of unique perimeter points."""
    perim = column_stack(circle_perimeter(r0, c0, radius_px))
    seen = set()
    points = []
    for pr, pc in perim:
        pt = (int(pr), int(pc))
        if pt not in seen:
            seen.add(pt)
            points.append(pt)
    points.sort(key=lambda p: atan2(p[0] - r0, p[1] - c0))
    return points

# main code block
if __name__ == "__main__":
    # Load datasets and initialize variables
    with rio_open("E:/Manchester/UGIS/data/bolton/bolton_dsm.tif") as dsm, \
         rio_open("E:/Manchester/UGIS/data/bolton/bolton_trees_resample.tif") as trees:
        
        # Read raster data bands
        dsm_data = dsm.read(1)
        trees_data = trees.read(1)
        
        # Load schools shapefile
        schools = read_file("E:/Manchester/UGIS/data/bolton/primary_schools.shp")
        
        # Verify EPSG code consistency
        dsm_epsg = dsm.crs.to_epsg()
        trees_epsg = trees.crs.to_epsg()
        schools_epsg = schools.crs.to_epsg()
        print(f"DSM EPSG: {dsm_epsg}, Trees EPSG: {trees_epsg}, Schools EPSG: {schools_epsg}")
        assert dsm_epsg == trees_epsg == schools_epsg, "EPSG codes do not match!"
        
        # Start performance timer
        start = perf_counter()
        
        # Use try-finally block to ensure shared memory cleanup
        try:
            # Put DSM in shared memory
            dsm_nbytes = dsm_data.size * dsm_data.dtype.itemsize
            dsm_shm = SharedMemory(create=True, size=dsm_nbytes)
            dsm_shared_arr = ndarray(dsm_data.shape, dtype=dsm_data.dtype, buffer=dsm_shm.buf)
            dsm_shared_arr[:] = dsm_data[:]
            
            # Put trees data in shared memory
            trees_nbytes = trees_data.size * trees_data.dtype.itemsize
            trees_shm = SharedMemory(create=True, size=trees_nbytes)
            trees_shared_arr = ndarray(trees_data.shape, dtype=trees_data.dtype, buffer=trees_shm.buf)
            trees_shared_arr[:] = trees_data[:]
            
            # Initialize tasks list (tuple: (school index, arguments dictionary))
            tasks = []
            for idx, row in schools.iterrows():
                # Complete task arguments: x0/y0 from school geometry, trees shared memory info
                tasks.append((idx, {
                    'x0': row.geometry.x,
                    'y0': row.geometry.y,
                    'radius_m': 800,
                    'observer_height': 1.7,
                    'dsm': (dsm_shm.name, dsm_data.shape, str(dsm_data.dtype)),
                    'trees': (trees_shm.name, trees_data.shape, str(trees_data.dtype)),
                    'transform': dsm.transform
                }))
            
            # Launch parallel processes using ProcessPoolExecutor
            with ProcessPoolExecutor() as executor:
                # Map Future objects to school indices for result assignment
                future_map = {}
                for task in tasks:
                    idx, args = task
                    # Submit task to executor with dictionary expansion
                    future = executor.submit(gvi_worker, **args)
                    future_map[future] = idx
                
                # Report number of launched processes
                print(f"Launched {len(executor._processes)} processes...")
                
                # Process results as they complete
                for future in as_completed(future_map.keys()):
                    idx = future_map[future]
                    try:
                        # Get GVI result and assign to corresponding school row
                        gvi_value = future.result()
                        schools.loc[idx, "gvi"] = gvi_value
                    except Exception as e:
                        # Handle exceptions without crashing the entire script
                        print(f"ERROR: Worker raised an exception for school index {idx}: {e}")
                        schools.loc[idx, "gvi"] = nan
            
            # Report completion and performance
            print(f"\n{len(schools.index)} Schools analysed in {perf_counter() - start:.2f} seconds.")
            print("\nGVI Results Summary:")
            print(schools[["name", "gvi"]].sort_values("gvi", ascending=False).head(10))
            
            # Plot GVI results map
            fig, my_ax = subplots(1, 1, figsize=(16, 10))
            my_ax.set_title("Green Visibility Index (GVI) per school")
            
            # Show trees raster as transparent background
            rio_show(
                trees,
                ax=my_ax,
                transform=trees.transform,
                cmap='Greens',
                alpha=0.4,
            )
            
            # Plot schools colored by GVI value
            schools.plot(
                ax=my_ax,
                column='gvi',
                cmap='Greens',
                markersize=120,
                edgecolor='black',
                missing_kwds={"color": "gray", "label": "No GVI Data"}
            )
            
            # Add color bar if there are valid GVI values
            if schools["gvi"].notna().any():
                fig.colorbar(
                    ScalarMappable(norm=Normalize(vmin=schools["gvi"].min(), vmax=schools["gvi"].max()), cmap='Greens'),
                    ax=my_ax,
                    pad=0.01,
                    label="GVI (Proportion of Visible Tree Pixels)"
                )
            
            # Add north arrow
            x, y, arrow_length = 0.97, 0.99, 0.1
            my_ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
                arrowprops=dict(facecolor='black', width=5, headwidth=15),
                ha='center', va='center', fontsize=20, xycoords=my_ax.transAxes)
            
            # Add scalebar
            my_ax.add_artist(ScaleBar(dx=1, units="m", location="lower right"))
            
            # Save plot to output directory
            savefig('./out/9.png', bbox_inches='tight')
            print("\nGVI map saved to ./out/9.png")
        
        finally:
            # Ensure shared memory is closed and cleaned up
            dsm_shm.close()
            dsm_shm.unlink()
            trees_shm.close()
            trees_shm.unlink()