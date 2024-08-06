# random_location_generator.py

import os
import shapefile
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point, shape
from collections import Counter
from math import radians, sin, cos, sqrt, atan2
from facility import Facility  # Import the Facility class

class RandomLocationGenerator:
    def __init__(self, shapefile_path, fixed_seed):
        self.shapefile_path = shapefile_path
        self.fixed_seed = fixed_seed
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
            si = np.random.randint(1, 11)   # Random SI between 1 and 10
            facility_obj = Facility(index, lat, lon, ttr, si)
            self.facility_objects.append(facility_obj)

        # Sort facility objects based on their indices
        self.facility_objects.sort(key=lambda fac: fac.index)

        # Compute distances between all facilities
        for i, fac1 in enumerate(self.facility_objects):
            for j, fac2 in enumerate(self.facility_objects):
                if i != j:
                    distance = self.haversine(fac1.lon, fac1.lat, fac2.lon, fac2.lat)
                    fac1.distances[fac2.index] = distance
                else:
                    fac1.distances[fac1.index] = 0  # Distance to itself is zero

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

        print(f"Plot saved to {file_name}")

        # Write Facility objects to Facilities.txt
        facilities_file = os.path.join(output_directory, 'Facilities.txt')
        with open(facilities_file, 'w') as f:
            for fac in self.facility_objects:
                f.write(f"{fac}\n")
        print(f"Facility details saved to {facilities_file}")