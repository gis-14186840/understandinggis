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

from numpy.random import uniform

from numpy import arange

import numpy as np

from shapely.geometry import Polygon


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



def compute_offset(center, distance, azimuth):
    """Calculate offset coordinates from center point"""
    x, y = center
    rad_azimuth = np.radians(azimuth)
    offset_x = x + distance * np.cos(rad_azimuth)
    offset_y = y + distance * np.sin(rad_azimuth)
    return (offset_x, offset_y)


def evaluate_distortion(g, transformer, minx, miny, maxx, maxy, minr=10000, maxr=1000000, sample_number=1000, vertices=16):
  
    # Initialize the storage list
    area_indices = []
    shape_indices = []
    distance_indices = []
    
    # calculate the required number of random locations (x and y separately) plus radius
    xs = uniform(low=minx, high=maxx, size=sample_number)
    ys = uniform(low=miny, high=maxy, size=sample_number)
    rs = uniform(low=minr, high=maxr, size=sample_number)

    # offset distances
    forward_azimuths = arange(0, 360, 22.5)
    
    
    # create two lists
    # zip and extract using variable expansion
    for x, y, r in zip(xs, ys, rs):
        
        # construct a circle around the centre point on the ellipsoid
        lons, lats = g.fwd([x]*vertices, [y]*vertices, forward_azimuths, [r]*vertices)[:2]
    
        # project the result, calculate area, append to the list
        e_coords = [ transformer.transform(lon, lat, direction='FORWARD') for lon, lat in zip(lons, lats) ]

        # get the area of the resulting circle
        ellipsoidal_area = Polygon(e_coords).area
        
        # transform the centre point to the projected
        centre_x, centre_y = transformer.transform(x, y, direction='FORWARD')

        # construct a circle around the projected point on a plane, calculate area
        planar_area = Polygon([ compute_offset((centre_x, centre_y), r, az) for az in forward_azimuths ]).area

        # Calculating the area distortion values
        if ellipsoidal_area + planar_area > 0:  # Avoid division by zero
            area_index = abs(ellipsoidal_area - planar_area) / abs(ellipsoidal_area + planar_area)
            area_indices.append(area_index)

        # get radial distances from the centre to each of the 16 points on the circle
        ellipsoidal_radial_distances = [ hypot(centre_x - ex, centre_y - ey) for ex, ey in e_coords ]

        # Check if the sum of distances is zero to avoid division by zero
        distance_sum = sum(ellipsoidal_radial_distances)
        if distance_sum > 0:  # Only calculate shape distortion if sum is positive

        # get the absolute proportional difference between the expected and actual radial distance for each 'spoke'
            shape_distortion = [abs((1 / vertices) - (d / sum(ellipsoidal_radial_distances))) for d in ellipsoidal_radial_distances]
            shape_indices.append(sum(shape_distortion))
            
            # Distance distortion assessment
    for _ in range(sample_number):
        # Generate two random points
        x1, y1 = uniform(low=minx, high=maxx), uniform(low=miny, high=maxy)
        x2, y2 = uniform(low=minx, high=maxx), uniform(low=miny, high=maxy)
            
        # calculate the distance along the ellipsoid
        ellipsoidal_distance = g.line_length([x1, x2], [y1, y2])
        
        # project both points
        proj_x1, proj_y1 = transformer.transform(x1, y1, direction='FORWARD')
        proj_x2, proj_y2 = transformer.transform(x2, y2, direction='FORWARD')
        
        # calculate planar distance
        planar_distance = hypot(proj_x1 - proj_x2, proj_y1 - proj_y2)
        
        # calculate distance distortion index
        if ellipsoidal_distance + planar_distance > 0:  # Avoid division by zero
           distance_index = abs(ellipsoidal_distance - planar_distance) / abs(ellipsoidal_distance + planar_distance)
           distance_indices.append(distance_index)
        
    # Calculate the final distortion index
    Ea = sum(area_indices) / len(area_indices)  # area distortion
    Es = sum(shape_indices) / len(shape_indices)  # shape distortion 
    Ep = sum(distance_indices) / len(distance_indices)  # distance distortion
    
    return Ep, Es, Ea

# loop through each CRS
for ax_num, projection in enumerate(projections):

    
    # initialise a PyProj Transformer to transform coordinates
    transformer = Transformer.from_crs(CRS.from_proj4(geo_string), 
                                       CRS.from_proj4(projection['proj']), 
                                       always_xy=True)

    # calculate the distortion
    Ep, Es, Ea = evaluate_distortion(g, transformer, minx, miny, maxx, maxy, 10000, 1000000, 1000)
    
    # calculate ice area
    ice_area_km2 = ice.to_crs(projection['proj']).geometry.area.sum() / 1000000


# report to user
print(f"\n{projection['name']} ({projection['description']})")
print(f"   {"Distance distortion (Ep):":<26}{Ep:.6f}")
print(f"   {"Shape distortion (Es):":<26}{Es:.6f}")
print(f"   {"Area distortion (Ea):":<26}{Ea:.6f}")
print(f"   {"Ice Area:":<26}{ice_area_km2 / 1000:,.0f} km sq.")
    