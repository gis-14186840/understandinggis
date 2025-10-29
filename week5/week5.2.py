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

from matplotlib.pyplot import subplots, savefig

from matplotlib.patches import Patch

from matplotlib_scalebar.scalebar import ScaleBar


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


def make_bounds_square(ax):
    """
    * Adjust the bounds of the specified axis to make them for to a square
    """
    # get the current bounds
    ax_bounds_x = ax.get_xlim()
    ax_bounds_y = ax.get_ylim()

    # get the width and height
    ax_width = ax_bounds_x[1] - ax_bounds_x[0]
    ax_height = ax_bounds_y[1] - ax_bounds_y[0]
    
    # if width is larger, expand height to match
    if ax_width > ax_height:
        buffer = (ax_width - ax_height) / 2
        ax.set_ylim((ax_bounds_y[0] - buffer, ax_bounds_y[1] + buffer))
    
    # if height is larger expand width to match
    elif ax_width < ax_height:
        buffer = (ax_height - ax_width) / 2
        ax.set_xlim((ax_bounds_x[0] - buffer, ax_bounds_x[1] + buffer))





def evaluate_distortion(g, transformer, minx, miny, maxx, maxy, minr=10000, maxr=1000000, sample_number=1000, vertices=16):
  
    # Initialize the storage list
    area_indices = []
    shape_indices = []
    distance_indices = []
    
    area_union_indices = []
    
    
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
        ellipsoidal_polygon = Polygon(e_coords)
        
        ellipsoidal_area = Polygon(e_coords).area
        
        
        # transform the centre point to the projected
        centre_x, centre_y = transformer.transform(x, y, direction='FORWARD')

        # construct a circle around the projected point on a plane, calculate area
        planar_coords = [ compute_offset((centre_x, centre_y), r, az) for az in forward_azimuths ]
        planar_polygon = Polygon(planar_coords)
        
        planar_area = Polygon([ compute_offset((centre_x, centre_y), r, az) for az in forward_azimuths ]).area


        # Calculating the area distortion values
        if ellipsoidal_area + planar_area > 0:  # Avoid division by zero
            area_index = abs(ellipsoidal_area - planar_area) / abs(ellipsoidal_area + planar_area)
            area_indices.append(area_index)


        # calculate area distortion index using IoU method (Gosling & Symeonakis, 2020)
        intersection_area = ellipsoidal_polygon.intersection(planar_polygon).area
        union_area = ellipsoidal_polygon.union(planar_polygon).area
        
        if union_area > 0:  # Avoid division by zero
            iou = intersection_area / union_area
            area_union_index = 1 - iou  # r = 1 - (K∩L / K∪L)
            area_union_indices.append(area_union_index)
            

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

if __name__ == "__main__":
    # Loading the datasets
    
  # create a 2x2 figure
  fig, my_axs = subplots(2, 2, figsize=(10, 10), constrained_layout=True)
  fig.suptitle('How much Ice is in Iceland?\n', fontsize=20)
  text = ""

  # loop through each CRS
  for ax_num, projection in enumerate(projections): 
    
    # get x and y position of current axis
    axx = ax_num // my_axs.shape[0]
    axy = ax_num % my_axs.shape[0]

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


    # append text for figure
    text += f"{projection['name']+":":<13} $E_p={Ep:.4f}$  $E_s={Es:.4f}$  $E_a={Ea:.4f}$\n\n"

    # disable axis, add title
    my_axs[axx][axy].axis('off')
    my_axs[axx][axy].set_facecolor('#000000')
    my_axs[axx][axy].set_title(f"{projection['name']} ({projection['description']})\nIce area: {ice_area_km2:,.0f} km sq.")

    # plot iceland
    iceland.to_crs(projection['proj']).plot(
        ax = my_axs[axx][axy],
        color = "#b2df8a",
        edgecolor = '#33a02c',
        linewidth = 0.2,
        )

    # plot ice
    ice.to_crs(projection['proj']).plot(
        ax = my_axs[axx][axy],
        color = "#e6f5f9",
        edgecolor = "#e6f5f9",
        linewidth = 0.1,
        )

    # add scalebar
    my_axs[axx][axy].add_artist(ScaleBar(dx=1, units="m", location="lower right"))

    # adjust the plot bounds to fit a square
    make_bounds_square(my_axs[axx][axy])


  # disable axis on the empty axis
  my_axs[1][1].axis('off')

  # manually draw a legend to the empty axis
  my_axs[1][1].legend([Patch(facecolor='#e6f5f9', edgecolor='#e6f5f9', label='Glacier')], ['Glacier'], loc='lower right')

  # add north arrow to empty axis
  x, y, arrow_length = 0.9, 0.3, 0.15
  my_axs[1][1].annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
    arrowprops=dict(facecolor='black', width=3, headwidth=9),
    ha='center', va='center', fontsize=16, xycoords=my_axs[1][1].transAxes)

  # add the results to the empty axis - monospace font ensures table alignment
  my_axs[1][1].text(0.1, 0.4, text, fontfamily='monospace')

  # save the result
  savefig('out/5.2.png', bbox_inches='tight')
  print("done!")

