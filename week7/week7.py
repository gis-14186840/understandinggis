from rasterio import open as rio_open

from rasterio.transform import rowcol, xy

from rasterio.plot import show as rio_show
from matplotlib.pyplot import subplots, savefig

from numpy import zeros

from matplotlib.colors import LinearSegmentedColormap

def coord_2_img(transform, x, y):
    """ 
    * Convert from coordinate space to image space using the 
    * 	Affine transform object from a rasterio dataset
    *
    * Note that rowcol() returns floats so they need to be 
    * 	converted to integers to be used as cell references
    """
    r, c = rowcol(transform, x, y)
    return (int(r), int(c))

# open a raster file into a variable called dem
with rio_open('E:/Manchester/UGIS/data/helvellyn/Helvellyn-50.tif') as dem:

	# everything inside the with block can access dem
    # once you leave the block, the file automatically closes for you
    
    # test the dataset has been opened successfully
    # print(dem.profile)
    
    # get the single data band from a dem
    band_1 = dem.read(1)
    
    # define Helvellyn coordinates
    summit_x = 334170
    summit_y = 515165
    
    # transfor coordinate
    summit_row, summit_col = coord_2_img(dem.transform, summit_x, summit_y)
    
    # print result
    summit_elevation = band_1[summit_row][summit_col]
    print(f"\nHelvellyn elevation：{summit_elevation:.0f}m")
    
    
# part 2    

    # plot the dataset
    fig, my_ax = subplots(1, 1, figsize=(16, 10))
    
    # add the DEM
    rio_show(
      band_1,
      ax=my_ax,
      transform = dem.transform,
    )
    
    # create a new 'band' of raster data the same size
    output = zeros(band_1.shape)
    
    # Plot flooded areas
    cmap = LinearSegmentedColormap.from_list('binary', [(0, 0, 0, 0), (0, 0.5, 1, 0.5)], N=2)
    
    # add the empty layer
    rio_show(
        output,
        ax=my_ax,
        transform=dem.transform,
        cmap=cmap)

# save the resulting map
savefig('./out/6.png', bbox_inches='tight')