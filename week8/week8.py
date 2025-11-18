from numpy import zeros, column_stack
from rasterio import open as rio_open
from rasterio.plot import show as rio_show
from matplotlib.pyplot import subplots, savefig
from matplotlib.colors import LinearSegmentedColormap, Normalize
from skimage.draw import line, circle_perimeter

from sys import exit

from math import hypot, floor, ceil

from matplotlib.cm import ScalarMappable
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib_scalebar.scalebar import ScaleBar
from geopandas import GeoSeries
from shapely.geometry import Point
from skimage.draw import line, circle_perimeter

# Function to convert coordinate space (x,y) to image space (row,col)
def coords_2_img(x, y, transform):
    """Convert (x,y) coordinates to (row,col) in image space"""
    col, row = ~transform * (x, y)  # Use inverse transform
    return int(round(row)), int(round(col))  # Return as integers

# open the elevation data file
with rio_open("E:/Manchester/UGIS/data/helvellyn/Helvellyn-50.tif") as dem:

    # read the data out of band 1 in the dataset
    dem_data = dem.read(1) # COMPLETE THIS LINE

    # create a new 'band' of raster data the same size
    output = zeros(dem_data.shape, dtype=dem_data.dtype) # COMPLETE THIS LINE
    
    # Draw a point at (334170, 515165)
    x_point, y_point = 334170, 515165
    row, col = coords_2_img(x_point, y_point, dem.transform)
    output[row, col] = 1  # Set point to 1 (red)
    
    # Draw a line 50 pixels east from the point
    line_rows, line_cols = line(row, col, row, col + 50)
    for r, c in zip(line_rows, line_cols):
        output[r, c] = 1  # Set line pixels to 1
    
    # print(line(row, col, row, col+50))
    # print(column_stack(line(row, col, row, col+50)))
    
    # Draw a circle with 50px radius around the point
    circle_rows, circle_cols = circle_perimeter(row, col, 50)
    for r, c in zip(circle_rows, circle_cols):
        # Ensure circle stays within raster bounds
        if 0 <= r < output.shape[0] and 0 <= c < output.shape[1]:
            output[r, c] = 1  # Set circle pixels to 1
            
           
# Viewshed main function
def viewshed(x0, y0, radius_m, observer_height, target_height, dem_data, transform):
    # Convert origin to image space
    r0, c0 = coords_2_img(x0, y0, transform)
    
    # make sure that we are within the dataset
    if not (0 <= r0 < dem_data.shape[0] and 0 <= c0 < dem_data.shape[1]):
        print(f"Sorry: {x0, y0} is not within the elevation dataset.")
        exit()
        
    # convert the radius (m) to pixels
    radius_px = int(radius_m / transform[0])
    
    # get the observer height (above sea level)
    height0 = dem_data[r0, c0] + observer_height
    print(f"Observer elevation: {height0:.1f} m")
    
    # get pixels in the perimeter of the viewshed
    for r, c in column_stack(circle_perimeter(r0, c0, radius_px)):

	   # calculate line of sight to each pixel, pass output and get a new one back each time
	   #output = line_of_sight(r0, c0, height0, r, c, target_height, radius_px, dem_data, transform, output)
       pass

    # return the resulting viewshed
    return output

# The line_of_sight() function
def line_of_sight(r0, c0, height0, r1, c1, target_height, radius, dem_data, transform, output):
    # Initialize max slope tracker
    max_dydx = -float('inf')

    # Get line pixels (exclude first pixel)
    line_pixels = column_stack(line(r0, c0, r1, c1))[1:]

    # Loop through line pixels
    for r, c in line_pixels:
        # Calculate distance (pixels) from origin
        dx = hypot(r - r0, c - r0)

        # if we go too far, or go off the edge of the data, stop looping
        if dx > radius or not 0 <= r < dem_data.shape[0] or not 0 <= c < dem_data.shape[1]:
            break

        # calculate the current value for dy / dx
        base_dydx = (dem_data[(r, c)] - height0) / dx
        tip_dydx = (dem_data[(r, c)] + target_height - height0) / dx

        # if the tip dydx is bigger than the previous max, it is visible
        if (tip_dydx > max_dydx):
            output[(r, c)] = 1

		# if the base dydx is bigger than the previous max, update
        max_dydx = max(max_dydx, base_dydx)

    # return updated output surface
    return output
            
# Main execution
if __name__ == "__main__":
    # Load DEM data
    with rio_open("E:/Manchester/UGIS/data/helvellyn/Helvellyn-50.tif") as dem:
        dem_data = dem.read(1)
        dem_transform = dem.transform
    
    # Viewshed parameters
    x0, y0 = 330000, 512500  # Origin coordinates
    radius_m = 20000          # 20 km radius
    observer_height = 1.8     # 1.8 m observer height
    target_height = 100       # 100 m target height
    
    # calculate the viewshed
    output = viewshed(x0, y0, 20000, 1.8, 100, dem_data, dem.transform)