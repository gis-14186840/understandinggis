# THIS IMPORTS A SQUARE ROOT FUNCTION, WHICH IS A BIG HINT!!
from math import sqrt

from geopandas import read_file

from shapely import STRtree


def distance(x1, y1, x2, y2):
    """
    * Use Pythagoras' theorem to measure the distance. This is acceptable in this case because:
    *     - the CRS of the data is a local projection
    *     - the distances are short
    *  - computational efficiency is important (as we are making many measurements)
    """
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)
# complete this line to return the distance between (x1,y1) and (x2,y2)
result = distance(345678, 456789, 445678, 556789)
print(f"{result:.2f}")
print()


# read in shapefiles, ensure that they all have the same CRS
pop_points = read_file("E:/Manchester/UGIS/data/gulu/pop_points.shp")
water_points = read_file("E:/Manchester/UGIS/data/gulu/water_points.shp").to_crs(pop_points.crs)
gulu_district = read_file("E:/Manchester/UGIS/data/gulu/district.shp").to_crs(pop_points.crs)


print(f"population points: {len(pop_points.index)}")
print()



# Create a buffered polygon (10.5km buffer around Gulu District)
polygon = gulu_district.geometry.iloc[0]
buffered_polygon = polygon.buffer(10500)  # 10.5km buffer

# report how many wells there are at this stage
print(f"Initial wells: {len(water_points.index)}")

# get the geometries from the water points geodataframe as a list
geoms = water_points.geometry.to_list()

# initialise an instance of an STRtree using the geometries
idx = STRtree(geoms)

# get the wells that intersect bounds of the district
possible_matches_index = idx.query(buffered_polygon)
possible_matches = water_points.iloc[possible_matches_index]
print(f"Potential wells: {len(possible_matches.index)}")


# Filter water points to those within the buffered area using vectorized operation
precise_matches = water_points.loc[water_points.within(buffered_polygon)]
print(f"Filtered wells: {len(precise_matches.index)}")

# Use vectorized nearest neighbor query with distance calculation
# This line replaces the entire loop!
nearest_indices, distances = precise_matches.sindex.nearest(
    pop_points.geometry, 
    return_all=False, 
    return_distance=True
)

print(f"Total distances calculated: {len(distances)}")

# Apply the function to all geometries
pop_points['nearest_well'] = distances

# Calculate and display statistics
min_distance = distances.min()
mean_distance = distances.mean()
max_distance = distances.max()

print(f"Minimum distance to water: {min_distance:,.0f}m")
print(f"Mean distance to water: {mean_distance:,.0f}m")
print(f"Maximum distance to water: {max_distance:,.0f}m")




