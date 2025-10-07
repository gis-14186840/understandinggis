from geopandas import read_file, GeoSeries

from matplotlib.pyplot import subplots, savefig, title

from pyproj import Geod

# load the shapefile of countries - this gives a table of 12 columns and 246 rows (one per country)
world = read_file("E:/Manchester/UGIS/data/natural-earth/ne_10m_admin_0_countries.shp")

# open the graticule dataset
graticule = read_file("E:/Manchester/UGIS/data/natural-earth/ne_110m_graticules_5.shp")

# select the Lambert Conformal Conic Projection
lambert_conic = "+proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"

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



# set title
title(f"Trump's wall would have been {cumulative_length / 1000:.2f} km long.")

# project border
border_series = GeoSeries(border, crs=world.crs).to_crs(lambert_conic)

# extract the bounds from the (projected) GeoSeries Object
minx, miny, maxx, maxy = border_series.geometry.iloc[0].bounds

# set bounds (10000m buffer around the border itself, to give us some context)
buffer = 10000
my_ax.set_xlim([minx - buffer, maxx + buffer])
my_ax.set_ylim([miny - buffer, maxy + buffer])

# plot data
usa.to_crs(lambert_conic).plot(
    ax = my_ax,
    color = '#ccebc5',
    edgecolor = '#4daf4a',
    linewidth = 0.5,
    )
mex.to_crs(lambert_conic).plot(
    ax = my_ax,
    color = '#fed9a6',
    edgecolor = '#ff7f00',
    linewidth = 0.5,
    )
border_series.plot(     # note that this has already been projected above!
    ax = my_ax,
    color = '#984ea3',
    linewidth = 2,
    )
graticule.to_crs(lambert_conic).plot(
    ax=my_ax,
    color='grey',
    linewidth = 1,
    )

# save the result
savefig('out/2.png', bbox_inches='tight')
print("done!")

