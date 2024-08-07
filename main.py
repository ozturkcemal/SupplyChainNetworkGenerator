import random
import json
import os
from bom import BOM
from random_location_generator import RandomLocationGenerator

class Main:
    def __init__(self):
        # Open the report file in write mode
        self.report_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'instance_report.txt')
        self.log("Starting Main class initialization...")
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
        self.log(f"List of items in the BOM: {self.nodes}")

        # Store the list of facilities from RandomLocationGenerator
        self.facilities = self.location_generator.get_facilities()
        self.log(f"List of facility indices: {[fac.index for fac in self.facilities]}")

        # Create a mapping of nodes to facilities
        self.node_facilities_mapping = self.create_node_facilities_mapping()
        for node, facilities in self.node_facilities_mapping.items():
            self.log(f"Item {node} alternative facilities are: {[fac.index for fac in facilities]}")

        # Create the processing times dictionary
        self.processing_times = self.create_processing_times()
        for node, times in self.processing_times.items():
            self.log(f"Processing times for item {node}:")
            for facility, time in times.items():
                self.log(f"  Facility {facility.index}: {time}")

        # Export processing times to JSON
        self.export_processing_times_to_json('output/times.json')

        # Create the inventory dictionary
        self.inventory = self.create_inventory()
        for node, inventory in self.inventory.items():
            self.log(f"Inventory for item {node}:")
            for facility, inv in inventory.items():
                self.log(f"  Facility {facility.index}: {inv}")

        # Export inventory to JSON
        self.export_inventory_to_json('output/inventory.json')

        # Create the PGHG dictionary
        self.pghg = self.create_pghg()
        for node, pghg in self.pghg.items():
            self.log(f"PGHG for item {node}:")
            for facility, value in pghg.items():
                self.log(f"  Facility {facility.index}: {value}")

        # Export PGHG to JSON
        self.export_pghg_to_json('output/pghg.json')

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

    def create_processing_times(self):
        """Create a processing times dictionary for each node and its facilities."""
        processing_times = {}
        for node in self.nodes:
            processing_times[node] = {}
            for facility in self.facilities:
                if facility in self.node_facilities_mapping[node]:
                    processing_times[node][facility] = random.randint(5, 10)
                else:
                    processing_times[node][facility] = 0
        return processing_times

    def create_inventory(self):
        """Create an inventory dictionary for each node and its facilities."""
        inventory = {}
        for node in self.nodes:
            inventory[node] = {}
            for facility in self.facilities:
                if facility in self.node_facilities_mapping[node]:
                    inventory[node][facility] = random.randint(self.min_demand * 2, self.max_demand * 2)
                else:
                    inventory[node][facility] = 0
        return inventory

    def create_pghg(self):
        """Create a PGHG dictionary for each node and its facilities based on processing times."""
        pghg = {}
        for node, times in self.processing_times.items():
            pghg[node] = {}
            for facility, time in times.items():
                pghg[node][facility] = time * self.max_demand
        return pghg

    def export_processing_times_to_json(self, filename):
        """Export processing times to a JSON file with headers."""
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        data = []
        headers = ['item'] + [facility.index for facility in self.facilities]
        data.append(headers)
        for node, times in self.processing_times.items():
            row = [node] + [times[facility] for facility in self.facilities]
            data.append(row)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        self.log(f"Processing times exported to {filename}")

    def export_inventory_to_json(self, filename):
        """Export inventory to a JSON file with headers."""
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        data = []
        headers = ['item'] + [facility.index for facility in self.facilities]
        data.append(headers)
        for node, inventory in self.inventory.items():
            row = [node] + [inventory[facility] for facility in self.facilities]
            data.append(row)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        self.log(f"Inventory exported to {filename}")

    def export_pghg_to_json(self, filename):
        """Export PGHG to a JSON file with headers."""
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        data = []
        headers = ['item'] + [facility.index for facility in self.facilities]
        data.append(headers)
        for node, pghg in self.pghg.items():
            row = [node] + [pghg[facility] for facility in self.facilities]
            data.append(row)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

        self.log(f"PGHG exported to {filename}")

    def log(self, message):
        """Append a message to the report file."""
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(self.report_file), exist_ok=True)
        with open(self.report_file, 'a') as f:
            f.write(message + "\n")


if __name__ == "__main__":
    Main()