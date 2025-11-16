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


# open the raster dataset
with rio_open("E:/Manchester/UGIS/data/helvellyn/Helvellyn-50.tif") as dem:  # 50m resolution

    # read the data out of band 1 in the dataset
    dem_data = dem.read(1)