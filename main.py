import json
import sys
import random
import networkx as nx
from bom import BOM
from random_location_generator import RandomLocationGenerator

class Main:
    def __init__(self):
        self.get_user_input()
        self.bom = BOM(self.n, self.num_roots, self.max_depth, self.max_parents, self.min_demand,
                       self.max_demand, self.seed)
        self.location_generator = RandomLocationGenerator('shapefiles/TM_WORLD_BORDERS-0.3.shp', fixed_seed=self.seed)
        self.run()

    def get_user_input(self):
        n_input = input(
            "Enter the number of items in the Bill of Material (between 5 to 10, or press Enter to randomly assign): ")
        self.n = int(n_input) if n_input else random.randint(8, 20)

        num_roots_input = input(
            f"Enter the number of root items (or press Enter to randomly assign between 2 and {self.n // 2}): ")
        self.num_roots = int(num_roots_input) if num_roots_input else random.randint(2, self.n // 2)

        max_depth_input = input(
            "Enter the maximum tier (depth of the BOM tree) or press Enter to use the default (3): ")
        self.max_depth = int(max_depth_input) if max_depth_input else 3

        max_parents_input = input(
            "Enter the maximum number of parent items a component/subassembly could have or press Enter to use the default (2): ")
        self.max_parents = int(max_parents_input) if max_parents_input else 2

        seed_input = input("Enter a seed value (or press Enter to use a random seed): ")
        self.seed = int(seed_input) if seed_input else random.randint(0, 10000)

        min_demand_input = input(
            "Enter the minimum demand value for final items (leaf nodes) or press Enter to use the default (10): ")
        self.min_demand = int(min_demand_input) if min_demand_input else 10

        max_demand_input = input(
            "Enter the maximum demand value for final items (leaf nodes) or press Enter to use the default (100): ")
        self.max_demand = int(max_demand_input) if max_demand_input else 100

        # Get number of facility locations
        while True:
            try:
                num_locations_input = input(f"Enter the number of facility locations to generate (between {self.n // 2} and {self.n}, or press Enter to randomly assign): ")
                if num_locations_input:
                    self.num_locations = int(num_locations_input)
                    if self.num_locations < (self.n // 2) or self.num_locations > self.n:
                        print(f"Please enter a number between {self.n // 2} and {self.n}.")
                    else:
                        break
                else:
                    self.num_locations = random.randint(self.n // 2, self.n)
                    break
            except ValueError:
                print("Invalid input. Please enter a valid integer.")

    def run(self):
        # Open a file to write the print statements
        with open('output/BOM_output.txt', 'w') as f:
            # Redirect stdout to the file
            original_stdout = sys.stdout
            sys.stdout = f

            dag_with_multiple_parents = self.bom.G

            # Print the edges with weights
            print("Edges with weights:")
            for (u, v, wt) in dag_with_multiple_parents.edges(data='weight'):
                print(f"Edge ({u}, {v}) has weight {wt}")

            # Print the nodes with their demands
            print("\nNodes with demands:")
            for node, demand in nx.get_node_attributes(dag_with_multiple_parents, 'demand').items():
                print(f"Node {node} has demand {demand}")

            # Print the depth of each node
            print("\nDepth of each node:")
            for node, depth in self.bom.depth.items():
                print(f"Node {node} is at depth {depth}")

            # Find and print the longest path
            longest_path_length, longest_path = self.bom.find_longest_path()
            print(
                f"\nLongest path length (height) or the number of levels in BOM (in terms of number of nodes): {longest_path_length}")
            print(f"Longest path: {' -> '.join(map(str, longest_path))}")

            # Visualize the tree and save the figure
            self.bom.visualize_graph('output/BOM_visualization.png')

            # Create and print the BOM matrix
            bom_matrix = self.bom.create_bom_matrix()
            print("\nBOM matrix:")
            print(bom_matrix)

            # Define labels
            labels = {
                "nodes": [f"Node {i}" for i in range(self.n)],
                "demand": "Demand"
            }

            # Export BOM matrix to JSON
            self.export_bom_matrix_to_json(bom_matrix, 'output/bom_matrix.json', labels)

            # Restore stdout
            sys.stdout = original_stdout

        # Generate and visualize random locations
        self.location_generator.generate_random_locations(self.num_locations)

    def export_bom_matrix_to_json(self, bom_matrix, filename, labels):
        bom_matrix_list = bom_matrix.tolist()
        data = {
            "labels": labels,
            "matrix": bom_matrix_list
        }
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)

if __name__ == "__main__":
    Main()