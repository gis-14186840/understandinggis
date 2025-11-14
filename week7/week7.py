from rasterio import open as rio_open

from rasterio.transform import rowcol, xy

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
