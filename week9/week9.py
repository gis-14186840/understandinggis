# Import the library
from osmnx import graph_from_xml

from shapely import STRtree
from shapely.geometry import Point, LineString

from pyproj import Geod

from sys import exit
from networkx import NodeNotFound, NetworkXNoPath

from heapq import heappush, heappop

from geopandas import GeoSeries

from geopandas import read_file
from shapely.geometry import Point
from matplotlib.patches import Patch
from matplotlib_scalebar.scalebar import ScaleBar
from matplotlib.pyplot import subplots, savefig, Line2D

import os

# create a MultiDiGraph from an XML dataset from OpenStreetMap
graph = graph_from_xml('E:/Manchester/UGIS/data/kaliningrad/kaliningrad.xml')

# create spatial index from graph
idx = STRtree([Point(n[1]['x'], n[1]['y']) for n in graph.nodes(data=True)])

# specify the start and end point of your route
from_point = Point(20.483322, 54.692934)
to_point = Point(20.544863, 54.723827)

# calculate the 'from' and 'to' node as the nearest to the specified coordinates
from_node_id, to_node_id = idx.nearest([from_point, to_point])

# get the IDs from the Graph to get the nodes themselves
node_list = list(graph.nodes())
from_node = node_list[from_node_id]
to_node = node_list[to_node_id]

# print the 'from' and 'to' nodes to the console
print(graph.nodes()[from_node], graph.nodes()[to_node])

# Get actual node IDs from the graph (map index to node ID)
node_list = list(graph.nodes())
from_node = node_list[from_node_id]
to_node = node_list[to_node_id]


# Define Heuristic Function (Ellipsoidal Distance)
def ellipsoidal_distance(node_a, node_b):
	"""
	Calculate the 'as the crow flies' distance between two nodes in a graph using
	 the Inverse Vincenty method, via the PyProj library.
	"""
	# extract the data (the coordinates) from node_a and node_b
	point_a = graph.nodes(data=True)[node_a]
	point_b = graph.nodes(data=True)[node_b]

	# compute the distance across the WGS84 ellipsoid (the one used by the dataset)
	return Geod(ellps='WGS84').inv(point_a['x'], point_a['y'], point_b['x'], point_b['y'])[2]


# Define Route Reconstruction Function
def reconstruct_path(end_node, parent_node, parents):
	"""
	Once we have found the end node of our route, reconstruct the shortest path 
	 to it using the parents list
	"""
	# initialise a list that will contain the path, beginning with the current node (the end of the route)
	path = [end_node]
	
	# then get the parent (the node from which we arrived at the end of the route)
	node = parent_node

	# loop back through the list of explored nodes until we reach the start node (the one where parent == None)
	while node is not None:

		# for each node in the path, add it to the path...
		path.append(node)

		# ...and move on to its parent (the one before it in the path)
		node = parents[node]
	
	# finally, reverse the path (so it goes start -> end) and return it
	path.reverse()	# note that this is an 'in place' function that edits the list itself, it does not return anything!
	return path



# Implement A* Algorithm
def astar_path(G, source, target, heuristic):
  
    # First, make sure that both the `source` and `target` nodes actually exist...
    if source not in G or target not in G:
        raise NodeNotFound(f"Either source ({source}) or target ({target}) is not in the graph")

    # Create a counter to ensure that each item in the heap queue will have a unique value
    # (as two could theoretically have the same estimated distance)
    counter = 0

    # Initialise the heap queue: list of tuples (priority, counter, node, cost, parent)
    # priority: estimated total distance (network distance + heuristic)
    # counter: unique identifier for nodes with same priority
    # node: current node ID
    # cost: network distance from start to current node
    # parent: parent node ID in the path
    queue = [(0, counter, source, 0, None)]

    # Dictionary to track distances: {node: (network_distance_from_start, straight_line_to_target)}
    distances = {}

    # Dictionary to track parent of each explored node (for path reconstruction)
    parents = {}

    # Keep going as long as there are more nodes to search
    while queue:
        # Pop the next node, its network distance from the start, and its parent from the queue
        # Use list slicing to ignore the first two items (priority and counter)
        cur_node, cur_net_dist, cur_parent = heappop(queue)[2:]

        # Check if we have reached the destination
        if cur_node == target:
            # If so, reconstruct the path and return
            return reconstruct_path(cur_node, cur_parent, parents)

        # Skip if we have already assessed this node with a better path
        # Check if we have already explored this node
        if cur_node in parents:
            # If we are back at the start (no parent), abandon this path
            if parents[cur_node] is None:
                continue
            # If we already have a shorter path to this node, abandon this new path
            if distances[cur_node][0] < cur_net_dist:
                continue

        # Record the parent of the current node and process neighbors
        # Add the parent of the current node to the parents dictionary
        parents[cur_node] = cur_parent

        # Get all neighbors of the current node (loop through edge items)
        for neighbour, edge_data in G[cur_node].items():
            # Calculate network distance from start to neighbor (current distance + edge length)
            dist_from_start = cur_net_dist + edge_data[0]['length']

            # Check if we have already processed this neighbor
            if neighbour in distances:
                # Extract previous network distance and heuristic distance
                previous_dist_from_start, dist_to_end = distances[neighbour]
                # If previous path is shorter, skip this neighbor
                if previous_dist_from_start <= dist_from_start:
                    continue
            else:
                # If not processed, calculate heuristic distance (neighbor -> target)
                dist_to_end = heuristic(neighbour, target)

            # Update distances dictionary with new values
            distances[neighbour] = (dist_from_start, dist_to_end)

            # Calculate estimated total distance (priority for heap queue)
            estimated_dist = dist_from_start + dist_to_end

            # Increment counter and push neighbor to heap queue
            counter += 1
            heappush(queue, (estimated_dist, counter, neighbour, dist_from_start, cur_node))

    # If the loop finishes without returning, no path exists
    raise NetworkXNoPath(f"Node {target} not reachable from {source}")



# Execute A* Algorithm with Error Handling
try:
    # Calculate the shortest path using custom A* algorithm
    shortest_path = astar_path(graph, from_node, to_node, ellipsoidal_distance)
    
    # Print the resulting path (list of node IDs)
    print("Shortest path node list:")
    print(shortest_path)
    print(f"\nTotal number of nodes in path: {len(shortest_path)}")

# Catch exception if source/target node not found in graph
except NodeNotFound:
    print("Sorry, there is no path between those locations in the provided network")
    exit()

# Catch exception if no path exists between nodes
except NetworkXNoPath:
    print("Sorry, there is no path between those locations in the provided network")
    exit()


# Convert Path to LineString
def path_to_linestring(start_point, path_list, end_point):

    # Initialise the list with the start point coordinates (x, y)
    line = [start_point.coords[0]]  # Extract (lon, lat) tuple from Point
    
    # Loop through each node in the shortest path and add coordinates
    for n in path_list:
        # Get the node's coordinate data from the graph
        node = graph.nodes(data=True)[n]
        # Append (x, y) tuple to the line list (matches start_point format)
        line.append((node['x'], node['y']))  # Complete missing line
    
    # Append the end point coordinates to the list
    line.append(end_point.coords[0])  # Complete missing line
    
    # Return as a Shapely LineString
    return LineString(line)

# Convert shortest path to LineString and print for verification
path_linestring = path_to_linestring(from_point, shortest_path, to_point)
print("\nConverted Path to LineString:")
print(path_linestring)


# Convert LineString to GeoSeries & Project
# Define CRS strings (WGS84 geographic & UTM34N projected)
wgs84 = "EPSG:4326"  # WGS84 (default for OSM data)
utm34 = "EPSG:32634" # UTM Zone 34N (appropriate for Kaliningrad)

# Convert LineString to GeoSeries and reproject to UTM34N
path_geoseries = GeoSeries(path_linestring, crs=wgs84).to_crs(utm34)

# Print projected GeoSeries to verify
print("\nProjected Path GeoSeries (UTM34N):")
print(path_geoseries)


# Create & Save the Map
# Create output directory if it doesn't exist
os.makedirs('./out', exist_ok=True)

# Load background data (buildings and water) and reproject to UTM34N
buildings = read_file('E:/Manchester/UGIS/data/kaliningrad/buildings.shp').to_crs(utm34)
water = read_file('E:/Manchester/UGIS/data/kaliningrad/water.shp').to_crs(utm34)

# Create map figure
fig, my_ax = subplots(1, 1, figsize=(16, 10))
my_ax.axis('off')  # Hide axis labels/ticks
my_ax.set(title="The 4 Bridges of Kaliningrad: A* Shortest Path")

# Set map bounds with 1000m buffer around the path
buffer = 1000
path_bounds = path_geoseries.geometry.iloc[0].bounds
my_ax.set_xlim([path_bounds[0] - buffer, path_bounds[2] + buffer])
my_ax.set_ylim([path_bounds[1] - buffer, path_bounds[3] + buffer])

# Plot background layers (zorder controls drawing order: lower = behind)
water.plot(ax=my_ax, color='#a6cee3', linewidth=1, zorder=1)    # Water (light blue)
buildings.plot(ax=my_ax, color='grey', linewidth=1, zorder=2)    # Buildings (grey)

# Plot the shortest path (purple, thick line)
path_geoseries.plot(ax=my_ax, color='#984ea3', linewidth=3, zorder=4)

# Plot start (blue) and end (red) points (projected to UTM34N)
GeoSeries([from_point], crs=wgs84).to_crs(utm34).plot(
    ax=my_ax, markersize=60, color='blue', edgecolor='black', zorder=5
)
GeoSeries([to_point], crs=wgs84).to_crs(utm34).plot(
    ax=my_ax, markersize=60, color='red', edgecolor='black', zorder=6
)

# Add custom legend
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markeredgecolor='black', markersize=8, label='Origin'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markeredgecolor='black', markersize=8, label='Destination'),
    Patch(facecolor='grey', label='Buildings'),
    Patch(facecolor='#a6cee3', edgecolor='#a6cee3', label='Water'),
    Line2D([0], [0], color='#984ea3', lw=3, label='Path'),
    Line2D([0], [0], color='#4daf4a', lw=3, label='Path(NX)')  # Reserved for NetworkX comparison (as per tutorial)
]
my_ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

# Add north arrow
x, y, arrow_length = 0.99, 0.99, 0.1
my_ax.annotate('N', xy=(x, y), xytext=(x, y - arrow_length),
               arrowprops=dict(facecolor='black', width=5, headwidth=15),
               ha='center', va='center', fontsize=20, xycoords=my_ax.transAxes)

# Add scale bar (units: meters)
my_ax.add_artist(ScaleBar(dx=1, units="m", location="lower left"))

# Save the map to output directory
savefig('./out/10.png', bbox_inches='tight', dpi=150)
print("\nMap saved to ./out/10.png")
print("done!")