# Import the library
from osmnx import graph_from_xml
from shapely import STRtree
from shapely.geometry import Point, LineString
from pyproj import Geod
from heapq import heappush, heappop
from sys import exit
from networkx import NodeNotFound, NetworkXNoPath, astar_path as astar_path_nx, DiGraph
from geopandas import GeoSeries, read_file
from matplotlib.patches import Patch
from matplotlib_scalebar.scalebar import ScaleBar
from matplotlib.pyplot import subplots, savefig, Line2D
from pickle import dump, load, HIGHEST_PROTOCOL
import os


# Configuration (Paths & CRS)

# Data directory (use absolute path from original code)
DATA_DIR = 'E:/Manchester/UGIS/data/kaliningrad/'
PICKLE_PATH = os.path.join(DATA_DIR, 'kaliningrad.pkl')
OSM_XML_PATH = os.path.join(DATA_DIR, 'kaliningrad.xml')
BUILDINGS_SHP_PATH = os.path.join(DATA_DIR, 'buildings.shp')
WATER_SHP_PATH = os.path.join(DATA_DIR, 'water.shp')

# Define CRS (projected to UTM34N for mapping)
wgs84 = "EPSG:4326"  # WGS84 geographic CRS (native for OSM data)
utm34 = "EPSG:32634" # UTM Zone 34N projected CRS (suitable for Kaliningrad)


# Data Loading with Pickle Serialization
try:
    # Load serialized data from pickle file (fast)
    with open(PICKLE_PATH, 'rb') as input_file:
        print("Pickle file found successfully, loading data.")
        data = load(input_file)
        graph = data['graph']       # MultiDiGraph (road network)
        buildings = data['buildings'] # GeoDataFrame (buildings, projected to UTM34N)
        water = data['water']       # GeoDataFrame (water, projected to UTM34N)

except FileNotFoundError:
    # No pickle file found - load from raw data (slow, runs on first execution)
    print("No pickle file found, loading data (takes a long time).")
    
    # Load OSM road network
    graph = graph_from_xml(OSM_XML_PATH)
    
    # Load background data and reproject to UTM34N
    buildings = read_file(BUILDINGS_SHP_PATH).to_crs(utm34)
    water = read_file(WATER_SHP_PATH).to_crs(utm34)
    
    # Package all data into a dictionary for serialization
    data = {
        'graph': graph,
        'buildings': buildings,
        'water': water
    }
    # Serialize data to pickle file for future use
    with open(PICKLE_PATH, 'wb') as output_file:
        dump(data, output_file, HIGHEST_PROTOCOL)
    print("Pickle file created successfully for future use.")


# Find Nearest Nodes (Start/End Points)

# Create spatial index for nearest node search
idx = STRtree([Point(n[1]['x'], n[1]['y']) for n in graph.nodes(data=True)])

# Specify the start and end point of the route (WGS84 coordinates)
from_point = Point(20.483322, 54.692934)
to_point = Point(20.544863, 54.723827)

# Calculate the 'from' and 'to' node as the nearest to the specified coordinates
from_node_id, to_node_id = idx.nearest([from_point, to_point])
node_list = list(graph.nodes())
from_node = node_list[from_node_id]
to_node = node_list[to_node_id]

# Print the 'from' and 'to' nodes to the console
print(f"\nFrom node coordinates: {graph.nodes()[from_node]}")
print(f"To node coordinates: {graph.nodes()[to_node]}")


# Core Functions

def ellipsoidal_distance(node_a, node_b):

    # Extract the data (the coordinates) from node_a and node_b
    point_a = graph.nodes(data=True)[node_a]
    point_b = graph.nodes(data=True)[node_b]

    # Compute the distance across the WGS84 ellipsoid (the one used by the dataset)
    return Geod(ellps='WGS84').inv(point_a['x'], point_a['y'], point_b['x'], point_b['y'])[2]

def reconstruct_path(end_node, parent_node, parents):

    # Initialise a list that will contain the path, beginning with the current node (the end of the route)
    path = [end_node]
    
    # Then get the parent (the node from which we arrived at the end of the route)
    node = parent_node

    # Loop back through the list of explored nodes until we reach the start node (the one where parent == None)
    while node is not None:
        # For each node in the path, add it to the path...
        path.append(node)
        # ...and move on to its parent (the one before it in the path)
        node = parents[node]
    
    # Finally, reverse the path (so it goes start -> end) and return it
    path.reverse()  # Note that this is an 'in place' function that edits the list itself, it does not return anything!
    return path

def path_to_linestring(start_point, path_list, end_point):

    # Initialise the list with the start point coordinates (x, y)
    line = [start_point.coords[0]]  # Extract (lon, lat) tuple from Point
    
    # Loop through each node in the shortest path and add coordinates
    for n in path_list:
        # Get the node's coordinate data from the graph
        node = graph.nodes(data=True)[n]
        # Append (x, y) tuple to the line list (matches start_point format)
        line.append((node['x'], node['y']))
    
    # Append the end point coordinates to the list
    line.append(end_point.coords[0])
    
    # Return as a Shapely LineString
    return LineString(line)


# Custom A* Algorithm Implementation

def astar_path(G, source, target, heuristic):

    # First, make sure that both the `source` and `target` nodes actually exist
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


# Run Path Calculations (Custom + NetworkX A*)

# Run custom A* algorithm
try:
    print("\nCalculating shortest path with custom A* algorithm...")
    shortest_path_custom = astar_path(graph, from_node, to_node, ellipsoidal_distance)
    print(f"Custom A* path found. Total nodes: {len(shortest_path_custom)}")
    print(f"Custom A* path (first 10 nodes): {shortest_path_custom[:10]}...")
except (NodeNotFound, NetworkXNoPath) as e:
    print(f"Error with custom A* algorithm: {e}")
    exit()

# Run NetworkX A* algorithm (convert to DiGraph to fix bug)
try:
    print("\nCalculating shortest path with NetworkX A* algorithm...")
    # Convert MultiDiGraph to DiGraph to resolve NetworkX A* compatibility issue
    nx_graph = DiGraph(graph)
    shortest_path_nx = astar_path_nx(nx_graph, from_node, to_node, ellipsoidal_distance)
    print(f"NetworkX A* path found. Total nodes: {len(shortest_path_nx)}")
    print(f"NetworkX A* path (first 10 nodes): {shortest_path_nx[:10]}...")
except (NodeNotFound, NetworkXNoPath) as e:
    print(f"Error with NetworkX A* algorithm: {e}")
    exit()


# Convert Paths to GeoSeries (for Mapping)

# Convert custom path to LineString and GeoSeries
path_custom_ls = path_to_linestring(from_point, shortest_path_custom, to_point)
path_custom_gs = GeoSeries(path_custom_ls, crs=wgs84).to_crs(utm34)
print(f"\nCustom A* path LineString:")
print(path_custom_ls)

# Convert NetworkX path to LineString and GeoSeries
path_nx_ls = path_to_linestring(from_point, shortest_path_nx, to_point)
path_nx_gs = GeoSeries(path_nx_ls, crs=wgs84).to_crs(utm34)
print(f"\nNetworkX A* path LineString:")
print(path_nx_ls)


# Compare Path Lengths
custom_length = path_custom_gs.geometry.iloc[0].length
nx_length = path_nx_gs.geometry.iloc[0].length
print(f"\nPath Length Comparison (UTM34N, meters):")
print(f"My route: {custom_length:.0f}m. Network X route: {nx_length:.0f}m.")
print(f"Length difference: {abs(custom_length - nx_length):.0f}m.")


# Create & Save Map (with Both Paths)

# Create output directory if it doesn't exist
os.makedirs('./out', exist_ok=True)

# Create map figure
fig, my_ax = subplots(1, 1, figsize=(16, 10))
my_ax.axis('off')
my_ax.set(title="The 4 Bridges of Kaliningrad: Custom A* vs NetworkX A*")

# Set map bounds with 1000m buffer around the path
buffer = 1000
path_bounds = path_custom_gs.geometry.iloc[0].bounds
my_ax.set_xlim([path_bounds[0] - buffer, path_bounds[2] + buffer])
my_ax.set_ylim([path_bounds[1] - buffer, path_bounds[3] + buffer])

# Plot background layers (zorder controls drawing order: lower = behind)
water.plot(ax=my_ax, color='#a6cee3', linewidth=1, zorder=1)    # Water (light blue)
buildings.plot(ax=my_ax, color='grey', linewidth=1, zorder=2)    # Buildings (grey)

# Plot both paths (NetworkX path behind custom path)
path_nx_gs.plot(ax=my_ax, color='#4daf4a', linewidth=3, zorder=3)  # NetworkX path (green)
path_custom_gs.plot(ax=my_ax, color='#984ea3', linewidth=3, zorder=4)  # Custom path (purple)

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
    Line2D([0], [0], color='#984ea3', lw=3, label='Custom A* Path'),
    Line2D([0], [0], color='#4daf4a', lw=3, label='NetworkX A* Path')
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
map_save_path = './out/astar_comparison.png'
savefig(map_save_path, bbox_inches='tight', dpi=150)
print(f"\nMap saved to: {map_save_path}")

print("\nAll tasks completed successfully!")