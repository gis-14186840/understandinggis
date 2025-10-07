from geopandas import read_file, GeoSeries

from matplotlib.pyplot import subplots, savefig, title

from pyproj import Geod

# load the shapefile of countries - this gives a table of 12 columns and 246 rows (one per country)
world = read_file("E:/Manchester/UGIS/data/natural-earth/ne_10m_admin_0_countries.shp")

# print a list of all of the columns in the shapefile
print(world.columns)

# extract the country rows as a GeoDataFrame object with 1 row
usa = world.loc[(world.ISO_A3 == 'USA')]

print(type(usa))

# extract the geometry columns as a GeoSeries object
usa_col = usa.geometry

print(type(usa_col))

# extract the geometry objects themselves from the GeoSeries
usa_geom = usa_col.iloc[0]

print(type(usa_geom))

# Extract Mexico data
mex = world.loc[(world.ISO_A3 == 'MEX')]
print(type(mex))

mex_col = mex.geometry
print(type(mex_col))

mex_geom = mex_col.iloc[0]
print(type(mex_geom))

# calculate the intersection of the geometry objects
border = usa_geom.intersection(mex_geom)

# create map axis object
my_fig, my_ax = subplots(1, 1, figsize=(16, 10))

# remove axes
my_ax.axis('off')

# plot the border
GeoSeries(border).plot(
  ax = my_ax
	)

# save the image
savefig('./out/first-border.png')

# set which ellipsoid you would like to use
g = Geod(ellps='WGS84')

print(border)

# loop through each segment in the line and print the coordinates
for segment in border.geoms:
	print(f"from:{segment.coords[0]}\tto:{segment.coords[1]}")
    
# initialise a variable to hold the cumulative length
cumulative_length = 0

# Loop through each segment in the line
for segment in border.geoms:
    # Extract coordinates for start and end points
    start_lon, start_lat = segment.coords[0]
    end_lon, end_lat = segment.coords[1]
    
    # Calculate distance using Vincenty equations (inverse method)
    distance = g.inv(start_lon, start_lat, end_lon, end_lat)[2]
    
    # Add the distance to our cumulative total
    cumulative_length += distance

print(f"Border length: {cumulative_length} meters")

