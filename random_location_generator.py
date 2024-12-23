import json
import os
from collections import Counter
from math import radians, sin, cos, sqrt, atan2

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import shapefile
from shapely.geometry import Point, shape

from facility import Facility  # Import the Facility class

class RandomLocationGenerator:
    def __init__(self, shapefile_path, fixed_seed, min_demand, max_demand):
        self.shapefile_path = shapefile_path
        self.fixed_seed = fixed_seed
        self.min_demand = min_demand
        self.max_demand = max_demand
        np.random.seed(self.fixed_seed)  # Set the random seed for reproducibility

        self.country_codes = [
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
        self.shp = None
        self.filtered_data = None
        self.count = Counter()
        self.facility_objects = []

        self.load_shapefile()
        self.filter_shapes_and_records()

    def load_shapefile(self):
        if not os.path.exists(self.shapefile_path):
            raise FileNotFoundError(f"Shapefile not found: {self.shapefile_path}")

        self.shp = shapefile.Reader(self.shapefile_path, encoding='latin1')

    def filter_shapes_and_records(self):
        self.filtered_data = [(boundary, record) for boundary, record in
                              zip(self.shp.shapes(), self.shp.records()) if record[2] in self.country_codes]

    def sample(self, num_locations, min_x=-180, max_x=180, min_y=-90, max_y=90):
        locations = []
        while len(locations) < num_locations:
            location = (np.random.uniform(min_x, max_x), np.random.uniform(min_y, max_y))
            for boundary, record in sorted(self.filtered_data, key=lambda x: -self.count[x[1][2]]):
                if Point(location).within(shape(boundary)):
                    self.count[record[2]] += 1
                    locations.append(location)
                    break
        return locations

    @staticmethod
    def haversine(lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        r = 6371  # Radius of earth in kilometers
        return r * c

    def generate_random_locations(self, num_locations):
        np.random.seed(self.fixed_seed)  # Ensure the same seed is used for reproducibility
        random_locations = self.sample(num_locations)

        # Clear any previous facility objects
        self.facility_objects = []

        for index, (lon, lat) in enumerate(random_locations):
            ttr = np.random.randint(2, 11)  # Random TTR between 2 and 10
            si = np.random.randint(1, 11)  # Random SI between 1 and 10
            capacity = np.random.randint(self.min_demand * 5, self.min_demand * 10 + 1)  # Capacity between min_demand * 2 and min_demand * 5
            facility_obj = Facility(index, lat, lon, ttr, si, capacity)
            self.facility_objects.append(facility_obj)

        # Sort facility objects based on their indices
        self.facility_objects.sort(key=lambda fac: fac.index)

        # Compute distances between all facilities
        for i, fac1 in enumerate(self.facility_objects):
            for j, fac2 in enumerate(self.facility_objects):
                if i < j:  # Ensure each pair is only processed once
                    distance = self.haversine(fac1.lon, fac1.lat, fac2.lon, fac2.lat)
                    fac1.distances[fac2.index] = distance
                    fac2.distances[fac1.index] = distance  # Assign the distance from j to i
                    # Compute TGHG
                    fac1.tghg[fac2.index] = distance * 1.05
                    fac2.tghg[fac1.index] = distance * 1.05  # Assign the TGHG from j to i
                elif i == j:
                    fac1.distances[fac1.index] = 0  # Distance to itself is zero
                    fac1.tghg[fac1.index] = 0  # TGHG to itself is zero

        # Create GeoDataFrame for plotting
        gdf_locations = gpd.GeoDataFrame(geometry=[Point(lon, lat) for lon, lat in random_locations],
                                         crs="EPSG:4326")
        gdf_shapefile = gpd.read_file(self.shapefile_path)
        bounds = gdf_locations.total_bounds
        minx, miny, maxx, maxy = bounds

        fig, ax = plt.subplots(figsize=(12, 12))
        gdf_shapefile.plot(ax=ax, color='lightgrey', edgecolor='black')
        gdf_locations.plot(ax=ax, color='red', markersize=50, label='Facility Locations')

        # Annotate each location with its index
        for i in range(len(random_locations)):
            lon1, lat1 = random_locations[i]
            ax.text(lon1, lat1, f'{i}', fontsize=10, ha='right', color='black')  # Show index at each location

        # Draw lines and distances between facilities
        for i in range(len(random_locations)):
            for j in range(i + 1, len(random_locations)):
                lon1, lat1 = random_locations[i]
                lon2, lat2 = random_locations[j]
                distance = self.haversine(lon1, lat1, lon2, lat2)
                ax.plot([lon1, lon2], [lat1, lat2], color='blue', linestyle='-', linewidth=1, alpha=0.5)
                midpoint_lon = (lon1 + lon2) / 2
                midpoint_lat = (lat1 + lat2) / 2
                ax.text(midpoint_lon, midpoint_lat, f'{distance:.2f} km', fontsize=8, ha='center', color='black')

        ax.set_xlim(minx - 1, maxx + 1)
        ax.set_ylim(miny - 1, maxy + 1)
        ax.set_title(f'{num_locations} Facility Locations with Edges and Distances on World Map')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.legend()

        # Display the plot for 2 seconds
        plt.show(block=False)
        plt.pause(2)

        # Ensure the 'output' directory exists
        output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        os.makedirs(output_directory, exist_ok=True)

        # Save the plot as a PNG file in the 'output' directory
        file_name = os.path.join(output_directory, 'facility_locations.png')
        plt.savefig(file_name)
        plt.close()

        # Write Facility objects to Facilities.txt
        facilities_file = os.path.join(output_directory, 'Facilities.txt')
        with open(facilities_file, 'w') as f:
            for fac in self.facility_objects:
                f.write(f"{fac}\n")
        # print(f"Facility details saved to {facilities_file}")
        self.export_facility_data_to_json('facility_data.json')
        self.export_tghg_to_json('tghg_data.json')

    def get_facilities(self):
        """Return the list of Facility objects."""
        return self.facility_objects

    def export_facility_data_to_json(self, filename):
        # Prepare data for the JSON file
        data = {
            "facilities": []  # This will contain the rows of the table
        }

        # Create the header for the table
        headers = ["facilities"] + [f"Facility {i}" for i in range(len(self.facility_objects))] + ["TTR", "SI", "Capacity", "lat",
                                                                                                   "lon"]

        # Initialize the table data with the headers
        table = [headers]

        # Add the distance data and additional information for each facility
        for i, facility in enumerate(self.facility_objects):
            row = [f"Facility {i}"]  # Start with the facility index
            # Add distance data
            row.extend([facility.distances.get(j, 0) for j in range(len(self.facility_objects))])
            # Add additional information (TTR, SI, capacity, lat, lon)
            row.extend([facility.ttr, facility.si, facility.capacity, facility.lat, facility.lon])
            table.append(row)

        # Add the table to the data dictionary
        data["facilities"] = table

        # Ensure the 'output' directory exists
        output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        os.makedirs(output_directory, exist_ok=True)

        # Save the data to a JSON file
        json_file_path = os.path.join(output_directory, filename)
        with open(json_file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        # print(f"Facility data saved to {json_file_path}")

    def export_tghg_to_json(self, filename):
        # Prepare data for the TGHG JSON file
        data = {
            "tghg": []  # This will contain the rows of the table
        }

        # Create the header for the table
        headers = ["facilities"] + [f"Facility {i}" for i in range(len(self.facility_objects))]

        # Initialize the table data with the headers
        table = [headers]

        # Add the TGHG data for each facility
        for i, facility in enumerate(self.facility_objects):
            row = [f"Facility {i}"]  # Start with the facility index
            # Add TGHG data
            row.extend([facility.tghg.get(j, 0) for j in range(len(self.facility_objects))])
            table.append(row)

        # Add the table to the data dictionary
        data["tghg"] = table

        # Ensure the 'output' directory exists
        output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        os.makedirs(output_directory, exist_ok=True)

        # Save the data to a JSON file
        json_file_path = os.path.join(output_directory, filename)
        with open(json_file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        # print(f"TGHG data saved to {json_file_path}")