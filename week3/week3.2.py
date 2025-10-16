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
print(f"Initial wells: {len(water_points.index)}")
print()


# METHOD 1: Using explicit spatial index (STRtree) with buffered boundary
print("=== METHOD 1: Using explicit spatial index with buffered boundary ===")


# Create a buffered polygon (10.5km buffer around Gulu District)
polygon = gulu_district.geometry.iloc[0]
buffered_polygon = polygon.buffer(10500)  # 10.5km buffer

print(f"Initial wells: {len(water_points.index)}")



# get the geometries from the water points geodataframe as a list
geoms = water_points.geometry.to_list()

# initialise an instance of an STRtree using the geometries
idx = STRtree(geoms)



# Use spatial index to find wells within buffered area
possible_matches_index = idx.query(buffered_polygon)
possible_matches = water_points.iloc[possible_matches_index]
print(f"Potential wells (with buffer): {len(possible_matches.index)}")


# Precise filtering with buffered polygon
precise_matches = possible_matches.loc[possible_matches.within(buffered_polygon)]
print(f"Filtered wells (with buffer): {len(precise_matches.index)}")


# rebuild the spatial index using the new, smaller dataset
# get the geometries from the precise_matches geodataframe as a list
geoms_precise = precise_matches.geometry.to_list()
idx = STRtree(geoms_precise)


# Declare an empty list to store distances
distances_buffered = []

# loop through each population point
for id, house in pop_points.iterrows():
    
    # 1: Get the index of the nearest well to the current population point
    # use the spatial index to get the index of the closest well
    nearest_well_index = idx.nearest(house.geometry)
        
    # 2: Extract the row of data corresponding to the nearest well
    # use the spatial index to get the closest well object from the original dataset
    nearest_well = precise_matches.iloc[nearest_well_index].geometry
        
    # 3: Extract the Point from the MultiPoint (if necessary)
    # .geoms[0] extracts the first Point from the MultiPoint
    if hasattr(nearest_well, 'geoms'):
        nearest_well_point = nearest_well.geoms[0]
    else:
        nearest_well_point = nearest_well
        
    # 4: Measure the distance and append to the list
    # store the distance to the nearest well
    distances_buffered.append(distance(
        house.geometry.x, 
        house.geometry.y, 
        nearest_well_point.x, 
        nearest_well_point.y
        ))
        
    # Print progress every 1000 iterations
    if id % 10000 == 0:
        print(f"Processed {id} population points...")

# Print the length of distances list to verify
print(f"Total distances calculated: {len(distances_buffered)}")

            
# store distance to nearest well
pop_points['nearest_well_buffered'] = distances_buffered



# Calculate the mean distance
mean_buffered = sum(distances_buffered) / len(distances_buffered)

print(f"Minimum distance to water (with buffer): {min(distances_buffered):,.0f}m.")
print(f"Mean distance to water (with buffer): {mean_buffered:,.0f}m.")
print(f"Maximum distance to water (with buffer): {max(distances_buffered):,.0f}m.")
print()



# METHOD 2: Using geopandas built-in spatial index
print("=== METHOD 2: Using geopandas built-in spatial index ===")

# Reset water points to original data
water_points = read_file("E:/Manchester/UGIS/data/gulu/water_points.shp").to_crs(pop_points.crs)

# Ensure spatial index is constructed
water_points.sindex

print(f"Initial wells: {len(water_points)}")

# Use geopandas built-in spatial operations with buffered polygon
precise_matches_gpd = water_points.loc[water_points.within(buffered_polygon)]

print(f"Filtered wells (geopandas method): {len(precise_matches_gpd)}")

# Rebuild spatial index with filtered wells (geopandas method)
precise_matches_gpd.sindex

# Calculate distances using geopandas method
distances_gpd = []
for id, house in pop_points.iterrows():
    # Find the nearest well using geometry distance
    # This uses geopandas' built-in spatial index
    nearest_wells = precise_matches_gpd.geometry.distance(house.geometry)
    nearest_index = nearest_wells.idxmin()
    nearest_well = precise_matches_gpd.loc[nearest_index].geometry
    
    distances_gpd.append(distance(
        house.geometry.x, 
        house.geometry.y, 
        nearest_well_point.x, 
        nearest_well_point.y
    ))
    
    if id % 10000 == 0:
        print(f"Processed {id} population points...")
        

print(f"Total distances calculated (geopandas): {len(distances_gpd)}")

# Add distances as a new column
pop_points['nearest_well_gpd'] = distances_gpd

# Calculate and display statistics
mean_gpd = sum(distances_gpd) / len(distances_gpd)

print(f"Minimum distance to water (with buffer): {min(distances_buffered):,.0f}m.")
print(f"Mean distance to water (with buffer): {mean_buffered:,.0f}m.")
print(f"Maximum distance to water (with buffer): {max(distances_buffered):,.0f}m.")




