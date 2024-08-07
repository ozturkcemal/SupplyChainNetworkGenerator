import random

from bom import BOM
from random_location_generator import RandomLocationGenerator

class Main:
    def __init__(self):
        self.get_user_input()
        self.bom = BOM(self.n, self.num_roots, self.max_depth, self.max_parents, self.min_demand,
                       self.max_demand, self.seed)
        # Call the run method on the BOM instance
        self.bom.run()

        # Pass min_demand and max_demand to RandomLocationGenerator
        self.location_generator = RandomLocationGenerator(
            'shapefiles/TM_WORLD_BORDERS-0.3.shp',
            fixed_seed=self.seed,
            min_demand=self.min_demand,
            max_demand=self.max_demand
        )
        # Generate and visualize random locations before running the main logic
        self.location_generator.generate_random_locations(self.num_locations)

        # Store the list of nodes from BOM
        self.nodes = self.bom.get_nodes()
        print(f"List of nodes in the BOM: {self.nodes}")

        # Store the list of facilities from RandomLocationGenerator
        self.facilities = self.location_generator.get_facilities()
        print(f"List of facility indices: {[fac.index for fac in self.facilities]}")

        # Create a mapping of nodes to facilities
        self.node_facilities_mapping = self.create_node_facilities_mapping()
        for node, facilities in self.node_facilities_mapping.items():
            print(f"Node {node} is mapped to facilities: {[fac.index for fac in facilities]}")

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
                num_locations_input = input(
                    f"Enter the number of facility locations to generate (between {self.n // 2} and {self.n}, or press Enter to randomly assign): ")
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

    def create_node_facilities_mapping(self):
        """Create a mapping of nodes to a random list of facilities."""
        mapping = {}
        for node in self.nodes:
            num_facilities = random.randint(2, max(3, len(self.facilities) // 3))
            selected_facilities = random.sample(self.facilities, num_facilities)
            mapping[node] = selected_facilities
        return mapping


if __name__ == "__main__":
    Main()