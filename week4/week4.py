from geopandas import read_file

# open a dataset of all countries in the world
world = read_file("E:/Manchester/UGIS/data/natural-earth/ne_10m_admin_0_countries.shp")

# Constants
SIMPLIFICATION_PERC = 98
# British National Grid definition
OSGB = "EPSG:27700"

# extract the UK, project, and extract the geometry
uk = world[(world['ISO_A3'] == 'GBR')].to_crs(OSGB).geometry.iloc[0]	# COMPLETE THIS LINE

# report geometry type
print(f"geometry type: {uk.geom_type}")