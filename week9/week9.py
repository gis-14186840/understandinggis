# Import the library
from osmnx import graph_from_xml

from shapely import STRtree
from shapely.geometry import Point

from pyproj import Geod

from sys import exit
from networkx import NodeNotFound, NetworkXNoPath

from heapq import heappush, heappop


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


