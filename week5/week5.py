from math import cos, sin, radians, hypot	# IMPORT NECESSARY FUNCTIONS HERE


def compute_offset(origin, distance, direction):
    """
    Compute the location of a point at a given distance and direction from a specified location using trigonometry
    """
    
    # Convert the direction from degrees to radians
    direction_rad = radians(direction)
    
    # Calculate the offset
    offset_x = origin[0] + cos(direction_rad) * distance	# COMPLETE THIS LINE
    offset_y = origin[1] + sin(direction_rad) * distance	# COMPLETE THIS LINE 
    return (offset_x, offset_y)

# this code tests whether your function works correctly
origin = (345678, 456789)
destination = compute_offset(origin, 1011, 123)	# move 1011m in a direction of 123 degrees 
print("CORRECT!!" if (int(destination[0]), int(destination[1])) == (345127, 457636) 
      else f"INCORRECT!! Error: {(int(destination[0])-345127, int(destination[1])-457636)}")



# PART 2

import geopandas as gpd

from pyproj import Geod, CRS, Transformer

# Open the countries shapefile as a GeoDataFrame and store in 'world'
world = gpd.read_file("E:/Manchester/UGIS/data/natural-earth/ne_10m_admin_0_countries.shp")

# Extract the Iceland row using ISO code 'ISL' and store in 'iceland'
iceland = world[world['ISO_A3'] == 'ISL'] 

# Open the Iceland land cover shapefile as a GeoDataFrame and store in 'land_cover'
land_cover = gpd.read_file("E:/Manchester/UGIS/data/iceland/gis_osm_natural_a_free_1.shp")

# Extract rows where fclass is "glacier" and store in 'ice'
ice = land_cover[land_cover['fclass'] == "glacier"]

# Get the bounds of Iceland
minx, miny, maxx, maxy = iceland.total_bounds

# Print the bounds to verify
print(minx, miny, maxx, maxy)


# set the geographical proj string and ellipsoid (should be the same)
geo_string = "+proj=longlat +datum=WGS84 +no_defs"
g = Geod(ellps='WGS84')

# create a list of dictionaries for the projected CRS' to evaluate for distortion
projections = [
        {'name': "Web Mercator", 
            'description': "Global Conformal", 
            'proj': "+proj=webmerc +datum=WGS84 +units=m +no_defs"},
        {'name': "Eckert IV", 
            'description': "Global Equal Area", 
            'proj': "+proj=eck4 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"},
        {'name': "Iceland Albers", 
            'description': "Local Equal Area", 
            'proj': "+proj=aea +lat_0=65 +lon_0=-19 +lat_1=64 +lat_2=66 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"}
    ]




# loop through each CRS
for ax_num, projection in enumerate(projections):

    print(f"{projection['name']}")
    
    # initialise a PyProj Transformer to transform coordinates
    transformer = Transformer.from_crs(CRS.from_proj4(geo_string), 
                                       CRS.from_proj4(projection['proj']), 
                                       always_xy=True)

