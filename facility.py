class Facility:
    def __init__(self, index, lat, lon, ttr, si, capacity):
        self.index = index
        self.lat = lat
        self.lon = lon
        self.ttr = ttr
        self.si = si
        self.capacity = capacity  # New attribute for capacity
        self.distances = {}  # Dictionary to store distances to other facilities

    def __str__(self):
        distances_str = ', '.join(f'{idx}: {dist:.2f} km' for idx, dist in self.distances.items())
        return (f'Facility Index: {self.index}, '
                f'Latitude: {self.lat:.2f}, Longitude: {self.lon:.2f}, '
                f'TTR: {self.ttr}, SI: {self.si}, '
                f'Capacity: {self.capacity}, '  # Include capacity in the string representation
                f'Distances: {distances_str}')