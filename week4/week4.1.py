from geopandas import read_file

from sys import exit

from math import sqrt

from shapely.geometry import LineString


from geopandas import GeoSeries # THIS ONE CAN BE COMBINED WITH AN EXISTING IMPORT STATEMENT
from matplotlib_scalebar.scalebar import ScaleBar
from matplotlib.pyplot import subplots, savefig, subplots_adjust


# open a dataset of all countries in the world
world = read_file("E:/Manchester/UGIS/data/natural-earth/ne_10m_admin_0_countries.shp")

# British National Grid definition
OSGB = "EPSG:27700"


def distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points"""
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def get_effective_area(a, b, c):
    """
    * Calculate the area of a triangle made from the points a, b and c using Heron's formula
    *     https://en.wikipedia.org/wiki/Heron%27s_formula
    """
    # calculate the length of each side
    side_a = distance(b[0], b[1], c[0], c[1])
    side_b = distance(a[0], a[1], c[0], c[1])
    side_c = distance(a[0], a[1], b[0], b[1])

    # calculate semi-perimeter of the triangle (perimeter / 2)
    s = (side_a + side_b + side_c) / 2

    # apply Heron's formula and return
    return sqrt(s * (s - side_a) * (s - side_b) * (s - side_c))


# extract the UK, project, and extract the geometry
uk = world[(world['ISO_A3'] == 'GBR')].to_crs(OSGB).geometry.iloc[0]    # COMPLETE THIS LINE

# report geometry type
print(f"geometry type: {uk.geom_type}")


# quit the analysis if we are dealing with any geometry but a MultiPolygon
if uk.geom_type != 'MultiPolygon':
  print("Geometry is not a MultiPolygon, exiting...")
  exit()


# initialise variables to hold the coordinates and area of the largest polygon
biggest_area = 0
coord_list = []

# loop through each polygon in the multipolygon and find the biggest (mainland Great Britain)
for poly in uk.geoms:

    # if it is the biggest so far
    if  poly.area > biggest_area:   # COMPLETE THIS LINE
    
        # store the new value for biggest area
        biggest_area = poly.area
        
     # store the coordinates of the polygon
        coord_list = list(poly.boundary.coords)    
        # COMPLETE THIS LINE (look at the variables that you defined before the loop)
        
print(f"Largest polygon area: {biggest_area}")
print(f"Original number of nodes: {len(coord_list)}")


# set the percentage of nodes that you want to remove
SIMPLIFICATION_PERC = 80

# how many nodes do we need?
n_nodes = int(len(coord_list) / 100.0 * (100 - SIMPLIFICATION_PERC))

# ensure that there are at least 3 nodes (minimum for a polygon)
if n_nodes < 3:
    n_nodes = 3 

print(f"Target number of nodes: {n_nodes}")
print()

def visvalingam_whyatt(node_list, n_nodes):
# loop through each node, excluding the end points
 areas = []
 for i in range(1, len(node_list)-1):

   # get the effective area
   area = get_effective_area(node_list[i-1], node_list[i], node_list[i+1])    # COMPLETE THIS LINE

   # append the node and effective area to the list
   areas.append({"point": node_list[i], "area": area})
  
 # add the end points back in at the start (0) and end (len(areas))
 areas.insert(0, {"point": node_list[0], "area": 0})
 areas.insert(len(areas), {"point": node_list[len(node_list)-1], "area": 0})
 

 # take a copy of the list so that we don't edit the original
 nodes = areas.copy()

 # keep going as long as the number of nodes is greater than the desired number
 while len(nodes) > n_nodes:
     
  min_area = float("inf")
  node_to_delete = -1
  
 
  
  for i in range(1, len(nodes)-1):
            if nodes[i]['area'] < min_area:
                min_area = nodes[i]['area']
                node_to_delete = i
                
  if node_to_delete != -1:
    # remove the current point from the list
    nodes.pop(node_to_delete)
 
    # recalculate effective area to the left of the deleted node
    if node_to_delete - 1 > 0:
        nodes[node_to_delete-1]['area'] = get_effective_area(
         nodes[node_to_delete-2]['point'], 
         nodes[node_to_delete-1]['point'], 
         nodes[node_to_delete]['point'])    # COMPLETE THIS LINE

    # if there is a node to the right of the deleted node, recalculate the effective area
    if node_to_delete < len(nodes)-1:
        nodes[node_to_delete]['area'] = get_effective_area(
         nodes[node_to_delete-1]['point'], 
         nodes[node_to_delete]['point'],
         nodes[node_to_delete+1]['point'])        # COMPLETE THIS LINE

 # extract the nodes and return
 return [node['point'] for node in nodes]

 # extract the nodes and return
 out = []
 for node in nodes:
   out.append(node['point'])

 return out

# remove one node and overwrite it with the new, shorter list
simplified_nodes = visvalingam_whyatt(coord_list, n_nodes)

# make a linestring out of the coordinates
before_line = LineString(coord_list)
print(f"original node count: {len(coord_list)}")
print(f"original length: {before_line.length / 1000:.2f}km\n")

# make the resulting list of coordinates into a line
after_line = LineString(simplified_nodes)
print(f"simplified node count: {len(simplified_nodes)}")
print(f"simplified length: {after_line.length / 1000:.2f}km\n")


# create map axis object, with two axes (maps)
fig, my_axs = subplots(1, 2, figsize=(16, 10))

# set titles
fig.suptitle("The Length of the Coastline of Mainland Great Britain")
my_axs[0].set_title(f"Original: {before_line.length / 1000:.0f}km, {len(coord_list)} nodes.")
my_axs[1].set_title(f"{SIMPLIFICATION_PERC}% Simplified: {after_line.length / 1000:.0f}km, {len(simplified_nodes)} nodes.")

# reduce the gap between the subplots
subplots_adjust(wspace=0)

osgb = "EPSG:27700"

# add the original coastline
GeoSeries(before_line, crs=osgb).plot(
    ax=my_axs[0],
    color='blue',
    linewidth = 0.6,
	)

# add the new coastline
GeoSeries(after_line, crs=osgb).plot(
    ax=my_axs[1],
    color='red',
    linewidth = 0.6,
	)

# edit individual axis
for my_ax in my_axs:

	# remove axes
	my_ax.axis('off')

	# add north arrow
	x, y, arrow_length = 0.95, 0.99, 0.1
	my_ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
		arrowprops=dict(facecolor='black', width=5, headwidth=15),
		ha='center', va='center', fontsize=20, xycoords=my_ax.transAxes)

	# add scalebar
	my_ax.add_artist(ScaleBar(dx=1, units="m", location="lower right"))

# save the result
savefig(f'out/5.png', bbox_inches='tight')
print("done!")