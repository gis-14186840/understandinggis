from random import shuffle
from matplotlib.pyplot import subplots, savefig, subplots_adjust

# create the class
class Schelling:

    def __init__(self, width, height, empty_ratio, similarity_threshold, n_iterations):
        """
        * This function is called a constructor. It is called automatically 
        * when an instance of the class is created, and is used to handle 
        * the setup of an instance of this class (i.e. 'construct' it)
        """
        # instance variables
        self.width = width
        self.height = height
        self.empty_ratio = empty_ratio
        self.similarity_threshold = similarity_threshold
        self.n_iterations = n_iterations

        # create an empty dictionary to store agents
        self.agents = {}

        # get all house addresses
        all_houses = [(x, y) for x in range(self.width) for y in range(self.height)]
        # print("All houses:", all_houses)   # temporary test print

        # randomise the house list
        shuffle(all_houses)
        # print("Shuffled houses:", all_houses)  # temporary test print

        # calculate number of empty houses
        n_empty = int(self.empty_ratio * len(all_houses))
        # print("Number of empty houses:", n_empty)

        # identify empty houses with list slicing
        self.empty_houses = all_houses[:n_empty]
        # print("Empty houses:", self.empty_houses)

        # the remaining houses
        remaining_houses = all_houses[n_empty:]
        # print("Remaining houses:", remaining_houses)
        # print("Check lengths:", len(self.empty_houses) + len(remaining_houses), "should equal", len(all_houses))

        # get agents for each group using list slicing and comprehension
        red_group = [[coords, 'red'] for coords in remaining_houses[0::2]]
        blue_group = [[coords, 'blue'] for coords in remaining_houses[1::2]]

        # print("Red group:", red_group)
        # print("Blue group:", blue_group)

        # add both sets of agents to the instance variable
        self.agents.update(dict(red_group + blue_group))

        # print("Agents dictionary:", self.agents) 
        
    def plot(self, my_ax, title):
        """
        * Plot the current state of the model
        """

        my_ax.set_title(title, fontsize=10, fontweight='bold')
        my_ax.set_xlim([0, self.width])
        my_ax.set_ylim([0, self.height])
        my_ax.set_xticks([])
        my_ax.set_yticks([])
        
        # plot agents one by one
        for agent_coords in self.agents:
            
            # we can use the agent's group name as the colour directly!
            my_ax.scatter(agent_coords[0]+0.5, agent_coords[1]+0.5, color=self.agents[agent_coords])

if __name__ == "__main__":

    # create an instance of the class
    schelling = Schelling(25, 25, 0.25, 0.6, 500)

    # print out each instance variable
    # print("Width:", schelling.width)
    # print("Height:", schelling.height)
    # print("Empty ratio:", schelling.empty_ratio)
    
    # initialise plot with two subplots (1 row, 2 columns)
    fig, my_axs = subplots(1, 2, figsize=(14, 6))

    # reduce the gap between the subplots
    subplots_adjust(wspace=0.1)

    # plot the initial state of the model into the first axis
    schelling.plot(my_axs[0], 'Initial State')

    # output image
    savefig(f"./out/11.png", bbox_inches='tight')
    print("done")
    print("Similarity threshold:", schelling.similarity_threshold)
    print("Iterations:", schelling.n_iterations)