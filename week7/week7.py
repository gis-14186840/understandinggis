from rasterio import open as rio_open
# open a raster file into a variable called dem
with rio_open('./data/helvellyn/Helvellyn-50.tif') as dem:

	# everything inside the with block can access dem
  
# once you leave the block, the file automatically closes for you
print(dem.profile)