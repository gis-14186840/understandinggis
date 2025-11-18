from numpy import zeros, column_stack
from rasterio import open as rio_open
from skimage.draw import line, circle_perimeter

from sys import exit

from skimage.draw import line, circle_perimeter

from math import floor, ceil, hypot
from geopandas import GeoSeries
from shapely.geometry import Point
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from rasterio.plot import show as rio_show
from matplotlib.pyplot import subplots, savefig
from matplotlib_scalebar.scalebar import ScaleBar
from matplotlib.colors import LinearSegmentedColormap

# Function to convert coordinate space (x,y) to image space (row,col)
def coords_2_img(x, y, transform):
    """Convert (x,y) coordinates to (row,col) in image space"""
    col, row = ~transform * (x, y)  # Use inverse transform
    return int(round(row)), int(round(col))  # Return as integers
        
           
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
    
    # Create output raster
    output = zeros(dem_data.shape, dtype=dem_data.dtype)
    output[r0, c0] = 1  # Origin is visible

    # get pixels in the perimeter of the viewshed
    for r, c in column_stack(circle_perimeter(r0, c0, radius_px)):

	   # calculate line of sight to each pixel, pass output and get a new one back each time
        output = line_of_sight(r0, c0, height0, r, c, target_height, radius_px, dem_data, transform, output)

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
    




# output image
fig, my_ax = subplots(1, 1, figsize=(16, 10))
my_ax.set_title("Viewshed Analysis")

# draw dem
rio_show(
	dem_data,
	ax=my_ax,
	transform = dem.transform,
	cmap = 'viridis',
	)

# draw dem as contours
rio_show(
	dem_data,
	ax=my_ax,
	contour=True,
	transform = dem.transform,
	colors = ['white'],
	linewidths = [0.5],
	)

# add viewshed
rio_show(
	output,
	ax=my_ax,
	transform=dem.transform,
	cmap = LinearSegmentedColormap.from_list('binary_viewshed', [(0, 0, 0, 0), (1, 0, 0, 0.5)], N=2)
	)

# add origin point
GeoSeries(Point(x0, y0)).plot(
	ax = my_ax,
	markersize = 60,
	color = 'black',
	edgecolor = 'white'
	)

# add a colour bar
fig.colorbar(ScalarMappable(norm=Normalize(vmin=floor(dem_data.min()), vmax=ceil(dem_data.max())), cmap='viridis'), ax=my_ax, pad=0.01)

# add north arrow
x, y, arrow_length = 0.97, 0.99, 0.1
my_ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
	arrowprops=dict(facecolor='black', width=5, headwidth=15),
	ha='center', va='center', fontsize=20, xycoords=my_ax.transAxes)

# add scalebar
my_ax.add_artist(ScaleBar(dx=1, units="m", location="lower right"))

# add legend for point
my_ax.legend(
	handles=[
		Patch(facecolor=(1, 0, 0, 0.5), edgecolor=None, label=f'Visible Area'),
		Line2D([0], [0], marker='o', color=(1,1,1,0), label='Viewshed Origin', markerfacecolor='black', markersize=8)
	], loc='lower left')

# save the result
savefig('./out/7.png', bbox_inches='tight')
print("done!")