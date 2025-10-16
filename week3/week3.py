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



# read in shapefiles, ensure that they all have the same CRS
pop_points = read_file("E:/Manchester/UGIS/data/gulu/pop_points.shp")
water_points = read_file("E:/Manchester/UGIS/data/gulu/water_points.shp")
gulu_district = read_file("E:/Manchester/UGIS/data/gulu/district.shp")

# Print the CRS of each dataset using EPSG codes
print(pop_points.crs.to_epsg())

print(water_points.crs.to_epsg())

print(gulu_district.crs.to_epsg())

# read in the `water_points` dataset AND transform it the the same CRS as `pop_points`
water_points = read_file("E:/Manchester/UGIS/data/gulu/water_points.shp").to_crs(pop_points.crs)

# Check that all layers now have the same CRS
print(pop_points.crs.to_epsg())

print(water_points.crs.to_epsg())

print(gulu_district.crs.to_epsg())

print(f"population points: {len(pop_points.index)}")
print(f"Initial wells: {len(water_points.index)}")



# get the geometries from the water points geodataframe as a list
geoms = water_points.geometry.to_list()

# initialise an instance of an STRtree using the geometries
idx = STRtree(geoms)

