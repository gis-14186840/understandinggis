# Part 1: Create the Schelling class as required
class Schelling:
    def __init__(self, width, height, empty_ratio, similarity_threshold, n_iterations):
        """
        Constructor for the Schelling class
        :param self: Reference to the instance of the class
        :param width: Width of the grid (number of columns)
        :param height: Height of the grid (number of rows)
        :param empty_ratio: Proportion of empty houses (0-1 range)
        :param similarity_threshold: Minimum proportion of same-group neighbors for satisfaction
        :param n_iterations: Maximum number of iterations the model will run
        """
        # Store arguments as instance variables with the same names
        self.width = width
        self.height = height
        self.empty_ratio = empty_ratio
        self.similarity_threshold = similarity_threshold
        self.n_iterations = n_iterations

# Main code block to test the class
if __name__ == "__main__":
    # Create an instance of the Schelling class with specified parameters
    schelling = Schelling(25, 25, 0.25, 0.6, 500)
    
    # Print instance variables to verify successful initialization (to be deleted after testing)
    print("Grid width:", schelling.width)
    print("Grid height:", schelling.height)
    print("Empty ratio:", schelling.empty_ratio)
    print("Similarity threshold:", schelling.similarity_threshold)
    print("Maximum iterations:", schelling.n_iterations)