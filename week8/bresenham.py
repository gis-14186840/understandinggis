from numpy import zeros
from rasterio import open as rio_open
from rasterio.plot import show as rio_show
from matplotlib.pyplot import subplots, savefig
from matplotlib.colors import LinearSegmentedColormap

# open the elevation data file
with rio_open("E:/Manchester/UGIS/data/helvellyn/Helvellyn-50.tif") as dem:

    # read the data out of band 1 in the dataset
    dem_data = dem.read(1) # COMPLETE THIS LINE

    # create a new 'band' of raster data the same size
    output = zeros(dem_data.shape, dtype=dem_data.dtype) # COMPLETE THIS LINE

# plot the dataset
fig, my_ax = subplots(1, 1, figsize=(16, 10))

# add the DEM
rio_show(
  dem_data,
  ax=my_ax,
  transform = dem.transform,
)
# add the drawing layer
rio_show(
    output,
    ax=my_ax,
    transform=dem.transform,
    cmap = LinearSegmentedColormap.from_list('binary_viewshed', [(0, 0, 0, 0), (1, 0, 0, 0.5)], N=2)
    )
savefig('./out/bresenham.png', bbox_inches='tight')