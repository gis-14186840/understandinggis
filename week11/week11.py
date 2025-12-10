from random import shuffle, choice, seed
from matplotlib.pyplot import subplots, savefig, subplots_adjust
from copy import deepcopy
from random import seed

# Seed value 1824 is used
seed(1824)

# create the class
class Schelling:
    
    # class variable containing list of neighbours
    neighbours = [ (i, j) for i in range(-1, 2) for j in range(-1, 2) if (i, j) != (0, 0) ]
      
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

        # randomise the house list
        shuffle(all_houses)

        # calculate number of empty houses
        n_empty = int(self.empty_ratio * len(all_houses))

        # identify empty houses with list slicing
        self.empty_houses = all_houses[:n_empty]

        # the remaining houses
        remaining_houses = all_houses[n_empty:]
  
        # get agents for each group using list slicing and comprehension
        red_group = [[coords, 'red'] for coords in remaining_houses[0::2]]
        blue_group = [[coords, 'blue'] for coords in remaining_houses[1::2]]

        # add both sets of agents to the instance variable
        self.agents.update(dict(red_group + blue_group))

        # print("Agents dictionary:", self.agents) 
        
    def is_unsatisfied(self, agent):
        """
        * Determine whether an agent is unsatisfied based on its neighbours
        """
        # Initialise counters for same/different group neighbours
        count_similar = 0
        count_different = 0

        # Iterate through all 8 neighbours
        for n in self.neighbours:
            try:
                # Calculate neighbour coordinates
                neighbour_coords = (agent[0]+n[0], agent[1]+n[1])
                
                # Check if neighbour's group matches current agent's group
                if self.agents[neighbour_coords] == self.agents[agent]:
                    count_similar += 1
                else:
                    count_different += 1

            # if we go off the edge of the map or house is empty, there is nothing to do
            except KeyError:
                continue

        # Calculate similarity ratio and compare to threshold
        try:
            # Calculate proportion of same-group neighbours
            similarity_ratio = count_similar / (count_similar + count_different)
            
            # Return True if ratio is below threshold
            return similarity_ratio < self.similarity_threshold

        # catch the situation when there are only empty neighbours
        except ZeroDivisionError:
            # if this is the case they will be satisfied
            return False
        
    def run(self):

        # Loop from 1 to self.n_iterations + 1 
        for i in range(1, self.n_iterations + 1):
            # Initialise counter for number of agents that need to move in this iteration
            n_changes = 0
            
            # Deep copy: new object with all elements duplicated
            self.old_agents = deepcopy(self.agents)
            
            # Nested loop: iterate through static copy of agents from last iteration
            for agent in self.old_agents:
                # Check if agent is unsatisfied
                if self.is_unsatisfied(agent):
                    # Randomly choose an empty house for the agent to move to
                    empty_house = choice(self.empty_houses)
                    
                    # Add new location, remove old location
                    self.agents[empty_house] = self.agents[agent]
                    del self.agents[agent]
                    
                    # Update empty houses list to reflect the move
                    # Append old agent house to empty list, remove new house from empty list
                    self.empty_houses.append(agent)
                    self.empty_houses.remove(empty_house)
                    
                    # Increment counter for number of agents moved
                    n_changes += 1
            
            # Update user with iteration progress
            # print(f"Iteration: {i}, Number of changes: {n_changes}") 
            
            # Stop iterating if no agents moved
            if n_changes == 0:
                print(f"\nFound optimal solution at {i} iterations\n")
                break
        
        # Return number of iterations completed to calling code
        return i
                
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
    # print(schelling.is_unsatisfied(list(schelling.agents.keys())[0]))
    
    # initialise plot with two subplots (1 row, 2 columns)
    fig, my_axs = subplots(1, 2, figsize=(14, 6))

    # reduce the gap between the subplots
    subplots_adjust(wspace=0.1)

    # plot the initial state of the model into the first axis
    schelling.plot(my_axs[0], 'Initial State')
    
    # Run the model and store number of iterations completed
    iterations = schelling.run()
    
    # Add super title to the figure (overall model info)
    fig.suptitle(f"Schelling Model of Segregation ({schelling.similarity_threshold * 100:.2f}% Satisfaction after {iterations} iterations)")
    
    # Plot final state of the model (second axis)
    schelling.plot(my_axs[1], "Final State")
    
    # output image
    savefig(f"./out/schelling_segregation.png", bbox_inches='tight')
    print("done")
    print("Similarity threshold:", schelling.similarity_threshold)
    print("Iterations:", schelling.n_iterations)