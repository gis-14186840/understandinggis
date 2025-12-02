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

def line_of_sight_coords(r0, c0, z0, r1, c1, radius, dsm_data, start_idx=1, initial_max_dydx=-float('inf')):
    """
    * Optimized Line of Sight calculation (Brinkmann et al., 2022)
    * Use Bresenham's Line algorithm with support for shared path reuse
    * start_idx: index to start processing (skips shared prefix)
    * initial_max_dydx: max slope from shared prefix (avoids recalculation)
    * Returns: (visible_coords, final_max_dydx)
    """
    max_dydx = initial_max_dydx
    
    visible_coords = []
    # Get full path and start from specified index
    full_path = column_stack(line(r0, c0, r1, c1))[start_idx:]
    
    for r, c in full_path:
        # Distance in pixels from observer (Euclidean)
        dx = hypot(c0 - c, r0 - r)

        # Stop if out of bounds or beyond radius
        if dx > radius or not (0 <= r < dsm_data.shape[0]) or not (0 <= c < dsm_data.shape[1]):
            break

        # Slope from observer to the top of this cell
        cur_dydx = (dsm_data[r, c] - z0) / dx

        # If slope is greater than previous max, cell is visible
        if cur_dydx > max_dydx:
            visible_coords.append((int(r), int(c)))
            max_dydx = cur_dydx

    return visible_coords, max_dydx

def attach_shared_memory(shm_name, shape, dtype_str):
    """
    * Attach to raster dataset in shared memory 
    * Returns: (memory reference, band dataset)
    """
    existing_shm = SharedMemory(name=shm_name)
    shared_data = ndarray(shape, dtype=dtype(dtype_str), buffer=existing_shm.buf)
    return (existing_shm, shared_data)

# Brinkmann et al. (2022) optimization functions
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
    """Return angle-sorted list of unique perimeter points (Brinkmann et al., 2022)."""
    perim = column_stack(circle_perimeter(r0, c0, radius_px))
    seen = set()
    points = []
    for pr, pc in perim:
        pt = (int(pr), int(pc))
        if pt not in seen:
            seen.add(pt)
            points.append(pt)
    # Sort points by angle to ensure consecutive paths have maximum overlap
    points.sort(key=lambda p: atan2(p[0] - r0, p[1] - c0))
    return points

def gvi_worker(x0, y0, radius_m, observer_height, dsm, trees, transform):
    """
    * Calculate Green Visibility Index based on Labib et al. (2021)
    * Optimized with Brinkmann et al. (2022) shared path reuse
    * Note that there is no target height in this case, as we are using the DSM (so it is 0)
    """
    # Connect to shared memory for DSM and trees datasets
    existing_dsm_shm, dsm_data = attach_shared_memory(*dsm)
    existing_trees_shm, trees_data = attach_shared_memory(*trees)
    
    try:
        # Convert observer location to raster row/col
        r0, c0 = coord_2_img(transform, x0, y0)
        
        # Catch if the point is outside the dataset bounds
        if not (0 <= r0 < dsm_data.shape[0]) or not (0 <= c0 < dsm_data.shape[1]):
            print(f"ERROR: data point {x0},{y0} outside of dataset")
            return None

        # Calculate radius in pixels (assumes square pixels)
        radius_px = int(radius_m / abs(transform[0]))

        # Observer absolute elevation (DSM value + observer height)
        observer_abs_elev = dsm_data[r0, c0] + observer_height

        # Collect visible coords in a set to avoid duplicates
        visible = set()
        visible.add((int(r0), int(c0)))  # Add observer location

        # Get angle-sorted perimeter points (Brinkmann optimization step 1)
        sorted_points = build_sorted_perimeter_endpoints(r0, c0, radius_px)
        
        # Track previous path data for shared prefix reuse (Brinkmann optimization step 2)
        prev_path = None
        prev_max_dydx = -float('inf')

        # Iterate through sorted perimeter points to cast rays
        for rr, cc in sorted_points:
            # Compute full Bresenham path for current target
            current_path = compute_bresenham_path(r0, c0, rr, cc)
            
            if prev_path is not None:
                # Find length of shared prefix between current and previous path
                prefix_len = longest_common_prefix_len(prev_path, current_path)
                # Start calculation from end of shared prefix, reuse previous max slope
                new_visible, current_max_dydx = line_of_sight_coords(
                    r0, c0, observer_abs_elev, rr, cc, radius_px, dsm_data,
                    start_idx=prefix_len, initial_max_dydx=prev_max_dydx
                )
            else:
                # First path: no shared prefix, start from beginning
                new_visible, current_max_dydx = line_of_sight_coords(
                    r0, c0, observer_abs_elev, rr, cc, radius_px, dsm_data
                )
            
            # Add new visible cells to the set
            for rc in new_visible:
                visible.add(rc)
            
            # Update previous path data for next iteration
            prev_path = current_path
            prev_max_dydx = current_max_dydx

        # Convert visible coords to numpy arrays for fast indexing
        rows, cols = zip(*visible)
        rows = array(rows, dtype=intp)
        cols = array(cols, dtype=intp)

        # Count visible tree pixels (trees_data == 1 indicates tree coverage)
        visible_trees = np_sum(trees_data[rows, cols] == 1)

        # Return GVI (proportion of visible cells that are trees)
        return visible_trees / float(len(rows))
    
    finally:
        # Close shared memory connections (DO NOT unlink - other processes may need it)
        existing_dsm_shm.close()
        existing_trees_shm.close()

# Main code block
if __name__ == "__main__":
    # Load datasets with nested with blocks for proper resource management
    with rio_open("E:/Manchester/UGIS/data/bolton/bolton_dsm.tif") as dsm, \
         rio_open("E:/Manchester/UGIS/data/bolton/bolton_trees_resample.tif") as trees:
        
        # Read raster data bands (1 band each for DSM and trees)
        dsm_data = dsm.read(1)
        trees_data = trees.read(1)
        
        # Load primary schools shapefile into GeoDataFrame
        schools = read_file("E:/Manchester/UGIS/data/bolton/primary_schools.shp")
        
        # Verify EPSG code consistency across all datasets
        dsm_epsg = dsm.crs.to_epsg()
        trees_epsg = trees.crs.to_epsg()
        schools_epsg = schools.crs.to_epsg()
        print(f"DSM EPSG: {dsm_epsg}, Trees EPSG: {trees_epsg}, Schools EPSG: {schools_epsg}")
        assert dsm_epsg == trees_epsg == schools_epsg, "EPSG codes do not match! Aborting."
        
        # Start performance timer to measure total runtime
        start = perf_counter()
        
        # Use try-finally block to ensure shared memory cleanup
        try:
            # Create shared memory for DSM dataset
            dsm_nbytes = dsm_data.size * dsm_data.dtype.itemsize
            dsm_shm = SharedMemory(create=True, size=dsm_nbytes)
            dsm_shared_arr = ndarray(dsm_data.shape, dtype=dsm_data.dtype, buffer=dsm_shm.buf)
            dsm_shared_arr[:] = dsm_data[:]  # Copy data to shared memory
            
            # Create shared memory for trees dataset
            trees_nbytes = trees_data.size * trees_data.dtype.itemsize
            trees_shm = SharedMemory(create=True, size=trees_nbytes)
            trees_shared_arr = ndarray(trees_data.shape, dtype=trees_data.dtype, buffer=trees_shm.buf)
            trees_shared_arr[:] = trees_data[:]  # Copy data to shared memory
            
            # Initialize tasks list: tuple (school index, arguments dictionary)
            tasks = []
            for idx, row in schools.iterrows():
                tasks.append((idx, {
                    'x0': row.geometry.x,          # X coordinate of school
                    'y0': row.geometry.y,          # Y coordinate of school
                    'radius_m': 800,               # Visibility radius in meters
                    'observer_height': 1.7,        # Typical observer height (1.7m)
                    'dsm': (dsm_shm.name, dsm_data.shape, str(dsm_data.dtype)),  # DSM shared memory info
                    'trees': (trees_shm.name, trees_data.shape, str(trees_data.dtype)),  # Trees shared memory info
                    'transform': dsm.transform     # Affine transform for coordinate conversion
                }))
            
            # Launch parallel processes using ProcessPoolExecutor
            with ProcessPoolExecutor() as executor:
                # Map Future objects to school indices for result assignment
                future_map = {}
                for task in tasks:
                    idx, args = task
                    # Submit task to executor with dictionary expansion (**args)
                    future = executor.submit(gvi_worker, **args)
                    future_map[future] = idx
                
                # Report number of launched processes (depends on CPU core count)
                print(f"Launched {len(executor._processes)} processes...")
                
                # Process results as they complete (non-blocking)
                for future in as_completed(future_map.keys()):
                    idx = future_map[future]
                    try:
                        # Get GVI result and assign to corresponding school row
                        gvi_value = future.result()
                        schools.loc[idx, "gvi"] = gvi_value
                    except Exception as e:
                        # Handle exceptions gracefully without crashing the entire script
                        print(f"ERROR: Worker raised an exception for school index {idx}: {e}")
                        schools.loc[idx, "gvi"] = nan
            
            # Print summary results
            print(f"\n{len(schools.index)} Schools analysed in {perf_counter() - start:.2f} seconds.")
            print("\nTop 10 Schools by GVI (Brinkmann Optimized):")
            print(schools[["name", "gvi"]].sort_values("gvi", ascending=False).head(10).round(4))
            
            # Generate and save GVI visualization map
            fig, my_ax = subplots(1, 1, figsize=(16, 10))
            my_ax.set_title("Green Visibility Index (GVI) per School - Brinkmann Optimized", fontsize=16)
            
            # Plot trees raster as transparent background
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
                cbar = fig.colorbar(
                    ScalarMappable(norm=Normalize(vmin=schools["gvi"].min(), vmax=schools["gvi"].max()), cmap='Greens'),
                    ax=my_ax,
                    pad=0.01,
                    label="GVI (Proportion of Visible Tree Pixels)"
                )
                cbar.ax.tick_params(labelsize=10)
            
            # Add north arrow
            x, y, arrow_length = 0.97, 0.99, 0.1
            my_ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
                arrowprops=dict(facecolor='black', width=5, headwidth=15),
                ha='center', va='center', fontsize=20, xycoords=my_ax.transAxes)
            
            # Add scale bar (meters)
            my_ax.add_artist(ScaleBar(dx=1, units="m", location="lower right", scale_loc="bottom"))
            
            # Save plot to output directory (ensure ./out exists)
            savefig('./out/9_brinkmann_optimized.png', bbox_inches='tight', dpi=300)
            print("\nOptimized GVI map saved to ./out/9_brinkmann_optimized.png")
        
        finally:
            # Critical: Clean up shared memory (close and unlink)
            dsm_shm.close()
            dsm_shm.unlink()
            trees_shm.close()
            trees_shm.unlink()