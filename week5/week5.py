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