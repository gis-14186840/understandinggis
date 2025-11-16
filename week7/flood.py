from numpy import zeros
from rasterio import open as rio_open
from rasterio.transform import rowcol
from rasterio.plot import show as rio_show
from matplotlib.pyplot import subplots, savefig
from matplotlib.colors import LinearSegmentedColormap

def coord_2_img(transform, x, y):
	""" 
	* Convert from coordinate space to image space using the 
	*   Affine transform object from a rasterio dataset
	"""
	r, c = rowcol(transform, x, y)
	return int(r), int(c)

def flood_fill(depth, x0, y0, dem_data, transform):
    """
    * Implement flood fill algorithm to determine flooded areas
    * based on elevation and flood depth
    """

    # create a new dataset of 0's
    flood_layer = zeros(dem_data.shape)
    
    # convert from coordinate space to image space
    r0, c0 = coord_2_img(transform, x0, y0)
    
    # set for cells already assessed
    assessed = set()

    # set for cells to be assessed
    to_assess = set()
    
    # start with the origin cell
    to_assess.add((r0, c0))
    
    # calculate the maximum elevation of the flood
    flood_extent = dem_data[r0][c0] + depth
    
# set the depth of the flood
FLOOD_DEPTH = 2

# set origin for the flood as a tuple
LOCATION = (332000, 514000)

# open the raster dataset
with rio_open("E:/Manchester/UGIS/data/helvellyn/Helvellyn-50.tif") as dem:  # 50m resolution

    # read the data out of band 1 in the dataset
    dem_data = dem.read(1)
    
    # calculate the flood
    output = flood_fill(FLOOD_DEPTH, LOCATION[0], LOCATION[1], dem_data, dem.transform)
    
