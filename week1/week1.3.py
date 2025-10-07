from geopandas import read_file

world = read_file("E:/Manchester/UGIS/data/natural-earth/ne_50m_admin_0_countries.shp")
graticule = read_file("E:/Manchester/UGIS/data/natural-earth/ne_110m_graticules_15.shp")
bbox = read_file("E:/Manchester/UGIS/data/natural-earth/ne_110m_wgs84_bounding_box.shp")

ea_proj = '+proj=eqearth +lon_0=0 +datum=WGS84 +units=m +no_defs'
# reproject all three layers to equal earth
world = world.to_crs(ea_proj)
graticule = graticule.to_crs(ea_proj)
bbox = bbox.to_crs(ea_proj)

world['GDP Per Capita'] = world['GDP_MD_EST'] / world['POP_EST']

from matplotlib.pyplot import subplots, savefig
# create map axis object
my_fig, my_ax = subplots(1, 1, figsize=(16, 10))

# plot the countries onto ax
world.plot(ax = my_ax)

# turn off the visible axes on the map
my_ax.axis('off')

# add bounding box and graticule layers
bbox.plot(
    ax = my_ax,
    color = 'lightgray',
    linewidth = 0,
    )

# plot the graticule
graticule.plot(
    ax = my_ax,
    color = 'white',
    linewidth = 0.5,
    )

# plot the countries
world.plot(								# plot the world dataset
    ax = my_ax,						# specify the axis object to draw it to
    column = 'GDP Per Capita',		# specify the column used to style the dataset
    cmap = 'OrRd',				# specify the colour map used to style the dataset based on POP_EST
    scheme = 'quantiles',	# specify how the colour map will be mapped to the values in POP_EST
    linewidth = 0.5,			# specify the line width for the country outlines
    edgecolor = 'gray',		# specify the line colour for the country outlines
    legend = 'True',
    legend_kwds = {
    'loc': 'lower left',
    'title': 'GDP Per Capita'
    }
    )


my_ax.set(title="GDP Per Capita: Equal Earth Coordinate Reference System")
