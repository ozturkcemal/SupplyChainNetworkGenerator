import json
import os
import random
import sys
from collections import Counter
from math import radians, sin, cos, sqrt, atan2

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx  # Make sure this import is included
import numpy as np
import shapefile
from shapely.geometry import Point, shape

from bom import BOM  # Import BOM class from bom.py


class Main:
    def __init__(self):
        self.get_user_input()
        self.bom = BOM(self.n, self.num_roots, self.max_depth, self.max_parents, self.min_demand,
                       self.max_demand, self.seed)
        self.run()
        self.generate_random_locations()

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
        self.seed = int(seed_input) if seed_input else None

        min_demand_input = input(
            "Enter the minimum demand value for final items (leaf nodes) or press Enter to use the default (10): ")
        self.min_demand = int(min_demand_input) if min_demand_input else 10

        max_demand_input = input(
            "Enter the maximum demand value for final items (leaf nodes) or press Enter to use the default (100): ")
        self.max_demand = int(max_demand_input) if max_demand_input else 100

    def run(self):
        # Open a file to write the print statements
        with open('BOM_output.txt', 'w') as f:
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
            self.bom.visualize_graph('BOM_visualization.png')

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
            self.export_bom_matrix_to_json(bom_matrix, 'bom_matrix.json', labels)

            # Restore stdout
            sys.stdout = original_stdout

    def export_bom_matrix_to_json(self, bom_matrix, filename, labels):
        bom_matrix_list = bom_matrix.tolist()
        data = {
            "labels": labels,
            "matrix": bom_matrix_list
        }
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    #################### BELOW IS FOR RANDOM LOCATIONS #################################################

    def generate_random_locations(self):
        # Fixed random seed for reproducibility
        FIXED_SEED = 10

        # Path to your shapefile
        shapefile_path = 'shapefiles/TM_WORLD_BORDERS-0.3.shp'

        # Ensure the file exists
        if not os.path.exists(shapefile_path):
            raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")

        # Specify the encoding
        shp = shapefile.Reader(shapefile_path, encoding='latin1')  # or try 'cp1252' or 'iso-8859-1'

        # List of country codes to include (European countries + China, India, South Africa, US, Turkey, Iran)
        country_codes = [
            # European countries
            'ARM', 'BIH', 'CYP', 'DNK', 'IRL', 'AUT', 'EST', 'CZE', 'FIN',
            'FRA', 'DEU', 'GRC', 'HRV', 'HUN', 'ISL', 'ITA', 'LTU', 'LVA', 'BLR',
            'MLT', 'BEL', 'AND', 'GIB', 'LUX', 'MCO', 'NLD', 'NOR', 'POL', 'PRT',
            'ROU', 'MDA', 'ESP', 'CHE', 'GBR', 'SRB', 'SWE', 'ALB', 'MKD', 'MNE',
            'SVK', 'SVN',

            # Additional countries
            'CHN',  # China
            'IND',  # India
            'ZAF',  # South Africa
            'USA',  # United States
            'TUR',  # Turkey
            'IRN'  # Iran
        ]

        # Filter shapes and records for specified countries
        filtered_data = [(boundary, record) for boundary, record in
                         zip(shp.shapes(), shp.records()) if record[2] in country_codes]

        # Initialize counter
        count = Counter()

        # Define sampling function
        def sample(shapes, num_locations, min_x=-180, max_x=180, min_y=-90, max_y=90):
            locations = []
            while len(locations) < num_locations:
                location = (np.random.uniform(min_x, max_x), np.random.uniform(min_y, max_y))
                for boundary, record in sorted(shapes, key=lambda x: -count[x[1][2]]):
                    if Point(location).within(shape(boundary)):
                        count[record[2]] += 1
                        locations.append(location)
                        break
            return locations

        # Function to compute Haversine distance between two points
        def haversine(lon1, lat1, lon2, lat2):
            # Convert latitude and longitude from degrees to radians
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

            # Haversine formula
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            r = 6371  # Radius of earth in kilometers. Use 3956 for miles.
            return r * c

        # Get the number of facility locations from the user
        def get_number_of_locations():
            while True:
                try:
                    num_locations = int(input("Enter the number of facility locations to generate: "))
                    if num_locations > 0:
                        return num_locations
                    else:
                        print("Please enter a positive integer.")
                except ValueError:
                    print("Invalid input. Please enter a valid integer.")

        num_locations = get_number_of_locations()

        # Set the fixed random seed for reproducibility
        np.random.seed(FIXED_SEED)

        # Generate random facility locations
        random_locations = sample(filtered_data, num_locations)

        # Convert locations to a GeoDataFrame
        gdf_locations = gpd.GeoDataFrame(geometry=[Point(lon, lat) for lon, lat in random_locations],
                                         crs="EPSG:4326")

        # Load the shapefile into a GeoDataFrame
        gdf_shapefile = gpd.read_file(shapefile_path)

        # Calculate the bounds of the locations
        # Calculate the bounds of the locations
        bounds = gdf_locations.total_bounds
        minx, miny, maxx, maxy = bounds

        # Plotting
        fig, ax = plt.subplots(figsize=(12, 12))

        # Plot the shapefile boundaries
        gdf_shapefile.plot(ax=ax, color='lightgrey', edgecolor='black')

        # Plot the facility locations
        gdf_locations.plot(ax=ax, color='red', markersize=50, label='Facility Locations')

        # Draw edges between all pairs of facility locations and compute distances
        for i in range(len(random_locations)):
            for j in range(i + 1, len(random_locations)):
                lon1, lat1 = random_locations[i]
                lon2, lat2 = random_locations[j]
                distance = haversine(lon1, lat1, lon2, lat2)

                # Draw the line
                ax.plot([lon1, lon2], [lat1, lat2], color='blue', linestyle='-', linewidth=1, alpha=0.5)

                # Annotate the distance on the edge
                midpoint_lon = (lon1 + lon2) / 2
                midpoint_lat = (lat1 + lat2) / 2
                ax.text(midpoint_lon, midpoint_lat, f'{distance:.2f} km', fontsize=8, ha='center', color='black')

        # Set the limits to the bounds of the locations
        ax.set_xlim(minx - 1, maxx + 1)
        ax.set_ylim(miny - 1, maxy + 1)

        # Set title and labels
        ax.set_title(f'{num_locations} Facility Locations with Edges and Distances on World Map')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.legend()

        plt.show()


if __name__ == "__main__":
    Main()
