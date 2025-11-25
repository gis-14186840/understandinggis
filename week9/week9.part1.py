# Import the library
from networkx import Graph, is_eulerian, eulerian_circuit

# Create a graph object
graph = Graph()

# Add a node to the graph
graph.add_node(id)


# Add the 4 islands (nodes), colours as per the above diagram
graph.add_node('Blue')
graph.add_node('Green')
graph.add_node('Yellow')
graph.add_node('Purple')

# Add the 7 bridges (edges), colours as per the above diagram
graph.add_edge('Blue','Green', id=1)	# e.g. this is a bridge from the Blue to Green island
graph.add_edge('Blue', 'Green', id=2)
graph.add_edge('Blue', 'Yellow', id=3)
graph.add_edge('Blue', 'Yellow', id=4)
graph.add_edge('Blue', 'Purple', id=5)
graph.add_edge('Green', 'Purple', id=6)
graph.add_edge('Yellow', 'Purple', id=7)

# Print a report about the graph that you have just made
print(f"We have {len(list(graph.edges()))} bridges between {len(list(graph.nodes()))} islands.")

# Returns True or False to describe whether or not the graph is Eulerian
if is_eulerian(graph):
    print("The graph IS Eulerian.")

# Return the Eulerian route around Kaliningrad
    print("Eulerian Circuit:", list(eulerian_circuit(graph)))
else:
    print("The graph IS NOT Eulerian.")